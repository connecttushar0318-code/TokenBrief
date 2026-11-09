from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, Float
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base

class UserAccount(Base):
    __tablename__ = "user_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email_address = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    documents = relationship("DocumentRecord", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("ConversationThreadRecord", back_populates="user", cascade="all, delete-orphan")

class EmailVerificationRecord(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email_address = Column(String(255), index=True, nullable=False)
    otp_code = Column(String(10), nullable=False)
    purpose = Column(String(50), default="registration", nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    total_page_count = Column(Integer, default=0)
    total_chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("UserAccount", back_populates="documents")
    chunks = relationship("DocumentChunkRecord", back_populates="document", cascade="all, delete-orphan")
    quiz_questions = relationship("QuizQuestionRecord", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("DocumentEntityRecord", back_populates="document", cascade="all, delete-orphan")
    annotations = relationship("UserAnnotationRecord", back_populates="document", cascade="all, delete-orphan")
    sections = relationship("DocumentSectionRecord", back_populates="document", cascade="all, delete-orphan")

class DocumentSectionRecord(Base):
    __tablename__ = "document_sections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)
    section_index = Column(Integer, nullable=False)
    page_start = Column(Integer, nullable=False)
    page_end = Column(Integer, nullable=False)
    section_title = Column(String(255), nullable=True)
    section_summary = Column(Text, nullable=False)
    key_bullet_points = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("DocumentRecord", back_populates="sections")

class DocumentChunkRecord(Base):
    __tablename__ = "document_chunk_records"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index_number = Column(Integer, nullable=False)
    source_page_number = Column(Integer, nullable=True)
    chunk_text_content = Column(Text, nullable=False)
    embedding_vector = Column(Vector(384), nullable=False)

    document = relationship("DocumentRecord", back_populates="chunks")

class SemanticQueryCacheRecord(Base):
    __tablename__ = "semantic_query_cache"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=True, index=True)
    query_text = Column(Text, nullable=False)
    embedding_vector = Column(Vector(384), nullable=False)
    cached_answer = Column(Text, nullable=False)
    cached_sources_json = Column(Text, nullable=False)
    hit_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConversationThreadRecord(Base):
    __tablename__ = "conversation_threads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("document_records.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("UserAccount", back_populates="conversations")
    messages = relationship("ConversationMessageRecord", back_populates="thread", cascade="all, delete-orphan")

class ConversationMessageRecord(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("conversation_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_role = Column(String(20), nullable=False)
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    thread = relationship("ConversationThreadRecord", back_populates="messages")

class QuizQuestionRecord(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(10), nullable=False)
    explanation = Column(Text, nullable=True)
    source_page_number = Column(Integer, nullable=True)
    difficulty = Column(String(20), default="medium", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("DocumentRecord", back_populates="quiz_questions")
    answers = relationship("QuizAnswerRecord", back_populates="question", cascade="all, delete-orphan")

class QuizAttemptRecord(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)
    total_questions = Column(Integer, nullable=False)
    correct_count = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("UserAccount")
    document = relationship("DocumentRecord")
    answers = relationship("QuizAnswerRecord", back_populates="attempt", cascade="all, delete-orphan")

class QuizAnswerRecord(Base):
    __tablename__ = "quiz_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_option = Column(String(10), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    attempt = relationship("QuizAttemptRecord", back_populates="answers")
    question = relationship("QuizQuestionRecord", back_populates="answers")

class QueryLogRecord(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("document_records.id", ondelete="SET NULL"), nullable=True, index=True)
    question_text = Column(Text, nullable=False)
    latency_ms = Column(Float, nullable=False)
    cache_hit = Column(Boolean, default=False, nullable=False)
    model_used = Column(String(100), nullable=False)
    estimated_token_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("UserAccount")
    document = relationship("DocumentRecord")

class DocumentEntityRecord(Base):
    __tablename__ = "document_entities"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_text = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    source_page_number = Column(Integer, nullable=True)
    occurrence_count = Column(Integer, default=1, nullable=False)
    confidence_score = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("DocumentRecord", back_populates="entities")

class UserAnnotationRecord(Base):
    __tablename__ = "user_annotations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunk_records.id", ondelete="SET NULL"), nullable=True, index=True)
    highlighted_text = Column(Text, nullable=False)
    annotation_note = Column(Text, nullable=True)
    color_code = Column(String(30), default="yellow", nullable=False)
    source_page_number = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("UserAccount")
    document = relationship("DocumentRecord", back_populates="annotations")
    chunk = relationship("DocumentChunkRecord")

