from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
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
