from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from services.validation_service import AccountValidationService

class UserRegistrationRequest(BaseModel):
    email_address: str
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username_field(cls, candidate_username: str) -> str:
        return AccountValidationService.validate_username(candidate_username)

    @field_validator("email_address")
    @classmethod
    def validate_email_field(cls, candidate_email: str) -> str:
        return AccountValidationService.validate_email(candidate_email)

    @field_validator("password")
    @classmethod
    def validate_password_field(cls, candidate_password: str) -> str:
        return AccountValidationService.validate_password(candidate_password)

class UserLoginRequest(BaseModel):
    username: str
    password: str

class EmailVerificationRequest(BaseModel):
    email_address: str
    otp_code: str = Field(min_length=6, max_length=6)

class ResendOtpRequest(BaseModel):
    email_address: str

class ForgotPasswordRequest(BaseModel):
    email_address: str

class ResetPasswordRequest(BaseModel):
    email_address: str
    otp_code: str = Field(min_length=6, max_length=6)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, candidate_password: str) -> str:
        return AccountValidationService.validate_password(candidate_password)

class GenericMessageResponse(BaseModel):
    message: str
    status: str = "success"

class UserAccountResponse(BaseModel):
    id: int
    email_address: str
    username: str
    is_verified: bool
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuthenticationTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class DocumentMetadataResponse(BaseModel):
    id: int
    filename: str
    file_size_bytes: int
    total_page_count: int
    total_chunk_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentSummaryResponse(BaseModel):
    document_id: int
    filename: str
    executive_summary: str
    key_takeaways: List[str]
    topics: List[str]

class QuestionQueryRequest(BaseModel):
    question_text: str = Field(min_length=2)
    filter_document_id: Optional[int] = None
    maximum_results: int = Field(default=4, ge=1, le=10)

class SourceReferenceChunk(BaseModel):
    chunk_id: int
    document_id: int
    document_filename: str
    source_page_number: Optional[int]
    chunk_text_content: str
    similarity_percentage: float
    rerank_score: Optional[float] = None

class AnswerWithSourcesResponse(BaseModel):
    question_text: str
    generated_answer: str
    source_chunks: List[SourceReferenceChunk]
    cache_hit: bool = False
    cached_query: Optional[str] = None

class QuickChatRequest(BaseModel):
    message_text: str = Field(min_length=1)
    session_id: Optional[str] = None
    document_id: Optional[int] = None

class QuickChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[SourceReferenceChunk]
    cache_hit: bool = False

class CreateConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    document_id: Optional[int] = None

class ConversationMessageRequest(BaseModel):
    message_text: str = Field(min_length=1)

class ConversationMessageResponse(BaseModel):
    id: int
    sender_role: str
    message_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationThreadResponse(BaseModel):
    id: int
    title: str
    document_id: Optional[int]
    created_at: datetime
    messages: List[ConversationMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)

class SystemAdminStatsResponse(BaseModel):
    total_users: int
    verified_users: int
    total_documents: int
    total_pages: int
    total_chunks: int
    total_cached_queries: int
    total_cache_hits: int
    system_status: str

class SystemHealthStatusResponse(BaseModel):
    service_status: str
    database_status: str

class GenerateQuizRequest(BaseModel):
    document_id: int
    number_of_questions: int = Field(default=5, ge=1, le=20)
    difficulty: Optional[str] = "medium"

class QuizQuestionItemResponse(BaseModel):
    id: int
    document_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    source_page_number: Optional[int] = None
    difficulty: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SubmitQuizAnswerItem(BaseModel):
    question_id: int
    selected_option: str

class SubmitQuizAttemptRequest(BaseModel):
    document_id: int
    answers: List[SubmitQuizAnswerItem]

class QuizAnswerResultItem(BaseModel):
    question_id: int
    question_text: str
    selected_option: str
    correct_option: str
    is_correct: bool
    explanation: Optional[str] = None
    source_page_number: Optional[int] = None

