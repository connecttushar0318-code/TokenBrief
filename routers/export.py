from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from database import get_database_session
from models import UserAccount, DocumentRecord
from security import get_optional_authenticated_user
from schemas import ExportSessionPdfRequest
from services.export_service import SessionPdfExportService

router = APIRouter(prefix="/api/export", tags=["Export Engine"])

@router.post("/pdf")
async def export_custom_session_to_pdf(
    export_payload: ExportSessionPdfRequest,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    try:
        user_name = optional_user_account.username if optional_user_account else "Guest Analyst"

        if export_payload.thread_id:
            pdf_bytes = await SessionPdfExportService.export_thread_to_pdf(
                thread_id=export_payload.thread_id,
                database_session=database_session,
                user_account=optional_user_account
            )
        else:
            referenced_filenames = []
            if export_payload.document_ids:
                docs_query = select(DocumentRecord).where(DocumentRecord.id.in_(export_payload.document_ids))
                docs_result = await database_session.execute(docs_query)
                referenced_filenames = [d.filename for d in docs_result.scalars().all()]

            raw_messages = []
            if export_payload.messages:
                raw_messages = [
                    {"sender_role": m.sender_role, "message_text": m.message_text}
                    for m in export_payload.messages
                ]

            pdf_bytes = SessionPdfExportService.create_formatted_pdf_bytes(
                session_title=export_payload.session_title or "TokenBrief Intelligence Report",
                user_name=user_name,
                referenced_documents=referenced_filenames,
                messages=raw_messages
            )

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_filename = f"TokenBrief_Report_{timestamp_str}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"'
            }
        )
    except ValueError as val_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_error)
        )
    except Exception as export_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(export_error)}"
        )

@router.get("/thread/{thread_id}/pdf")
async def export_conversation_thread_pdf(
    thread_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    try:
        pdf_bytes = await SessionPdfExportService.export_thread_to_pdf(
            thread_id=thread_id,
            database_session=database_session,
            user_account=optional_user_account
        )

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_filename = f"TokenBrief_Thread_{thread_id}_{timestamp_str}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"'
            }
        )
    except ValueError as val_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_error)
        )
    except Exception as export_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(export_error)}"
        )
