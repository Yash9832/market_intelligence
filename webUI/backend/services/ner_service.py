"""
NER (Named Entity Recognition) service for extracting entities from user queries.
Specifically focused on identifying stock symbols, company names, and financial entities.
"""

from transformers import pipeline
from typing import List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

class NERService:
    """Service for Named Entity Recognition with focus on financial entities"""
    
    def __init__(self):
        """Initialize the NER pipeline"""
        try:
            # Use a financial/business focused NER model
            self.ner_pipeline = pipeline(
                "ner", 
                model="dslim/bert-base-NER", 
                grouped_entities=True
            )
            logger.info("NER pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NER pipeline: {e}")
            raise
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from text using NER model
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict containing entities and analysis
        """
        try:
            # Get NER results
            ner_results = self.ner_pipeline(text)
            
            entities = []
            organizations = []
            
            for ent in ner_results:
                entity = {
                    "entity": ent['entity_group'],
                    "word": ent['word'],
                    "start": ent['start'],
                    "end": ent['end'],
                    "score": float(ent['score'])
                }
                entities.append(entity)
                
                # Collect organizations (potential company names/stock symbols)
                if ent['entity_group'] in ['ORG', 'ORGANIZATION']:
                    organizations.append(ent['word'].strip())
            
            # Also try to extract potential stock symbols using regex
            potential_symbols = self._extract_stock_symbols(text)
            
            return {
                "text": text,
                "entities": entities,
                "organizations": organizations,
                "potential_stock_symbols": potential_symbols,
                "summary": self._create_summary(entities, organizations, potential_symbols)
            }
            
        except Exception as e:
            logger.error(f"Error in NER extraction: {e}")
            return {
                "text": text,
                "entities": [],
                "organizations": [],
                "potential_stock_symbols": [],
                "summary": "Error in entity extraction",
                "error": str(e)
            }
    
    def _extract_stock_symbols(self, text: str) -> List[str]:
        """
        Extract potential stock symbols using regex patterns and company name matching
        
        Args:
            text (str): Input text
            
        Returns:
            List of potential stock symbols
        """
        symbols = []
        text_lower = text.lower()
        
        # Direct company name to symbol mapping
        company_mappings = {
            "apple": "AAPL",
            "microsoft": "MSFT", 
            "nvidia": "NVDA",
            "tesla": "TSLA",
            "amazon": "AMZN",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
            "intel": "INTL",
            "amd": "AMD",
            "oracle": "ORCL",
            "salesforce": "CRM",
            "adobe": "ADBE",
            "paypal": "PYPL",
            "uber": "UBER",
            "lyft": "LYFT",
            "airbnb": "ABNB",
            "zoom": "ZM",
            "slack": "WORK",
            "twitter": "TWTR",
            "linkedin": "LNKD",
            "snapchat": "SNAP",
            "pinterest": "PINS",
            "shopify": "SHOP",
            "square": "SQ",
            "paypal": "PYPL",
            "visa": "V",
            "mastercard": "MA",
            "goldman sachs": "GS",
            "jpmorgan": "JPM",
            "bank of america": "BAC",
            "wells fargo": "WFC",
            "morgan stanley": "MS",
            "goldman": "GS",
            "jpmorgan chase": "JPM",
            "disney": "DIS",
            "coca cola": "KO",
            "pepsi": "PEP",
            "walmart": "WMT",
            "target": "TGT",
            "home depot": "HD",
            "lowes": "LOW",
            "starbucks": "SBUX",
            "mcdonald": "MCD",
            "mcdonalds": "MCD"
        }
        
        # Check for company names in the text
        for company, symbol in company_mappings.items():
            if company in text_lower:
                symbols.append(symbol)
        
        # Also check for direct stock symbols (like AAPL, MSFT)
        stock_pattern = r'\b[A-Z]{1,5}\b'
        potential_symbols = re.findall(stock_pattern, text.upper())
        
        # Filter common words that might be false positives
        common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'USE', 'MAN', 'NEW', 'NOW', 'OLD', 'SEE', 'HIM', 'TWO', 'HOW', 'ITS', 'WHO', 'DID', 'YES', 'HIS', 'HAS', 'HAD', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'WAY', 'WHY', 'BOY', 'RUN', 'TOP', 'TRY', 'ASK', 'EYE', 'JOB', 'OWN', 'ACT', 'AGE', 'END', 'FAR', 'LOT', 'SIT', 'SET', 'WIN', 'YET', 'BAD', 'BAG', 'BED', 'BOX', 'CAR', 'CUT', 'DOG', 'EAR', 'EAT', 'EGG', 'FEW', 'GOT', 'HIT', 'HOT', 'KEY', 'LAY', 'LEG', 'MAP', 'MAY', 'MOM', 'OFF', 'PET', 'RED', 'SUN', 'TEN', 'VAN', 'WET', 'ZIP', 'GOOD', 'BEST', 'OPTION', 'INVEST', 'STOCK', 'COMPANY', 'MARKET', 'PRICE', 'PERFORMANCE', 'ANALYSIS'}
        
        filtered_symbols = [s for s in potential_symbols if s not in common_words and len(s) >= 2]
        symbols.extend(filtered_symbols)
        
        return list(set(symbols))  # Remove duplicates
    
    def _create_summary(self, entities: List[Dict], organizations: List[str], symbols: List[str]) -> str:
        """
        Create a summary of extracted entities
        
        Args:
            entities: All extracted entities
            organizations: Organization entities
            symbols: Potential stock symbols
            
        Returns:
            Summary string
        """
        summary_parts = []
        
        if organizations:
            summary_parts.append(f"Companies/Organizations: {', '.join(organizations)}")
        
        if symbols:
            summary_parts.append(f"Potential Stock Symbols: {', '.join(symbols)}")
        
        if not summary_parts:
            summary_parts.append("No specific financial entities identified")
        
        return " | ".join(summary_parts)

# Global instance for reuse
ner_service = NERService()