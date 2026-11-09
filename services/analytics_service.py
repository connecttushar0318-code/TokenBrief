from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from models import QueryLogRecord, DocumentRecord
from schemas import (
    AnalyticsDashboardResponse,
    DailyQueryStat,
    ModelUsageStat,
    DocumentQueryStat,
    RecentQueryLogItem
)

class AnalyticsDashboardService:

    @classmethod
    async def record_query_log(
        cls,
        database_session: AsyncSession,
        question_text: str,
        latency_ms: float,
        cache_hit: bool,
        model_used: str,
        estimated_token_count: int,
        user_id: Optional[int] = None,
        document_id: Optional[int] = None
    ) -> QueryLogRecord:
        log_entry = QueryLogRecord(
            user_id=user_id,
            document_id=document_id,
            question_text=question_text[:1000],
            latency_ms=round(latency_ms, 2),
            cache_hit=cache_hit,
            model_used=model_used,
            estimated_token_count=estimated_token_count
        )
        database_session.add(log_entry)
        await database_session.commit()
        return log_entry

    @classmethod
    async def get_dashboard_metrics(
        cls,
        database_session: AsyncSession,
        user_id: Optional[int] = None
    ) -> AnalyticsDashboardResponse:
        base_filter = []
        if user_id:
            base_filter.append(QueryLogRecord.user_id == user_id)

        count_query = select(func.count(QueryLogRecord.id)).where(*base_filter)
        total_queries = (await database_session.execute(count_query)).scalar() or 0

        if total_queries == 0:
            return AnalyticsDashboardResponse(
                total_queries=0,
                average_latency_ms=0.0,
                cache_hit_ratio_percentage=0.0,
                total_tokens_estimated=0,
                daily_trends=[],
                model_breakdown=[],
                popular_documents=[],
                recent_queries=[]
            )

        avg_latency_query = select(func.avg(QueryLogRecord.latency_ms)).where(*base_filter)
        avg_latency = float((await database_session.execute(avg_latency_query)).scalar() or 0.0)

        cache_hits_query = select(func.count(QueryLogRecord.id)).where(QueryLogRecord.cache_hit == True, *base_filter)
        total_cache_hits = (await database_session.execute(cache_hits_query)).scalar() or 0
        cache_hit_ratio = round((total_cache_hits / total_queries) * 100.0, 2)

        tokens_query = select(func.sum(QueryLogRecord.estimated_token_count)).where(*base_filter)
        total_tokens = int((await database_session.execute(tokens_query)).scalar() or 0)

        daily_query = (
            select(
                func.to_char(QueryLogRecord.created_at, 'YYYY-MM-DD').label("query_date"),
                func.count(QueryLogRecord.id).label("daily_count"),
                func.avg(QueryLogRecord.latency_ms).label("daily_avg_latency")
            )
            .where(*base_filter)
            .group_by(text("query_date"))
            .order_by(text("query_date ASC"))
            .limit(30)
        )
        daily_rows = (await database_session.execute(daily_query)).all()
        daily_trends = [
            DailyQueryStat(
                date=row.query_date or "Today",
                query_count=int(row.daily_count),
                average_latency_ms=round(float(row.daily_avg_latency or 0.0), 2)
            )
            for row in daily_rows
        ]

        model_query = (
            select(
                QueryLogRecord.model_used,
                func.count(QueryLogRecord.id).label("model_count")
            )
            .where(*base_filter)
            .group_by(QueryLogRecord.model_used)
            .order_by(desc(text("model_count")))
        )
        model_rows = (await database_session.execute(model_query)).all()
        model_breakdown = [
            ModelUsageStat(
                model_name=row.model_used,
                usage_count=int(row.model_count),
                percentage=round((int(row.model_count) / total_queries) * 100.0, 2)
            )
            for row in model_rows
        ]

        doc_query = (
            select(
                QueryLogRecord.document_id,
                DocumentRecord.filename,
                func.count(QueryLogRecord.id).label("doc_query_count")
            )
            .outerjoin(DocumentRecord, QueryLogRecord.document_id == DocumentRecord.id)
            .where(*base_filter)
            .group_by(QueryLogRecord.document_id, DocumentRecord.filename)
            .order_by(desc(text("doc_query_count")))
            .limit(10)
        )
        doc_rows = (await database_session.execute(doc_query)).all()
        popular_documents = [
            DocumentQueryStat(
                document_id=row.document_id,
                filename=row.filename or ("All Documents Workspace" if row.document_id is None else f"Document #{row.document_id}"),
                query_count=int(row.doc_query_count)
            )
            for row in doc_rows
        ]

        recent_query = (
            select(QueryLogRecord)
            .where(*base_filter)
            .order_by(desc(QueryLogRecord.created_at))
            .limit(15)
        )
        recent_rows = (await database_session.execute(recent_query)).scalars().all()
        recent_queries = [
            RecentQueryLogItem(
                id=item.id,
                question_text=item.question_text[:120],
                document_id=item.document_id,
                latency_ms=item.latency_ms,
                cache_hit=item.cache_hit,
                model_used=item.model_used,
                created_at=item.created_at
            )
            for item in recent_rows
        ]

        return AnalyticsDashboardResponse(
            total_queries=total_queries,
            average_latency_ms=round(avg_latency, 2),
            cache_hit_ratio_percentage=cache_hit_ratio,
            total_tokens_estimated=total_tokens,
            daily_trends=daily_trends,
            model_breakdown=model_breakdown,
            popular_documents=popular_documents,
            recent_queries=recent_queries
        )
