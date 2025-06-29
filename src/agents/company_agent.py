"""
Intelligent Agent for coordinating company data extraction and database operations.
"""
import os
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_openai_tools_agent

from extractors.company_extractor import CompanyExtractor
from database.operations import CompanyDatabaseOperations
from database.models import DatabaseManager
from models.company import CompanyData, ExtractedData, DatabaseConfig


class CompanyAgent:
    """Intelligent agent for company data extraction and database management."""
    
    def __init__(self, openai_api_key: str, db_config: DatabaseConfig, model_name: str = "gpt-3.5-turbo"):
        """Initialize the agent with OpenAI API key and database configuration."""
        self.openai_api_key = openai_api_key
        self.db_config = db_config
        
        # Initialize components
        self.extractor = CompanyExtractor(openai_api_key, model_name)
        self.db_manager = CompanyDatabaseOperations(
            DatabaseManager(db_config.connection_string)
        )
        
        # Initialize LLM for agent
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model_name,
            temperature=0.1
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _create_tools(self) -> List:
        """Create tools for the agent."""
        
        @tool
        def extract_company_data(text: str) -> str:
            """Extract company information from text using LCEL framework."""
            try:
                extracted_data = self.extractor.extract_from_text(text)
                result = {
                    "total_companies": extracted_data.total_companies,
                    "companies": [
                        {
                            "company_name": company.company_name,
                            "founded_in": str(company.founding_date) if company.founding_date else None,
                            "founded_by": company.founders,
                        }
                        for company in extracted_data.companies
                    ]
                }
                return f"Successfully extracted {extracted_data.total_companies} companies: {result}"
            except Exception as e:
                return f"Error extracting company data: {str(e)}"
        
        @tool
        def store_company_data(text: str) -> str:
            """Extract and store company information in the database."""
            try:
                # Extract data
                extracted_data = self.extractor.extract_from_text(text)
                
                if extracted_data.total_companies == 0:
                    return "No company data found in the provided text."
                
                # Store in database
                results = self.db_manager.insert_extracted_data(extracted_data)
                
                return f"Successfully stored {results['successful_inserts']} companies. Failed: {results['failed_inserts']}. Company IDs: {results['inserted_ids']}"
            except Exception as e:
                return f"Error storing company data: {str(e)}"
        
        @tool
        def search_companies(search_term: str) -> str:
            """Search for companies by name or founder."""
            try:
                companies = self.db_manager.search_companies(search_term)
                if not companies:
                    return f"No companies found matching '{search_term}'"
                
                result = f"Found {len(companies)} companies matching '{search_term}':\n"
                for company in companies:
                    result += f"- {company['company_name']} (ID: {company['id']})\n"
                    if company['founded_by']:
                        result += f"  Founded by: {', '.join(company['founded_by'])}\n"
                    if company['founded_in']:
                        result += f"  Founded: {company['founded_in']}\n"
                    result += "\n"
                
                return result
            except Exception as e:
                return f"Error searching companies: {str(e)}"
        
        @tool
        def get_company_details(company_name: str) -> str:
            """Get detailed information about a specific company."""
            try:
                company = self.db_manager.get_company_by_name(company_name)
                if not company:
                    return f"Company '{company_name}' not found in database."
                
                result = f"Company Details for '{company['company_name']}':\n"
                result += f"ID: {company['id']}\n"
                result += f"Name: {company['company_name']}\n"
                if company['founded_in']:
                    result += f"Founded: {company['founded_in']}\n"
                if company['founded_by']:
                    result += f"Founded by: {', '.join(company['founded_by'])}\n"
                result += f"Created: {company['created_at']}\n"
                result += f"Updated: {company['updated_at']}\n"
                
                return result
            except Exception as e:
                return f"Error getting company details: {str(e)}"
        
        @tool
        def get_database_statistics() -> str:
            """Get statistics about the database."""
            try:
                stats = self.db_manager.get_statistics()
                result = "Database Statistics:\n"
                result += f"Total Companies: {stats['total_companies']}\n"
                result += f"Total Founders: {stats['total_founders']}\n"
                result += f"Companies with Founding Dates: {stats['companies_with_founding_dates']}\n"
                result += f"Companies without Founding Dates: {stats['companies_without_founding_dates']}\n"
                
                return result
            except Exception as e:
                return f"Error getting database statistics: {str(e)}"
        
        @tool
        def list_all_companies(limit: int = 10) -> str:
            """List all companies in the database with optional limit."""
            try:
                companies = self.db_manager.get_all_companies(limit=limit)
                if not companies:
                    return "No companies found in database."
                
                result = f"Listing {len(companies)} companies:\n"
                for company in companies:
                    result += f"- {company['company_name']} (ID: {company['id']})\n"
                    if company['founded_by']:
                        result += f"  Founded by: {', '.join(company['founded_by'])}\n"
                    if company['founded_in']:
                        result += f"  Founded: {company['founded_in']}\n"
                    result += "\n"
                
                return result
            except Exception as e:
                return f"Error listing companies: {str(e)}"
        
        return [
            extract_company_data,
            store_company_data,
            search_companies,
            get_company_details,
            get_database_statistics,
            list_all_companies
        ]
    
    def _create_agent(self):
        """Create the agent with tools."""
        prompt = ChatPromptTemplate.from_template("""
        You are an intelligent agent specialized in extracting and managing company information from text.
        
        Your capabilities include:
        1. Extracting company details (names, founding dates, founders) from text using LCEL framework
        2. Storing extracted data in PostgreSQL database
        3. Searching and retrieving company information
        4. Providing database statistics
        
        When a user asks you to process text or perform database operations, use the appropriate tools.
        Always provide clear, helpful responses and explain what you're doing.
        
        User request: {input}
        
        {agent_scratchpad}
        """)
        
        return create_openai_tools_agent(self.llm, self.tools, prompt)
    
    def process_text(self, text: str) -> str:
        """Process text to extract and store company information."""
        try:
            # First extract the data
            extracted_data = self.extractor.extract_from_text(text)
            
            if extracted_data.total_companies == 0:
                return "No company information found in the provided text."
            
            # Store in database
            results = self.db_manager.insert_extracted_data(extracted_data)
            
            return f"Successfully processed text and found {extracted_data.total_companies} companies. Stored {results['successful_inserts']} companies in database. Failed: {results['failed_inserts']}"
            
        except Exception as e:
            return f"Error processing text: {str(e)}"
    
    def run_agent(self, user_input: str) -> str:
        """Run the agent with user input."""
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result["output"]
        except Exception as e:
            return f"Error running agent: {str(e)}"
    
    def extract_with_streaming(self, text: str):
        """Extract company information with streaming support."""
        return self.extractor.extract_with_streaming(text)
    
    def batch_process(self, texts: List[str]) -> List[str]:
        """Process multiple texts in batch."""
        results = []
        for text in texts:
            result = self.process_text(text)
            results.append(result)
        return results 