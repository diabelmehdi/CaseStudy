from sqlalchemy import Column, Integer, String, DateTime, ARRAY
from sqlalchemy.sql import func
from app.db.session import Base


class PrimeQuery(Base):
    __tablename__ = "prime_queries"

    id = Column(Integer, primary_key=True, index=True)
    range_start = Column(Integer, nullable=False)
    range_end = Column(Integer, nullable=False)
    prime_count = Column(Integer, nullable=False)
    primes = Column(String, nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
