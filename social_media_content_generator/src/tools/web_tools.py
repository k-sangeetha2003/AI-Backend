from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from langchain_core.tools import tool
from pydantic import BaseModel, Field

def scrape_url(url: str) -> Dict:
    """
    Scrapes content from a given URL.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        Dict: Scraped content or error information
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return {
                "status": "error",
                "error": "Invalid URL format",
                "url": url
            }

        # Make request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract metadata
        title = soup.title.string if soup.title else ""
        meta_description = soup.find("meta", {"name": "description"})
        description = meta_description["content"] if meta_description else ""
        
        # Extract main content
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return {
            "url": url,
            "title": title,
            "description": description,
            "content": text[:5000],  # Limit content length
            "status": "success"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": url
        }

# Create the URL scraper tool using the new decorator format
@tool
def url_scraper(url: str) -> Dict:
    """
    Scrapes content from a given URL.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        Dict: Scraped content or error information
    """
    return scrape_url(url) 