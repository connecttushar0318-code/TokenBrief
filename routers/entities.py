from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from database import get_database_session
from models import UserAccount
from security import get_optional_authenticated_user
from schemas import (
    DocumentEntitiesResponse,
    KnowledgeGraphResponse
)
from services.entity_service import EntityKnowledgeGraphService

router = APIRouter(prefix="/api/entities", tags=["Knowledge Graph & Entities"])

@router.post("/extract/{document_id}", response_model=DocumentEntitiesResponse)
async def extract_document_entities(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    try:
        entities_result = await EntityKnowledgeGraphService.extract_and_store_entities(
            document_id=document_id,
            database_session=database_session
        )
        return entities_result
    except ValueError as val_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_error)
        )
    except Exception as general_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Entity extraction failed: {str(general_error)}"
        )

@router.get("/graph/{document_id}", response_model=KnowledgeGraphResponse)
async def get_document_knowledge_graph(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    try:
        graph_data = await EntityKnowledgeGraphService.get_document_graph(
            document_id=document_id,
            database_session=database_session
        )
        return graph_data
    except ValueError as val_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_error)
        )
    except Exception as general_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge graph generation failed: {str(general_error)}"
        )

@router.get("/workspace-graph", response_model=KnowledgeGraphResponse)
async def get_workspace_knowledge_graph(
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    user_id = optional_user_account.id if optional_user_account else None
    graph_data = await EntityKnowledgeGraphService.get_workspace_graph(
        database_session=database_session,
        user_id=user_id
    )
    return graph_data

@router.get("/{document_id}", response_model=DocumentEntitiesResponse)
async def get_document_entities_list(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    try:
        entities_result = await EntityKnowledgeGraphService.get_document_entities(
            document_id=document_id,
            database_session=database_session
        )
        return entities_result
    except ValueError as val_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_error)
        )
    except Exception as general_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch entities: {str(general_error)}"
        )
