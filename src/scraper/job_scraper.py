from playwright.sync_api import sync_playwright, TimeoutError
import logging
from datetime import datetime

class JobScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_jobs(self):
        """
        Método principal para buscar vagas usando Playwright
        """
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                # Criando contexto com configurações adequadas
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
                page = context.new_page()
                
                # Define um timeout menor para todas as operações
                page.set_default_timeout(10000)  # 10 segundos
                
                # Limpa cookies e cache antes de navegar
                context.clear_cookies()
                
                self.logger.info(f"Navegando para: {self.base_url}")
                
                # Navega para a página e aguarda carregar
                response = page.goto(self.base_url, wait_until='networkidle')
                
                if response is None:
                    self.logger.error("Não foi possível obter resposta da página")
                    return None
                
                self.logger.info(f"Status da página: {response.status}")
                
                # Aguarda elementos importantes carregarem
                page.wait_for_selector('h2.js_vacancyHeaderTitle', timeout=10000)
                page.wait_for_selector('.js_vacancyDataPanels', timeout=10000)
                
                # Processa a página e retorna os dados
                job_data = self.parse_jobs(page, self.base_url)
                return job_data
                
            except Exception as e:
                self.logger.error(f"Erro ao buscar vagas: {e}")
                return None
            finally:
                if 'browser' in locals():
                    browser.close()

    def clean_text(self, text):
        """
        Limpa o texto removendo espaços extras e quebras de linha
        """
        if not text:
            return ""
        # Remove quebras de linha e espaços extras
        cleaned = " ".join(text.split())
        return cleaned.strip()

    def clean_location(self, location):
        """
        Limpa o texto de localização removendo o texto desnecessário
        """
        if not location:
            return ""
        # Remove o texto "km de você" e limpa espaços
        location = location.split(",")[0] if "," in location else location
        return self.clean_text(location)

    def clean_salary(self, salary):
        """
        Formata o texto do salário para um formato mais legível
        """
        if not salary:
            return "Salário não informado"
        # Remove quebras de linha e espaços extras
        salary = self.clean_text(salary)
        # Substitui "a" por "até" para melhor legibilidade
        salary = salary.replace(" a ", " até ")
        return salary

    def parse_jobs(self, page, url):
        """
        Método para processar a página e extrair informações das vagas
        """
        try:
            vaga = {'url': url}  # Adiciona a URL como primeiro campo
            
            # Título da vaga
            try:
                titulo = page.locator('h2.js_vacancyHeaderTitle').first.text_content(timeout=5000).strip()
                if titulo:
                    self.logger.info(f"Título encontrado: {titulo}")
                    vaga['titulo'] = self.clean_text(titulo)
            except Exception as e:
                self.logger.error(f"Erro ao extrair título: {e}")
            
            # Empresa
            try:
                empresa = page.locator('div.h4 > a[target="_blank"]').first.text_content(timeout=5000).strip()
                if empresa:
                    self.logger.info(f"Empresa encontrada: {empresa}")
                    vaga['empresa'] = self.clean_text(empresa)
            except Exception as e:
                self.logger.error(f"Erro ao extrair empresa: {e}")
            
            # Localidade
            try:
                local = page.locator('.js_applyVacancyHidden .text-medium.mb-4:nth-of-type(1)').first.text_content(timeout=5000).strip()
                if local:
                    self.logger.info(f"Local encontrado: {local}")
                    vaga['local'] = self.clean_location(local)
            except Exception as e:
                self.logger.error(f"Erro ao extrair localidade: {e}")
            
            # Faixa Salarial
            try:
                salario = page.locator('.js_applyVacancyHidden .text-medium.mb-4:nth-of-type(2)').first.text_content(timeout=5000).strip()
                if salario:
                    self.logger.info(f"Salário encontrado: {salario}")
                    vaga['salario'] = self.clean_salary(salario)
            except Exception as e:
                self.logger.error(f"Erro ao extrair salário: {e}")
            
            # Descrição da Vaga
            try:
                descricao = page.locator('.js_vacancyDataPanels p.mb-16.text-break').first.text_content(timeout=5000).strip()
                if descricao:
                    self.logger.info(f"Descrição encontrada: {len(descricao)} caracteres")
                    vaga['descricao'] = self.clean_text(descricao)
            except Exception as e:
                self.logger.error(f"Erro ao extrair descrição: {e}")
            
            return vaga if vaga else None

        except Exception as e:
            self.logger.error(f"Erro ao processar vaga: {e}")
            return None
