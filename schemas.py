from datetime import datetime
from typing import Optional, List
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
