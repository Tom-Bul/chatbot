import requests
from bs4 import BeautifulSoup
from src.utils.logging import log_step
from colorama import Fore, Style
from urllib.parse import urljoin, urlparse, unquote
from src.utils.colors import Colors

class SearchEngine:
    """
    SearchEngine class handles web searches using DuckDuckGo's HTML interface.
    
    This class is responsible for:
    - Performing searches using DuckDuckGo's HTML endpoint
    - Parsing search results into a structured format
    - Filtering out problematic URLs and file types
    - Handling errors and providing appropriate feedback
    """

    @log_step("Searching the web")
    def search(self, query, num_results=10):
        """
        Performs a web search using DuckDuckGo's HTML interface.
        
        Args:
            query (str): The search query to execute
            num_results (int, optional): Maximum number of results to return. Defaults to 10.
            
        Returns:
            list: List of dictionaries containing search results with 'id', 'link', and 'search_description'
        """
        Colors.print("Searching DuckDuckGo", Colors.SYSTEM)
        
        # Set up headers to mimic a real browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Construct the DuckDuckGo HTML search URL
        url = f'https://html.duckduckgo.com/html/?q={query}'
        
        try:
            # Make the request and verify successful response
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse the results and handle success/failure cases
            results = self._parse_results(response.text)
            if results:
                Colors.print(f"Found {len(results)} results", Colors.SUCCESS)
            else:
                Colors.print("No results found", Colors.WARNING)
            return results
            
        except Exception as e:
            print(f'{Fore.RED}[Search error: {str(e)}]{Style.RESET_ALL}')
            return []

    def _parse_results(self, html):
        """
        Parses the HTML response from DuckDuckGo into structured results.
        
        Args:
            html (str): Raw HTML content from DuckDuckGo search
            
        Returns:
            list: List of dictionaries containing parsed search results
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # Iterate through search results, limiting to first 10
        for i, result in enumerate(soup.find_all('div', class_='result'), start=0):
            if i >= 10:
                break

            # Extract title and link
            title_tag = result.find('a', class_='result__a')
            if not title_tag:
                continue

            link = title_tag['href']
            
            # Skip problematic URLs and file types (e.g., PDFs, social media)
            if any(x in link.lower() for x in [
                '.pdf', '.doc', '.docx', '.ppt', '.pptx',  # Document files
                'twitter.com', 'facebook.com', 'instagram.com',  # Social media
                'youtube.com', 'tiktok.com'  # Video platforms
            ]):
                continue

            # Extract and clean the search result snippet
            snippet_tag = result.find('a', class_='result__snippet')
            snippet = snippet_tag.text.strip() if snippet_tag else 'No description available'

            # Add the parsed result to our list
            results.append({
                'id': i,  # Unique identifier for this result
                'link': link,  # URL of the result
                'search_description': snippet  # Preview text from the webpage
            })

        return results 