import requests
from bs4 import BeautifulSoup
from src.utils.logging import log_step
from colorama import Fore, Style
from urllib.parse import urljoin, urlparse, unquote
from src.utils.colors import Colors

class SearchEngine:
    @log_step("Searching the web")
    def search(self, query):
        Colors.print("Searching DuckDuckGo", Colors.SYSTEM)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url = f'https://html.duckduckgo.com/html/?q={query}'
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            results = self._parse_results(response.text)
            if results:
                Colors.print(f"Found {len(results)} results", Colors.SUCCESS)
            else:
                Colors.print("No results found", Colors.WARNING)
            return results
        except Exception as e:
            Colors.print(f"Failed: {str(e)}", Colors.ERROR)
            return []

    def _parse_results(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        for i, result in enumerate(soup.find_all('div', class_='result'), start=0):
            if i >= 10:
                break

            title_tag = result.find('a', class_='result__a')
            if not title_tag:
                continue

            link = title_tag['href']
            
            # Skip problematic URLs and file types
            if any(x in link.lower() for x in [
                '.pdf', '.doc', '.docx', '.ppt', '.pptx',
                'twitter.com', 'facebook.com', 'instagram.com',
                'youtube.com', 'tiktok.com'
            ]):
                continue

            snippet_tag = result.find('a', class_='result__snippet')
            snippet = snippet_tag.text.strip() if snippet_tag else 'No description available'

            results.append({
                'id': i,
                'link': link,
                'search_description': snippet
            })

        return results 