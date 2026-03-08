import httpx
from bs4 import BeautifulSoup
from src.utils.logger import logger

class BrowserProxy:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def scrape_page(self, url: str):
        """Fetches a web page and extracts the main text content (Reader Mode)."""
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Strip out unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'ads']):
                    element.decompose()
                
                # Simplified "Main Content" heuristic
                # Try to find the biggest body of text
                main_text = ""
                # Priority 1: <main> or <article> tags
                main_content = soup.find(['main', 'article'])
                if main_content:
                    main_text = main_content.get_text(separator='\n', strip=True)
                else:
                    # Priority 2: <body> excluding the stripped elements
                    main_text = soup.body.get_text(separator='\n', strip=True) if soup.body else "No content found."

                # Clean up whitespace
                lines = (line.strip() for line in main_text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)

                return {
                    "url": url,
                    "title": soup.title.string.strip() if soup.title else "Untitled Page",
                    "content": text[:10000] # Limit to 10k chars for reasonable context window
                }

        except Exception as e:
            logger.error(f"BrowserProxy Error on {url}: {e}")
            return {"url": url, "title": "Error", "content": f"Failed to load page: {str(e)}"}

browser_proxy = BrowserProxy()
