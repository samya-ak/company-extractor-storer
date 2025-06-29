"""
LCEL-based company information extractor using LangChain.
"""
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

from models.company import CompanyData, ExtractedData


class CompanyExtractor:
    """LCEL-based extractor for company information from text."""
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-3.5-turbo"):
        """Initialize the extractor with OpenAI API key."""
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model_name,
            temperature=0.1
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", "! ", "? "]
        )
        
        # Define the extraction prompt
        self.extraction_prompt = ChatPromptTemplate.from_template("""
You are an expert at extracting company information from text. 
Analyze the following paragraph and extract company details in JSON format.

Text to analyze:
{text}

Extract the following information:
- company_name: The name of the company (required)
- founding_date: The founding date in ISO format (YYYY-MM-DD) if available, or null if not found
- founders: List of founder names as strings

If multiple companies are mentioned, extract information for each one.
If only year is provided for founding date, use January 1st of that year.
If year and month are provided, use the 1st day of that month.

Return the result as a valid JSON array with objects containing these fields.
If no company information is found, return an empty array.

Example output format:
[
    {{
        "company_name": "Example Corp",
        "founding_date": "2020-01-01",
        "founders": ["John Doe", "Jane Smith"]
    }}
]
""")
        
        # Create the LCEL chain
        self.extraction_chain = (
            {"text": RunnablePassthrough()}
            | self.extraction_prompt
            | self.llm
            | JsonOutputParser()
        )
    
    def extract_from_paragraph(self, paragraph: str) -> List[CompanyData]:
        """Extract company information from a single paragraph."""
        try:
            # Clean the paragraph
            cleaned_paragraph = self._clean_text(paragraph)
            if not cleaned_paragraph.strip():
                return []
            
            # Extract using LCEL chain
            result = self.extraction_chain.invoke(cleaned_paragraph)
            
            # Convert to CompanyData objects
            companies = []
            for company_info in result:
                try:
                    company_data = CompanyData(
                        company_name=company_info.get("company_name", ""),
                        founding_date=company_info.get("founding_date"),
                        founders=company_info.get("founders", [])
                    )
                    companies.append(company_data)
                except Exception as e:
                    print(f"Error processing company data: {e}")
                    continue
            
            return companies
            
        except Exception as e:
            print(f"Error extracting from paragraph: {e}")
            return []
    
    def extract_from_text(self, text: str) -> ExtractedData:
        """Extract company information from full text by processing paragraphs."""
        # Split text into paragraphs
        paragraphs = self._split_into_paragraphs(text)
        
        extracted_data = ExtractedData()
        
        for paragraph in paragraphs:
            companies = self.extract_from_paragraph(paragraph)
            for company in companies:
                extracted_data.add_company(company)
        
        return extracted_data
    
    def extract_with_streaming(self, text: str):
        """Extract company information with streaming support."""
        paragraphs = self._split_into_paragraphs(text)
        
        for paragraph in paragraphs:
            companies = self.extract_from_paragraph(paragraph)
            yield {
                "paragraph": paragraph,
                "companies": companies,
                "count": len(companies)
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters that might interfere with parsing
        text = re.sub(r'[^\w\s\.\,\-\:\;\(\)]', '', text)
        return text
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into meaningful paragraphs."""
        # Split by double newlines first
        paragraphs = re.split(r'\n\s*\n', text)
        
        # If paragraphs are too long, split them further
        final_paragraphs = []
        for paragraph in paragraphs:
            if len(paragraph) > 2000:  # If paragraph is too long
                chunks = self.text_splitter.split_text(paragraph)
                final_paragraphs.extend(chunks)
            else:
                final_paragraphs.append(paragraph)
        
        # Filter out empty paragraphs
        return [p.strip() for p in final_paragraphs if p.strip()]
    
    def batch_extract(self, texts: List[str]) -> List[ExtractedData]:
        """Extract company information from multiple texts in batch."""
        results = []
        for text in texts:
            result = self.extract_from_text(text)
            results.append(result)
        return results 