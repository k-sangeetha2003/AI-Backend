import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from urllib.parse import urlparse

class URLScraper:
    @staticmethod
    def scrape_url(url: str) -> Optional[Dict]:
        """
        Scrapes content from a given URL.
        
        Args:
            url (str): The URL to scrape
            
        Returns:
            Optional[Dict]: Scraped content or None if failed
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                return None

            # Make request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
                "url": url,
                "error": str(e),
                "status": "failed"
            }

    @staticmethod
    def extract_key_points(content: Dict) -> Dict:
        """
        Extracts key points from scraped content.
        
        Args:
            content (Dict): Scraped content dictionary
            
        Returns:
            Dict: Extracted key points
        """
        if content["status"] == "failed":
            return content
            
        # Extract key points (to be implemented with NLP)
        key_points = {
            "title": content["title"],
            "summary": content["description"],
            "main_topics": [],
            "key_phrases": [],
            "sentiment": "",
            "source_url": content["url"]
        }
        
        return key_points 