import io
from typing import List, Dict, Any, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import (
    ConversationThreadRecord,
    ConversationMessageRecord,
    DocumentRecord,
    UserAccount
)

class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(total_pages)
            super().showPage()
        super().save()

    def draw_footer(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        footer_text = f"TokenBrief Intelligence Engine  |  Page {self._pageNumber} of {total_pages}  |  Confidential & Proprietary"
        self.drawCentredString(letter[0] / 2.0, 30, footer_text)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 42, letter[0] - 40, 42)
        self.restoreState()

class SessionPdfExportService:

    @classmethod
    def create_formatted_pdf_bytes(
        cls,
        session_title: str,
        user_name: Optional[str],
        referenced_documents: List[str],
        messages: List[Dict[str, Any]]
    ) -> bytes:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=50
        )

        sample_styles = getSampleStyleSheet()

        brand_header_style = ParagraphStyle(
            "BrandHeaderStyle",
            parent=sample_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#4338CA")
        )

        title_style = ParagraphStyle(
            "ReportTitleStyle",
            parent=sample_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F172A")
        )

        metadata_label_style = ParagraphStyle(
            "MetadataLabelStyle",
            parent=sample_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569")
        )

        metadata_value_style = ParagraphStyle(
            "MetadataValueStyle",
            parent=sample_styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1E293B")
        )

        question_header_style = ParagraphStyle(
            "QuestionHeaderStyle",
            parent=sample_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#1E3A8A")
        )

        question_text_style = ParagraphStyle(
            "QuestionTextStyle",
            parent=sample_styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1E293B")
        )

        answer_header_style = ParagraphStyle(
            "AnswerHeaderStyle",
            parent=sample_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#065F46")
        )

        answer_text_style = ParagraphStyle(
            "AnswerTextStyle",
            parent=sample_styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#0F172A")
        )

        story_elements = []

        story_elements.append(Paragraph("TokenBrief AI Workspace", brand_header_style))
        story_elements.append(Paragraph(session_title, title_style))
        story_elements.append(Spacer(1, 10))

        docs_display = ", ".join(referenced_documents) if referenced_documents else "All Workspace Documents"
        current_time_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        metadata_table_data = [
            [
                Paragraph("<b>Generated:</b>", metadata_label_style),
                Paragraph(current_time_str, metadata_value_style),
                Paragraph("<b>Account:</b>", metadata_label_style),
                Paragraph(user_name or "Guest Operator", metadata_value_style)
            ],
            [
                Paragraph("<b>Documents:</b>", metadata_label_style),
                Paragraph(docs_display, metadata_value_style),
                Paragraph("<b>Total Exchanges:</b>", metadata_label_style),
                Paragraph(str(len(messages)), metadata_value_style)
            ]
        ]

        metadata_table = Table(metadata_table_data, colWidths=[80, 200, 90, 160])
        metadata_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EDF2F7")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story_elements.append(metadata_table)
        story_elements.append(Spacer(1, 15))

        story_elements.append(HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#6366F1"),
            spaceBefore=5,
            spaceAfter=15
        ))

        for index, msg in enumerate(messages, start=1):
            role = msg.get("sender_role", "user").lower()
            text_content = msg.get("message_text", "")

            cleaned_content = text_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")

            if role in ["user", "human"]:
                block_data = [
                    [Paragraph(f"<b>Query #{index}</b>", question_header_style)],
                    [Paragraph(cleaned_content, question_text_style)]
                ]
                block_table = Table(block_data, colWidths=[530])
                block_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF2FF")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C7D2FE")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]))
                story_elements.append(KeepTogether([block_table, Spacer(1, 8)]))
            else:
                block_data = [
                    [Paragraph("<b>DocuVibe Grounded Intelligence:</b>", answer_header_style)],
                    [Paragraph(cleaned_content, answer_text_style)]
                ]
                block_table = Table(block_data, colWidths=[530])
                block_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#BBF7D0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]))
                story_elements.append(KeepTogether([block_table, Spacer(1, 14)]))

        doc.build(story_elements, canvasmaker=NumberedCanvas)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    @classmethod
    async def export_thread_to_pdf(
        cls,
        thread_id: int,
        database_session: AsyncSession,
        user_account: Optional[UserAccount] = None
    ) -> bytes:
        thread_query = select(ConversationThreadRecord).where(ConversationThreadRecord.id == thread_id)
        thread_result = await database_session.execute(thread_query)
        thread_record = thread_result.scalar_one_or_none()

        if not thread_record:
            raise ValueError(f"Conversation thread with ID {thread_id} was not found.")

        messages_query = (
            select(ConversationMessageRecord)
            .where(ConversationMessageRecord.thread_id == thread_id)
            .order_by(ConversationMessageRecord.created_at.asc())
        )
        messages_result = await database_session.execute(messages_query)
        messages_records = messages_result.scalars().all()

        referenced_docs = []
        if thread_record.document_id:
            doc_query = select(DocumentRecord).where(DocumentRecord.id == thread_record.document_id)
            doc_result = await database_session.execute(doc_query)
            doc_record = doc_result.scalar_one_or_none()
            if doc_record:
                referenced_docs.append(doc_record.filename)

        formatted_messages = [
            {"sender_role": msg.sender_role, "message_text": msg.message_text}
            for msg in messages_records
        ]

        user_name = user_account.username if user_account else "TokenBrief Analyst"

        return cls.create_formatted_pdf_bytes(
            session_title=thread_record.title,
            user_name=user_name,
            referenced_documents=referenced_docs,
            messages=formatted_messages
        )
