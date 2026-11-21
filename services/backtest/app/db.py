import os
from datetime import datetime
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

url = os.getenv("DATABASE_URL", "sqlite:///./backtest.db")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)
engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)
Base = declarative_base()


class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    strategy = Column(String(32), nullable=False)
    params = Column(JSON, nullable=False)
    symbol = Column(String(16), nullable=False, index=True)
    start_date = Column(String(10), nullable=False)
    end_date = Column(String(10), nullable=False)
    capital = Column(Float, nullable=False)
    fee_bps = Column(Float, nullable=False)
    data_source = Column(String(16), nullable=False)
    metrics = Column(JSON, nullable=False)
    benchmark_metrics = Column(JSON, nullable=False)


Base.metadata.create_all(engine)