class QuizAttemptResultResponse(BaseModel):
    attempt_id: int
    document_id: int
    total_questions: int
    correct_count: int
    score_percentage: float
    answers: List[QuizAnswerResultItem]
    completed_at: datetime

class QuizAttemptHistoryItem(BaseModel):
    id: int
    document_id: int
    total_questions: int
    correct_count: int
    score_percentage: float
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class QuizHistoryResponse(BaseModel):
    document_id: int
    attempts: List[QuizAttemptHistoryItem]
    best_score_percentage: float
    average_score_percentage: float

class DocumentComparisonRequest(BaseModel):
    document_ids: List[int] = Field(min_length=2, max_length=5)

class ComparisonCategoryRow(BaseModel):
    criterion: str
    document_values: Dict[str, str]
    key_difference: str

class DocumentSummaryHeader(BaseModel):
    document_id: int
    filename: str
    detected_type: str
    total_pages: int
    total_chunks: int

class DocumentComparisonResponse(BaseModel):
    documents: List[DocumentSummaryHeader]
    comparison_matrix: List[ComparisonCategoryRow]
    shared_topics: List[str]
    unique_topics_per_document: Dict[str, List[str]]
    synthesis_verdict: str

class DailyQueryStat(BaseModel):
    date: str
    query_count: int
    average_latency_ms: float

class ModelUsageStat(BaseModel):
    model_name: str
    usage_count: int
    percentage: float

class DocumentQueryStat(BaseModel):
    document_id: Optional[int]
    filename: str
    query_count: int

class RecentQueryLogItem(BaseModel):
    id: int
    question_text: str
    document_id: Optional[int]
    latency_ms: float
    cache_hit: bool
    model_used: str
    created_at: datetime

class AnalyticsDashboardResponse(BaseModel):
    total_queries: int
    average_latency_ms: float
    cache_hit_ratio_percentage: float
    total_tokens_estimated: int
    daily_trends: List[DailyQueryStat]
    model_breakdown: List[ModelUsageStat]
    popular_documents: List[DocumentQueryStat]
    recent_queries: List[RecentQueryLogItem]

class ExportPdfMessageItem(BaseModel):
    sender_role: str
    message_text: str
    timestamp: Optional[datetime] = None

class ExportSessionPdfRequest(BaseModel):
    thread_id: Optional[int] = None
    session_title: Optional[str] = "TokenBrief Intelligence Report"
    document_ids: Optional[List[int]] = None
    messages: Optional[List[ExportPdfMessageItem]] = None

class ExtractEntitiesRequest(BaseModel):
    document_id: int

class DocumentEntityItem(BaseModel):
    id: int
    document_id: int
    entity_text: str
    entity_type: str
    source_page_number: Optional[int] = None
    occurrence_count: int
    confidence_score: float

    model_config = ConfigDict(from_attributes=True)

class DocumentEntitiesResponse(BaseModel):
    document_id: int
    total_entities: int
    entities_by_type: Dict[str, List[str]]
    entities: List[DocumentEntityItem]

class GraphNode(BaseModel):
    id: str
    label: str
    group: str
    size: int = 10

class GraphLink(BaseModel):
    source: str
    target: str
    relationship: str
    weight: float = 1.0

class KnowledgeGraphResponse(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]
    summary: Dict[str, Any]

class CreateAnnotationRequest(BaseModel):
    document_id: int
    chunk_id: Optional[int] = None
    highlighted_text: str = Field(min_length=1)
    annotation_note: Optional[str] = None
    color_code: Optional[str] = "yellow"
    source_page_number: Optional[int] = None

class UpdateAnnotationRequest(BaseModel):
    annotation_note: Optional[str] = None
    color_code: Optional[str] = None

class UserAnnotationResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    chunk_id: Optional[int]
    highlighted_text: str
    annotation_note: Optional[str]
    color_code: str
    source_page_number: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentAnnotationsResponse(BaseModel):
    document_id: int
    total_annotations: int
    annotations: List[UserAnnotationResponse]

