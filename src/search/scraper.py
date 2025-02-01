import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style
import time
from src.utils.colors import Colors

class WebScraper:
    def scrape(self, url):
        Colors.print("Scraping webpage", Colors.SYSTEM)
        try:
            # Fix URLs missing scheme
            if url.startswith('//'):
                url = 'https:' + url

            # Extract actual URL from DuckDuckGo redirect
            if 'duckduckgo.com/l/?' in url:
                url = url.split('uddg=')[1].split('&')[0]
                url = requests.utils.unquote(url)
                Colors.print(f"Redirecting to: {url}", Colors.SYSTEM)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Add delay to avoid rate limiting
            time.sleep(1)
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Check for redirect
            if response.history:
                print(f'{Fore.YELLOW}[Redirecting to: {response.url}]{Style.RESET_ALL}')
                
            # Handle common error codes
            if response.status_code == 403:
                print(f'{Fore.RED}[Access denied - trying alternative source]{Style.RESET_ALL}')
                return None
            elif response.status_code != 200:
                print(f'{Fore.RED}[Error: HTTP {response.status_code}]{Style.RESET_ALL}')
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Limit text length
            
        except requests.exceptions.RequestException as e:
            print(f'{Fore.RED}[Scraping error: {str(e)}]{Style.RESET_ALL}')
            return None

    def scrape_alternative(self, url):
        # Implementation of scrape_alternative method
        pass

    def scrape_fallback(self, url):
        # Implementation of scrape_fallback method
        pass 