import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from config import settings

Base = declarative_base()

def create_database_engine():
    connection_url = settings.get_normalized_database_url()
    connection_arguments = {}

    if "neon.tech" in connection_url or "sslmode" in connection_url or "ssl=require" in connection_url:
        ssl_security_context = ssl.create_default_context()
        ssl_security_context.check_hostname = False
        ssl_security_context.verify_mode = ssl.CERT_NONE
        connection_arguments["ssl"] = ssl_security_context

        if "?" in connection_url:
            base_url, query_parameters = connection_url.split("?", 1)
            retained_parameters = [
                param for param in query_parameters.split("&")
                if not param.lower().startswith("ssl") and not param.lower().startswith("channel_binding")
            ]
            connection_url = f"{base_url}?{'&'.join(retained_parameters)}" if retained_parameters else base_url

    return create_async_engine(
        connection_url,
        echo=False,
        connect_args=connection_arguments,
        pool_pre_ping=True
    )

database_engine = create_database_engine()

database_session_factory = async_sessionmaker(
    bind=database_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_database_session():
    async with database_session_factory() as active_session:
        try:
            yield active_session
        finally:
            await active_session.close()

async def initialize_database_tables():
    async with database_engine.begin() as database_connection:
        await database_connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await database_connection.run_sync(Base.metadata.create_all)
        try:
            await database_connection.execute(
                text("CREATE INDEX IF NOT EXISTS ix_chunks_vector_hnsw ON document_chunk_records USING hnsw (embedding_vector vector_cosine_ops);")
            )
        except Exception:
            pass
