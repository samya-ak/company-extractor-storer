"""
Data models for company information extraction.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from dateutil import parser


class CompanyData(BaseModel):
    """Model for extracted company information."""
    company_name: str = Field(..., description="Name of the company")
    founding_date: Optional[datetime] = Field(None, description="Founding date of the company")
    founders: List[str] = Field(default_factory=list, description="List of company founders")
    
    @validator('founding_date', pre=True)
    def parse_founding_date(cls, v):
        """Parse and validate founding date with fallback logic."""
        if v is None:
            return None
        
        if isinstance(v, datetime):
            return v
        
        if isinstance(v, str):
            try:
                # Try to parse the date string
                parsed_date = parser.parse(v, fuzzy=True)
                return parsed_date
            except (ValueError, TypeError):
                # If parsing fails, return None
                return None
        
        return None


class ExtractedData(BaseModel):
    """Container for multiple company data extractions."""
    companies: List[CompanyData] = Field(default_factory=list, description="List of extracted company data")
    total_companies: int = Field(0, description="Total number of companies extracted")
    
    def add_company(self, company: CompanyData):
        """Add a company to the extracted data."""
        self.companies.append(company)
        self.total_companies = len(self.companies)
    
    def get_companies_by_name(self, name: str) -> List[CompanyData]:
        """Get companies by name (case-insensitive)."""
        return [c for c in self.companies if c.company_name.lower() == name.lower()]
    
    def get_companies_by_founder(self, founder: str) -> List[CompanyData]:
        """Get companies by founder name (case-insensitive)."""
        return [c for c in self.companies if any(f.lower() in founder.lower() for f in c.founders)]


class DatabaseConfig(BaseModel):
    """Configuration for database connection."""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    
    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}" 