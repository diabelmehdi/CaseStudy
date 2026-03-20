import time
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.prime import generate_primes
from app.core.config import get_settings
from app.db.session import get_db
from app.db.models import PrimeQuery
from app.schemas.prime import PrimeRequest, PrimeResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    settings = get_settings()
    return HealthResponse(status="healthy", environment=settings.app_env)


@router.post("/primes", response_model=PrimeResponse)
def find_primes(request: PrimeRequest, db: Session = Depends(get_db)):
    if request.start > request.end:
        raise HTTPException(
            status_code=400,
            detail="'start' must be less than or equal to 'end'"
        )

    if request.end > 10_000_000:
        raise HTTPException(
            status_code=400,
            detail="Range too large. Maximum allowed end value is 10,000,000"
        )

    start_time = time.monotonic()
    primes = generate_primes(request.start, request.end)
    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    record = PrimeQuery(
        range_start=request.start,
        range_end=request.end,
        prime_count=len(primes),
        primes=json.dumps(primes),
        execution_time_ms=elapsed_ms,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PrimeResponse(
        id=record.id,
        range_start=record.range_start,
        range_end=record.range_end,
        primes=primes,
        prime_count=record.prime_count,
        execution_time_ms=record.execution_time_ms,
        created_at=record.created_at,
    )


@router.get("/primes/history", response_model=List[PrimeResponse])
def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    records = (
        db.query(PrimeQuery)
        .order_by(PrimeQuery.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for record in records:
        results.append(
            PrimeResponse(
                id=record.id,
                range_start=record.range_start,
                range_end=record.range_end,
                primes=json.loads(record.primes),
                prime_count=record.prime_count,
                execution_time_ms=record.execution_time_ms,
                created_at=record.created_at,
            )
        )
    return results


@router.get("/primes/{query_id}", response_model=PrimeResponse)
def get_query_by_id(query_id: int, db: Session = Depends(get_db)):
    record = db.query(PrimeQuery).filter(PrimeQuery.id == query_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Query not found")

    return PrimeResponse(
        id=record.id,
        range_start=record.range_start,
        range_end=record.range_end,
        primes=json.loads(record.primes),
        prime_count=record.prime_count,
        execution_time_ms=record.execution_time_ms,
        created_at=record.created_at,
    )
