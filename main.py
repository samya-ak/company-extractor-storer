"""
Main application for the Company Data Extraction System.
"""
import sys
import os
from typing import List, Optional

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.config import Config, create_sample_env_file
from agents.company_agent import CompanyAgent
from database.models import DatabaseManager
from models.company import DatabaseConfig


class CompanyExtractionSystem:
    """Main system class for company data extraction and management."""
    
    def __init__(self, config: Config):
        """Initialize the system with configuration."""
        self.config = config
        self.agent = None
        self.db_manager = None
        
        # Initialize database
        self._init_database()
        
        # Initialize agent
        self._init_agent()
    
    def _init_database(self):
        """Initialize database connection and create tables."""
        try:
            self.db_manager = DatabaseManager(self.config.database_config.connection_string)
            self.db_manager.create_tables()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def _init_agent(self):
        """Initialize the intelligent agent."""
        try:
            self.agent = CompanyAgent(
                openai_api_key=self.config.openai_api_key,
                db_config=self.config.database_config,
                model_name=self.config.model_name
            )
            print("Agent initialized successfully")
        except Exception as e:
            print(f"Error initializing agent: {e}")
            raise
    
    def process_text(self, text: str) -> str:
        """Process text to extract and store company information."""
        return self.agent.process_text(text)
    
    def run_agent(self, user_input: str) -> str:
        """Run the agent with user input."""
        return self.agent.run_agent(user_input)
    
    def extract_with_streaming(self, text: str):
        """Extract company information with streaming support."""
        return self.agent.extract_with_streaming(text)
    
    def batch_process(self, texts: List[str]) -> List[str]:
        """Process multiple texts in batch."""
        return self.agent.batch_process(texts)
    
    def get_database_stats(self) -> str:
        """Get database statistics."""
        return self.agent.run_agent("Get database statistics")
    
    def search_companies(self, search_term: str) -> str:
        """Search for companies."""
        return self.agent.run_agent(f"Search for companies matching '{search_term}'")
    
    def list_companies(self, limit: int = 10) -> str:
        """List companies in the database."""
        return self.agent.run_agent(f"List {limit} companies from the database")


def main():
    """Main function to demonstrate the system."""
    print("🚀 Company Data Extraction System")
    print("=" * 50)
    
    # Check if .env file exists, if not create sample
    if not os.path.exists(".env"):
        print("No .env file found. Creating sample configuration...")
        create_sample_env_file()
        print("\nPlease create a .env file with your configuration and run again.")
        return
    
    try:
        # Load configuration
        config = Config()
        
        if not config.validate():
            print("Configuration validation failed. Please check your .env file.")
            return
        
        print("Configuration loaded successfully!")
        config.print_config()
        print()
        
        # Initialize system
        system = CompanyExtractionSystem(config)
        
        # Example usage
        print("📝 Example: Processing essay.txt file...")
        
        # Read the essay.txt file
        essay_file_path = os.path.join(os.path.dirname(__file__), 'src', 'samples', 'essay.txt')
        try:
            with open(essay_file_path, 'r', encoding='utf-8') as file:
                sample_text = file.read()
            print(f"Successfully loaded essay.txt ({len(sample_text)} characters)")
        except FileNotFoundError:
            print(f"Error: Could not find essay.txt at {essay_file_path}")
            return
        except Exception as e:
            print(f"Error reading essay.txt: {e}")
            return
        
        # Process the text
        result = system.process_text(sample_text)
        print(f"Result: {result}")
        print()
        
        # Get database statistics
        print("📊 Database Statistics:")
        stats = system.get_database_stats()
        print(stats)
        print()
        
        # Search for companies
        print("🔍 Searching for companies:")
        search_result = system.search_companies("Apple")
        print(search_result)
        print()
        
        # List all companies
        print("📋 All Companies in Database:")
        companies = system.list_companies(5)
        print(companies)
        
        # Interactive mode
        print("\n🤖 Interactive Mode - Type 'quit' to exit")
        print("You can ask questions like:")
        print("- 'Search for companies founded by Steve Jobs'")
        print("- 'Get details about Apple'")
        print("- 'List all companies'")
        print("- 'Get database statistics'")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_input:
                    response = system.run_agent(user_input)
                    print(f"Agent: {response}")
                    print()
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                print()
    
    except Exception as e:
        print(f"Error: {e}")
        print("\nPlease check your configuration and try again.")


if __name__ == "__main__":
    main() 