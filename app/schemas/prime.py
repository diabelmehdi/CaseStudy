from pydantic import BaseModel, ConfigDict, field_validator
from typing import List
from datetime import datetime


class PrimeRequest(BaseModel):
    start: int
    end: int

    @field_validator("start")
    @classmethod
    def start_must_be_positive(cls, v):
        if v < 1:
            raise ValueError("start must be a positive integer")
        return v

    @field_validator("end")
    @classmethod
    def end_must_be_positive(cls, v):
        if v < 1:
            raise ValueError("end must be a positive integer")
        return v


class PrimeResponse(BaseModel):
    id: int
    range_start: int
    range_end: int
    primes: List[int]
    prime_count: int
    execution_time_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    environment: str
