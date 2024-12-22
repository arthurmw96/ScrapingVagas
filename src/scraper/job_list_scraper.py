from .base_scraper import BaseScraper
from playwright.sync_api import sync_playwright
import time
from typing import List, Dict, Optional
from datetime import datetime

class JobListScraper(BaseScraper):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.selectors = {
            'card': "div.js_rowCard",
            'url': "div.js_vacancyLoad",
            'location': "div.small.text-medium",
            'date': "div.js_date"
        }

    def fetch_job_urls(self) -> List[Dict]:
        """
        Coleta todas as URLs de vagas e informações adicionais da página de listagem
        """
        self.logger.info(f"Iniciando coleta de dados de {self.base_url}")
        jobs_data = []

        with sync_playwright() as p:
            try:
                browser, context = self._create_browser_context(p)
                page = self._create_page(context)

                # Navega para a página
                page.goto(self.base_url, wait_until='networkidle')

                # Espera os cards de vagas carregarem
                page.wait_for_selector(self.selectors['card'])

                # Coleta todos os cards
                job_cards = page.query_selector_all(self.selectors['card'])
                
                for card in job_cards:
                    job_info = self._extract_job_info(card)
                    if job_info:
                        jobs_data.append(job_info)

                self.logger.info(f"Coletados dados de {len(jobs_data)} vagas")

            except Exception as e:
                self.logger.error(f"Erro durante a coleta de dados: {str(e)}")
            finally:
                context.close()
                browser.close()

        return jobs_data

    def _extract_job_info(self, card) -> Optional[Dict]:
        """
        Extrai todas as informações relevantes de um card de vaga
        """
        try:
            # Extrai URL
            url_element = card.query_selector(self.selectors['url'])
            if not url_element:
                return None
            url = url_element.get_attribute('data-href')
            # Adiciona o prefixo da URL base do InfoJobs
            url = f"https://www.infojobs.com.br{url}"
            
            # Extrai localização
            location_element = card.query_selector(self.selectors['location'])
            location = location_element.text_content().strip() if location_element else "Não especificado"
            # Limpa a localização removendo a parte ", X Km de você"
            if ',' in location:
                location = location.split(',')[0].strip()
            
            # Extrai data
            date_element = card.query_selector(self.selectors['date'])
            date_str = date_element.get_attribute('data-value') if date_element else None
            
            # Formata a data
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y/%m/%d %H:%M:%S')
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    formatted_date = date_str
            else:
                formatted_date = None

            return {
                'url': url,
                'location': location,
                'date': formatted_date,
                'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            self.logger.error(f"Erro ao extrair informações do card: {str(e)}")
            return None

    def fetch_paginated_job_urls(self, max_pages: int = None) -> List[Dict]:
        """
        Coleta informações de vagas de múltiplas páginas
        """
        all_jobs_data = []
        page_num = 1

        with sync_playwright() as p:
            try:
                browser, context = self._create_browser_context(p)
                page = self._create_page(context)

                while True:
                    if max_pages and page_num > max_pages:
                        break

                    page_url = f"{self.base_url}?page={page_num}"
                    self.logger.info(f"Processando página {page_num}: {page_url}")

                    # Navega para a página
                    page.goto(page_url, wait_until='networkidle')

                    try:
                        # Espera os cards de vagas carregarem
                        page.wait_for_selector(self.selectors['card'])
                    except TimeoutError:
                        self.logger.info("Não foram encontrados mais cards de vagas. Finalizando.")
                        break

                    # Coleta dados da página atual
                    job_cards = page.query_selector_all(self.selectors['card'])
                    if not job_cards:
                        break

                    for card in job_cards:
                        job_info = self._extract_job_info(card)
                        if job_info:
                            all_jobs_data.append(job_info)

                    page_num += 1
                    time.sleep(1)  # Rate limiting

            except Exception as e:
                self.logger.error(f"Erro durante a coleta de dados paginados: {str(e)}")
            finally:
                context.close()
                browser.close()

        self.logger.info(f"Total de vagas coletadas: {len(all_jobs_data)}")
        return all_jobs_data

    def fetch_jobs_with_scroll(self, target_jobs: int) -> List[Dict]:
        """
        Coleta vagas usando scroll infinito até atingir o número desejado de vagas únicas
        """
        self.logger.info(f"Iniciando coleta de {target_jobs} vagas de {self.base_url}")
        jobs_data = []
        processed_urls = set()  # Conjunto para rastrear URLs já processadas
        scroll_attempts = 0
        max_scroll_attempts = 10  # Número máximo de tentativas de scroll sem novos resultados

        with sync_playwright() as p:
            try:
                browser, context = self._create_browser_context(p)
                page = self._create_page(context)

                # Navega para a página
                self.logger.info("Navegando para a página inicial...")
                page.goto(self.base_url, wait_until='networkidle')

                # Espera os cards de vagas carregarem inicialmente
                self.logger.info("Aguardando cards iniciais carregarem...")
                page.wait_for_selector(self.selectors['card'])

                while len(jobs_data) < target_jobs and scroll_attempts < max_scroll_attempts:
                    # Coleta os cards visíveis atualmente
                    job_cards = page.query_selector_all(self.selectors['card'])
                    self.logger.info(f"Encontrados {len(job_cards)} cards na página")
                    
                    # Processa cada card
                    for card in job_cards:
                        job_info = self._extract_job_info(card)
                        if job_info and job_info['url'] not in processed_urls:
                            jobs_data.append(job_info)
                            processed_urls.add(job_info['url'])
                            self.logger.info(f"Coletada vaga {len(jobs_data)}/{target_jobs}: {job_info['url']}")
                            
                            if len(jobs_data) >= target_jobs:
                                break

                    # Se ainda não atingiu o número desejado, faz scroll e espera carregar mais
                    if len(jobs_data) < target_jobs:
                        # Scroll até o último card visível
                        last_card = job_cards[-1]
                        self.logger.info("Fazendo scroll até o último card...")
                        last_card.scroll_into_view_if_needed()
                        
                        # Espera um pouco para o conteúdo carregar
                        page.wait_for_timeout(2000)  # Aumentado para 2 segundos
                        
                        # Espera novos cards aparecerem
                        try:
                            # Conta cards antes do scroll
                            cards_before = len(page.query_selector_all(self.selectors['card']))
                            self.logger.info(f"Cards antes do scroll: {cards_before}")
                            
                            # Espera por 10 segundos por novos cards
                            for attempt in range(10):
                                page.wait_for_timeout(1000)
                                cards_after = len(page.query_selector_all(self.selectors['card']))
                                self.logger.info(f"Cards após {attempt+1}s: {cards_after}")
                                if cards_after > cards_before:
                                    scroll_attempts = 0  # Reset contador se encontrou novos cards
                                    break
                            
                            # Se não apareceram novos cards, incrementa contador de tentativas
                            if cards_after <= cards_before:
                                scroll_attempts += 1
                                self.logger.warning(f"Nenhum novo card encontrado. Tentativa {scroll_attempts}/{max_scroll_attempts}")
                                
                        except Exception as e:
                            self.logger.error(f"Erro ao esperar por novos cards: {str(e)}")
                            scroll_attempts += 1

                if scroll_attempts >= max_scroll_attempts:
                    self.logger.warning(f"Número máximo de tentativas de scroll atingido. Parando coleta.")
                
                self.logger.info(f"Coleta finalizada. Total de vagas coletadas: {len(jobs_data)}")

            except Exception as e:
                self.logger.error(f"Erro durante a coleta de dados: {str(e)}")
            finally:
                context.close()
                browser.close()

        return jobs_data

    def fetch_jobs_until_date(self, target_date) -> List[Dict]:
        """
        Coleta vagas até atingir uma data específica
        """
        self.logger.info(f"Iniciando coleta de vagas até {target_date.strftime('%d/%m/%Y')}")
        jobs_data = []
        reached_target_date = False
        current_page = 1
        MAX_PAGES = 500  # Limite de segurança

        with sync_playwright() as p:
            try:
                browser, context = self._create_browser_context(p)
                page = self._create_page(context)

                while not reached_target_date and current_page <= MAX_PAGES:
                    # Constrói a URL da página atual
                    url = self.base_url
                    if current_page > 1:
                        url = f"{self.base_url}&page={current_page}"

                    # Navega para a página
                    self.logger.info(f"Navegando para página {current_page}")
                    page.goto(url, wait_until='networkidle')

                    # Espera os cards de vagas carregarem
                    page.wait_for_selector(self.selectors['card'])

                    # Coleta todos os cards
                    job_cards = page.query_selector_all(self.selectors['card'])
                    
                    if not job_cards:
                        self.logger.info("Nenhuma vaga encontrada na página. Finalizando coleta.")
                        break

                    # Processa cada card
                    for card in job_cards:
                        job_info = self._extract_job_info(card)
                        if job_info:
                            # Verifica a data da vaga
                            if job_info['date']:
                                job_date = datetime.strptime(job_info['date'].split()[0], '%Y-%m-%d').date()
                                if job_date < target_date:
                                    self.logger.info(f"Atingida data alvo ({job_date}). Finalizando coleta.")
                                    reached_target_date = True
                                    break
                            jobs_data.append(job_info)

                    if reached_target_date:
                        break

                    current_page += 1
                    time.sleep(1)  # Pequena pausa entre páginas

                self.logger.info(f"Coletados dados de {len(jobs_data)} vagas")

            except Exception as e:
                self.logger.error(f"Erro durante a coleta de dados: {str(e)}")
            finally:
                context.close()
                browser.close()

        return jobs_data
