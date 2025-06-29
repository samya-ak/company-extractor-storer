"""
SQLAlchemy models for database tables.
"""
from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import json

Base = declarative_base()


class CompanyDetails(Base):
    """Database model for company details."""
    __tablename__ = "company_details"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    founded_in = Column(DateTime, nullable=True, index=True)
    founded_by = Column(Text, nullable=True)  # JSON string of founder names
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def get_founders(self) -> List[str]:
        """Get founders as a list of strings."""
        if hasattr(self, 'founded_by') and self.founded_by is not None:
            try:
                return json.loads(str(self.founded_by))
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_founders(self, founders: List[str]):
        """Set founders from a list of strings."""
        self.founded_by = json.dumps(founders) if founders else None
    
    def __repr__(self):
        return f"<CompanyDetails(id={self.id}, name='{self.company_name}', founded_in={self.founded_in}, founded_by={self.get_founders()})>"


class DatabaseManager:
    """Manager class for database operations."""
    
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close a database session."""
        session.close() 