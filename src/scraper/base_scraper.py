from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, TimeoutError
import logging

class BaseScraper(ABC):
    def __init__(self):
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_browser_context(self, playwright):
        """
        Cria um contexto do navegador com configurações padrão
        """
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            bypass_csp=True,
            java_script_enabled=True,
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        return browser, context

    def _create_page(self, context):
        """
        Cria uma nova página com configurações padrão
        """
        page = context.new_page()
        page.set_default_timeout(10000)  # 10 segundos
        return page

    async def _navigate_to_url(self, page, url):
        """
        Navega para uma URL com tratamento de erro
        """
        try:
            await page.goto(url, wait_until='networkidle')
            return True
        except TimeoutError:
            self.logger.error(f"Timeout ao acessar {url}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao acessar {url}: {str(e)}")
            return False
