"""
Database operations for company data storage and retrieval.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import DatabaseManager, CompanyDetails
from models.company import CompanyData, ExtractedData


class CompanyDatabaseOperations:
    """Handles all database operations for company data."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db_manager = db_manager
    
    def insert_company_data(self, company_data: CompanyData) -> Optional[int]:
        """Insert a single company data into the database."""
        session = self.db_manager.get_session()
        try:
            # Check if company already exists
            existing_company = session.query(CompanyDetails).filter(
                CompanyDetails.company_name.ilike(company_data.company_name)
            ).first()
            
            if existing_company:
                # Update existing company
                existing_company.founded_in = company_data.founding_date
                existing_company.set_founders(company_data.founders)
                
                session.commit()
                return existing_company.id
            else:
                # Create new company
                company = CompanyDetails(
                    company_name=company_data.company_name,
                    founded_in=company_data.founding_date
                )
                company.set_founders(company_data.founders)
                
                session.add(company)
                session.commit()
                return company.id
                
        except Exception as e:
            session.rollback()
            print(f"Error inserting company data: {e}")
            return None
        finally:
            self.db_manager.close_session(session)
    
    def insert_extracted_data(self, extracted_data: ExtractedData) -> Dict[str, Any]:
        """Insert multiple company data entries."""
        results = {
            "total_companies": extracted_data.total_companies,
            "successful_inserts": 0,
            "failed_inserts": 0,
            "inserted_ids": []
        }
        
        for company in extracted_data.companies:
            company_id = self.insert_company_data(company)
            if company_id:
                results["successful_inserts"] += 1
                results["inserted_ids"].append(company_id)
            else:
                results["failed_inserts"] += 1
        
        return results
    
    def get_company_by_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve company by ID."""
        session = self.db_manager.get_session()
        try:
            company = session.query(CompanyDetails).filter(CompanyDetails.id == company_id).first()
            if company:
                return {
                    "id": company.id,
                    "company_name": company.company_name,
                    "founded_in": company.founded_in,
                    "founded_by": company.get_founders(),
                    "created_at": company.created_at,
                    "updated_at": company.updated_at
                }
            return None
        finally:
            self.db_manager.close_session(session)
    
    def get_company_by_name(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve company by name (case-insensitive)."""
        session = self.db_manager.get_session()
        try:
            company = session.query(CompanyDetails).filter(
                CompanyDetails.company_name.ilike(company_name)
            ).first()
            if company:
                return {
                    "id": company.id,
                    "company_name": company.company_name,
                    "founded_in": company.founded_in,
                    "founded_by": company.get_founders(),
                    "created_at": company.created_at,
                    "updated_at": company.updated_at
                }
            return None
        finally:
            self.db_manager.close_session(session)
    
    def search_companies(self, search_term: str) -> List[Dict[str, Any]]:
        """Search companies by name or founder."""
        session = self.db_manager.get_session()
        try:
            # Search by company name
            companies_by_name = session.query(CompanyDetails).filter(
                CompanyDetails.company_name.ilike(f"%{search_term}%")
            ).all()
            
            # Search by founder (using JSON search)
            companies_by_founder = session.query(CompanyDetails).filter(
                CompanyDetails.founded_by.ilike(f"%{search_term}%")
            ).all()
            
            # Combine and deduplicate results
            all_companies = list(set(companies_by_name + companies_by_founder))
            
            return [{
                "id": company.id,
                "company_name": company.company_name,
                "founded_in": company.founded_in,
                "founded_by": company.get_founders(),
                "created_at": company.created_at,
                "updated_at": company.updated_at
            } for company in all_companies]
        finally:
            self.db_manager.close_session(session)
    
    def get_all_companies(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all companies with optional pagination."""
        session = self.db_manager.get_session()
        try:
            query = session.query(CompanyDetails).offset(offset)
            if limit:
                query = query.limit(limit)
            
            companies = query.all()
            
            return [{
                "id": company.id,
                "company_name": company.company_name,
                "founded_in": company.founded_in,
                "founded_by": company.get_founders(),
                "created_at": company.created_at,
                "updated_at": company.updated_at
            } for company in companies]
        finally:
            self.db_manager.close_session(session)
    
    def get_companies_by_founder(self, founder_name: str) -> List[Dict[str, Any]]:
        """Get all companies founded by a specific person."""
        session = self.db_manager.get_session()
        try:
            companies = session.query(CompanyDetails).filter(
                CompanyDetails.founded_by.ilike(f"%{founder_name}%")
            ).all()
            
            return [{
                "id": company.id,
                "company_name": company.company_name,
                "founded_in": company.founded_in,
                "founded_by": company.get_founders(),
                "created_at": company.created_at,
                "updated_at": company.updated_at
            } for company in companies]
        finally:
            self.db_manager.close_session(session)
    
    def delete_company(self, company_id: int) -> bool:
        """Delete a company."""
        session = self.db_manager.get_session()
        try:
            company = session.query(CompanyDetails).filter(CompanyDetails.id == company_id).first()
            if company:
                session.delete(company)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error deleting company: {e}")
            return False
        finally:
            self.db_manager.close_session(session)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        session = self.db_manager.get_session()
        try:
            total_companies = session.query(CompanyDetails).count()
            
            # Get companies with founding dates
            companies_with_dates = session.query(CompanyDetails).filter(
                CompanyDetails.founded_in.isnot(None)
            ).count()
            
            # Count total founders (approximate from JSON)
            total_founders = 0
            companies = session.query(CompanyDetails).all()
            for company in companies:
                total_founders += len(company.get_founders())
            
            return {
                "total_companies": total_companies,
                "total_founders": total_founders,
                "companies_with_founding_dates": companies_with_dates,
                "companies_without_founding_dates": total_companies - companies_with_dates
            }
        finally:
            self.db_manager.close_session(session) 