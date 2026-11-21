import os
from sqlalchemy import BigInteger, Column, Date, Float, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

url = os.getenv("DATABASE_URL", "sqlite:///./market.db")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)
engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)
Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"
    symbol = Column(String(16), primary_key=True)
    source = Column(String(16), nullable=False)  # yfinance | csv | synthetic


class Price(Base):
    __tablename__ = "market_prices"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(16), nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    __table_args__ = (UniqueConstraint("symbol", "date", name="uq_symbol_date"),)  # no duplicate days


Base.metadata.create_all(engine)
