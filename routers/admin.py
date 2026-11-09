from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_database_session
from models import (
    UserAccount,
    DocumentRecord,
    DocumentChunkRecord,
    SemanticQueryCacheRecord
)
from schemas import SystemAdminStatsResponse

router = APIRouter(prefix="/api/admin", tags=["Admin & Analytics"])

@router.get("/system-stats", response_model=SystemAdminStatsResponse)
async def get_system_admin_statistics(
    database_session: AsyncSession = Depends(get_database_session)
):
    users_total = await database_session.scalar(select(func.count(UserAccount.id)))
    verified_users_total = await database_session.scalar(
        select(func.count(UserAccount.id)).where(UserAccount.is_verified == True)
    )
    docs_total = await database_session.scalar(select(func.count(DocumentRecord.id)))
    pages_total = await database_session.scalar(select(func.sum(DocumentRecord.total_page_count)))
    chunks_total = await database_session.scalar(select(func.count(DocumentChunkRecord.id)))
    cache_entries = await database_session.scalar(select(func.count(SemanticQueryCacheRecord.id)))
    cache_hits = await database_session.scalar(select(func.sum(SemanticQueryCacheRecord.hit_count)))

    return SystemAdminStatsResponse(
        total_users=users_total or 0,
        verified_users=verified_users_total or 0,
        total_documents=docs_total or 0,
        total_pages=pages_total or 0,
        total_chunks=chunks_total or 0,
        total_cached_queries=cache_entries or 0,
        total_cache_hits=cache_hits or 0,
        system_status="optimal"
    )

@router.get("/users")
async def list_all_registered_users(
    database_session: AsyncSession = Depends(get_database_session)
):
    stmt = (
        select(
            UserAccount.id,
            UserAccount.username,
            UserAccount.email_address,
            UserAccount.is_verified,
            UserAccount.role,
            UserAccount.created_at,
            func.count(DocumentRecord.id).label("document_count")
        )
        .outerjoin(DocumentRecord, UserAccount.id == DocumentRecord.user_id)
        .group_by(UserAccount.id)
        .order_by(UserAccount.created_at.desc())
    )
    result = await database_session.execute(stmt)
    rows = result.all()

    return [
        {
            "id": r.id,
            "username": r.username,
            "email_address": r.email_address,
            "is_verified": r.is_verified,
            "role": r.role,
            "created_at": r.created_at,
            "documents_uploaded": r.document_count
        }
        for r in rows
    ]
