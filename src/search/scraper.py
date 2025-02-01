import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style
import time
from src.utils.colors import Colors

class WebScraper:
    def scrape(self, url):
        Colors.print("Scraping webpage", Colors.SYSTEM)
        try:
            # Extract actual URL from DuckDuckGo redirect
            if 'duckduckgo.com/l/?' in url:
                url = url.split('uddg=')[1].split('&')[0]
                url = requests.utils.unquote(url)
                Colors.print(f"Redirecting to: {url}", Colors.SYSTEM)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
            
            # Add delay to avoid rate limiting
            time.sleep(1)
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'meta', 'link', 'header', 'footer', 'nav', 'iframe', 'form', 'aside']):
                element.decompose()
            
            # Try to find main content with more specific selectors for news sites
            main_content = None
            selectors = [
                'article', 'main', 
                '.article-body', '.article-content', '.story-body', '.story-content',
                '#article-body', '#story-body', '#content-body',
                '.main-content', '.post-content', '.entry-content',
                '[role="main"]', '[role="article"]'
            ]
            
            for selector in selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if main_content:
                # Get paragraphs from main content
                paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                content = '\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
            else:
                # Fallback to body content
                body = soup.find('body')
                if body:
                    paragraphs = body.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    content = '\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
                else:
                    content = soup.get_text(separator='\n', strip=True)
            
            # Clean up the content
            content = '\n'.join(line.strip() for line in content.splitlines() if line.strip())
            
            if len(content) > 200:  # Increased minimum length
                Colors.print(f"Success: {len(content)} chars", Colors.SUCCESS)
                return content
            else:
                Colors.print(f"Content too short: {len(content)} chars", Colors.WARNING)
                return None
                
        except Exception as e:
            Colors.print(f"Error: {str(e)}", Colors.ERROR)
            return None 