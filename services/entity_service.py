import re
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models import DocumentRecord, DocumentChunkRecord, DocumentEntityRecord
from schemas import (
    DocumentEntitiesResponse,
    DocumentEntityItem,
    KnowledgeGraphResponse,
    GraphNode,
    GraphLink
)
from config import settings

class EntityKnowledgeGraphService:

    COMMON_TECHNICAL_SKILLS = [
        "python", "java", "c++", "c#", "javascript", "typescript", "html", "css", "sql",
        "react", "next.js", "angular", "vue", "fastapi", "flask", "django", "node.js",
        "docker", "kubernetes", "git", "github", "aws", "gcp", "azure", "linux", "postgresql",
        "mysql", "sqlite", "mongodb", "redis", "neon", "pgvector", "pytorch", "tensorflow",
        "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn", "keras", "opencv",
        "langchain", "huggingface", "rest api", "graphql", "tailwind css", "bootstrap"
    ]

    COMMON_DOMAINS_AND_CONCEPTS = [
        "data mining", "machine learning", "deep learning", "artificial intelligence",
        "data warehouse", "kdd process", "classification", "clustering", "association rules",
        "decision tree", "neural network", "regression", "support vector machine", "naive bayes",
        "k-means", "hierarchical clustering", "dbscan", "apriori algorithm", "fp-growth",
        "retrieval augmented generation", "vector embedding", "semantic search", "reranking",
        "feature engineering", "data cleaning", "normalization", "cross-validation",
        "overfitting", "precision", "recall", "f1-score", "roc-auc", "confusion matrix"
    ]

    COMMON_ORGANIZATIONS = [
        "google", "microsoft", "meta", "amazon", "apple", "ibm", "oracle", "openai",
        "university", "college", "institute", "school", "adgitm", "iit", "nit", "delhi"
    ]

    @classmethod
    async def extract_and_store_entities(
        cls,
        document_id: int,
        database_session: AsyncSession
    ) -> DocumentEntitiesResponse:
        doc_query = select(DocumentRecord).where(DocumentRecord.id == document_id)
        doc_result = await database_session.execute(doc_query)
        document_record = doc_result.scalar_one_or_none()

        if not document_record:
            raise ValueError(f"Document with ID {document_id} was not found.")

        chunks_query = (
            select(DocumentChunkRecord)
            .where(DocumentChunkRecord.document_id == document_id)
            .order_by(DocumentChunkRecord.chunk_index_number)
        )
        chunks_result = await database_session.execute(chunks_query)
        chunks = list(chunks_result.scalars().all())

        if not chunks:
            raise ValueError(f"Document with ID {document_id} contains no text chunks.")

        raw_entities = None
        if settings.gemini_api_key and settings.gemini_api_key.startswith("AIzaSy"):
            raw_entities = await cls._try_gemini_entity_extraction(document_record, chunks)

        if not raw_entities:
            raw_entities = cls._extract_fallback_entities(document_record, chunks)

        await database_session.execute(
            delete(DocumentEntityRecord).where(DocumentEntityRecord.document_id == document_id)
        )

        persisted_entities = []
        for entity_dict in raw_entities:
            new_entity = DocumentEntityRecord(
                document_id=document_id,
                entity_text=entity_dict["entity_text"][:250],
                entity_type=entity_dict["entity_type"].upper(),
                source_page_number=entity_dict.get("source_page_number", 1),
                occurrence_count=entity_dict.get("occurrence_count", 1),
                confidence_score=entity_dict.get("confidence_score", 1.0)
            )
            database_session.add(new_entity)
            persisted_entities.append(new_entity)

        await database_session.commit()
        for item in persisted_entities:
            await database_session.refresh(item)

        entities_by_type = defaultdict(list)
        for item in persisted_entities:
            entities_by_type[item.entity_type].append(item.entity_text)

        entity_items = [
            DocumentEntityItem.model_validate(item)
            for item in persisted_entities
        ]

        return DocumentEntitiesResponse(
            document_id=document_id,
            total_entities=len(persisted_entities),
            entities_by_type=dict(entities_by_type),
            entities=entity_items
        )

    @classmethod
    async def _try_gemini_entity_extraction(
        cls,
        document_record: DocumentRecord,
        chunks: List[DocumentChunkRecord]
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            from google import genai
            from google.genai import types

            sampled_context = "\n".join(
                [f"[Page {c.source_page_number or 1}] {c.chunk_text_content[:400]}" for c in chunks[:12]]
            )

            prompt = (
                f"Extract key named entities from this document titled '{document_record.filename}'.\n"
                f"Context:\n{sampled_context[:10000]}\n\n"
                f"Extract entities across types: 'SKILL', 'CONCEPT', 'ORGANIZATION', 'PERSON', 'TOOL'.\n"
                f"Output strictly valid JSON as an array of objects with keys: "
                f"'entity_text', 'entity_type', 'source_page_number' (integer), 'occurrence_count' (integer), 'confidence_score' (float 0.0 to 1.0).\n"
                f"Do not include markdown fences."
            )

            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.gemini_model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed = json.loads(raw_text.strip())
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed[:30]
        except Exception:
            return None
        return None

    @classmethod
    def _extract_fallback_entities(
        cls,
        document_record: DocumentRecord,
        chunks: List[DocumentChunkRecord]
    ) -> List[Dict[str, Any]]:
        extracted = {}

        is_resume = "resume" in document_record.filename.lower() or "cv" in document_record.filename.lower()
        aggregated_text = "\n".join([c.chunk_text_content for c in chunks])

        if is_resume:
            name_match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", aggregated_text.strip())
            if name_match:
                candidate_name = name_match.group(1).strip()
                extracted[candidate_name.lower()] = {
                    "entity_text": candidate_name,
                    "entity_type": "PERSON",
                    "source_page_number": chunks[0].source_page_number or 1,
                    "occurrence_count": 3,
                    "confidence_score": 0.98
                }

        for chunk in chunks:
            chunk_text = chunk.chunk_text_content.lower()
            page_num = chunk.source_page_number or 1

            for skill in cls.COMMON_TECHNICAL_SKILLS:
                pattern = r"\b" + re.escape(skill) + r"\b"
                matches = list(re.finditer(pattern, chunk_text))
                if matches:
                    key = skill.lower()
                    if key in extracted:
                        extracted[key]["occurrence_count"] += len(matches)
                    else:
                        extracted[key] = {
                            "entity_text": skill.title() if len(skill) > 3 else skill.upper(),
                            "entity_type": "SKILL",
                            "source_page_number": page_num,
                            "occurrence_count": len(matches),
                            "confidence_score": 0.95
                        }

            for concept in cls.COMMON_DOMAINS_AND_CONCEPTS:
                pattern = r"\b" + re.escape(concept) + r"\b"
                matches = list(re.finditer(pattern, chunk_text))
                if matches:
                    key = concept.lower()
                    if key in extracted:
                        extracted[key]["occurrence_count"] += len(matches)
                    else:
                        extracted[key] = {
                            "entity_text": concept.title(),
                            "entity_type": "CONCEPT",
                            "source_page_number": page_num,
                            "occurrence_count": len(matches),
                            "confidence_score": 0.92
                        }

            for org in cls.COMMON_ORGANIZATIONS:
                pattern = r"\b" + re.escape(org) + r"\b"
                matches = list(re.finditer(pattern, chunk_text))
                if matches:
                    key = org.lower()
                    if key in extracted:
                        extracted[key]["occurrence_count"] += len(matches)
                    else:
                        extracted[key] = {
                            "entity_text": org.upper() if len(org) <= 6 else org.title(),
                            "entity_type": "ORGANIZATION",
                            "source_page_number": page_num,
                            "occurrence_count": len(matches),
                            "confidence_score": 0.88
                        }

        sorted_entities = sorted(extracted.values(), key=lambda x: x["occurrence_count"], reverse=True)
        return sorted_entities[:35]

    @classmethod
    async def get_document_entities(
        cls,
        document_id: int,
        database_session: AsyncSession
    ) -> DocumentEntitiesResponse:
        query = (
            select(DocumentEntityRecord)
            .where(DocumentEntityRecord.document_id == document_id)
            .order_by(DocumentEntityRecord.occurrence_count.desc())
        )
        result = await database_session.execute(query)
        entities = list(result.scalars().all())

        if not entities:
            return await cls.extract_and_store_entities(document_id, database_session)

        entities_by_type = defaultdict(list)
        for item in entities:
            entities_by_type[item.entity_type].append(item.entity_text)

        entity_items = [
            DocumentEntityItem.model_validate(item)
            for item in entities
        ]

        return DocumentEntitiesResponse(
            document_id=document_id,
            total_entities=len(entities),
            entities_by_type=dict(entities_by_type),
            entities=entity_items
        )

    @classmethod
    async def get_document_graph(
        cls,
        document_id: int,
        database_session: AsyncSession
    ) -> KnowledgeGraphResponse:
        doc_query = select(DocumentRecord).where(DocumentRecord.id == document_id)
        doc_result = await database_session.execute(doc_query)
        document_record = doc_result.scalar_one_or_none()

        if not document_record:
            raise ValueError(f"Document with ID {document_id} was not found.")

        entities_response = await cls.get_document_entities(document_id, database_session)

        nodes: List[GraphNode] = []
        links: List[GraphLink] = []

        doc_node_id = f"doc_{document_record.id}"
        nodes.append(GraphNode(
            id=doc_node_id,
            label=document_record.filename,
            group="DOCUMENT",
            size=28
        ))

        for entity in entities_response.entities:
            entity_node_id = f"ent_{entity.id}"
            nodes.append(GraphNode(
                id=entity_node_id,
                label=entity.entity_text,
                group=entity.entity_type,
                size=12 + min(entity.occurrence_count * 2, 16)
            ))
            links.append(GraphLink(
                source=doc_node_id,
                target=entity_node_id,
                relationship="MENTIONS",
                weight=float(min(entity.occurrence_count, 5))
            ))

        chunks_query = select(DocumentChunkRecord).where(DocumentChunkRecord.document_id == document_id)
        chunks_result = await database_session.execute(chunks_query)
        chunks = list(chunks_result.scalars().all())

        co_occurrences: Dict[Tuple[int, int], int] = defaultdict(int)
        for chunk in chunks:
            chunk_lower = chunk.chunk_text_content.lower()
            present_entities = [
                e for e in entities_response.entities
                if e.entity_text.lower() in chunk_lower
            ]
            for i in range(len(present_entities)):
                for j in range(i + 1, min(i + 5, len(present_entities))):
                    pair = tuple(sorted([present_entities[i].id, present_entities[j].id]))
                    co_occurrences[pair] += 1

        for (ent_id_1, ent_id_2), count in co_occurrences.items():
            if count >= 2:
                links.append(GraphLink(
                    source=f"ent_{ent_id_1}",
                    target=f"ent_{ent_id_2}",
                    relationship="CO_OCCURS",
                    weight=float(count)
                ))

        summary_data = {
            "document_id": document_id,
            "document_name": document_record.filename,
            "total_nodes": len(nodes),
            "total_links": len(links),
            "entity_categories": list(entities_response.entities_by_type.keys())
        }

        return KnowledgeGraphResponse(
            nodes=nodes,
            links=links,
            summary=summary_data
        )

    @classmethod
    async def get_workspace_graph(
        cls,
        database_session: AsyncSession,
        user_id: Optional[int] = None
    ) -> KnowledgeGraphResponse:
        docs_query = select(DocumentRecord)
        if user_id:
            docs_query = docs_query.where(DocumentRecord.user_id == user_id)
        docs_result = await database_session.execute(docs_query)
        documents = list(docs_result.scalars().all())

        nodes: List[GraphNode] = []
        links: List[GraphLink] = []
        entity_text_to_node_id: Dict[str, str] = {}
        entity_node_counters: Dict[str, int] = defaultdict(int)

        for doc in documents:
            doc_node_id = f"doc_{doc.id}"
            nodes.append(GraphNode(
                id=doc_node_id,
                label=doc.filename,
                group="DOCUMENT",
                size=26
            ))

            entities_resp = await cls.get_document_entities(doc.id, database_session)
            for entity in entities_resp.entities:
                canonical_key = entity.entity_text.strip().lower()
                if canonical_key not in entity_text_to_node_id:
                    node_id = f"ent_global_{canonical_key.replace(' ', '_')}"
                    entity_text_to_node_id[canonical_key] = node_id
                    nodes.append(GraphNode(
                        id=node_id,
                        label=entity.entity_text,
                        group=entity.entity_type,
                        size=14
                    ))
                node_id = entity_text_to_node_id[canonical_key]
                entity_node_counters[node_id] += 1
                links.append(GraphLink(
                    source=doc_node_id,
                    target=node_id,
                    relationship="CONTAINS",
                    weight=1.0
                ))

        for node in nodes:
            if node.id in entity_node_counters and entity_node_counters[node.id] > 1:
                node.size = 20

        summary_data = {
            "total_documents": len(documents),
            "total_nodes": len(nodes),
            "total_links": len(links),
            "bridge_entities_count": sum(1 for c in entity_node_counters.values() if c > 1)
        }

        return KnowledgeGraphResponse(
            nodes=nodes,
            links=links,
            summary=summary_data
        )
