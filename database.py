from sqlmodel import SQLModel, Field, create_engine, Session
from datetime import datetime
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str
    filename: str
    status: str
    charts_count: int
    logs: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

def create_db():
    SQLModel.metadata.create_all(engine)

def save_job(job_id: str, filename: str, status: str, charts_count: int, logs: str):
    with Session(engine) as session:
        job = Job(
            job_id=job_id,
            filename=filename,
            status=status,
            charts_count=charts_count,
            logs=logs
        )
        session.add(job)
        session.commit()

def get_all_jobs():
    with Session(engine) as session:
        jobs = session.exec(SQLModel.select(Job).order_by(Job.created_at.desc())).all()
        return jobs