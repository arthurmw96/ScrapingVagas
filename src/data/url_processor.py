import logging
from typing import List, Dict
from .supabase_client import SupabaseClient

class URLProcessor:
    def __init__(self):
        self.db = SupabaseClient()
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def save_urls(self, jobs_data: List[Dict]) -> None:
        """
        Salva os dados das vagas no Supabase
        """
        try:
            self.db.insert_jobs(jobs_data)
            self.logger.info(f"Salvos dados de {len(jobs_data)} vagas no Supabase")
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados das vagas: {str(e)}")

    def get_pending_urls(self) -> List[str]:
        """
        Retorna URLs que ainda não foram processadas
        """
        try:
            pending_urls = self.db.get_pending_urls()
            self.logger.info(f"Encontradas {len(pending_urls)} URLs pendentes")
            return pending_urls
        except Exception as e:
            self.logger.error(f"Erro ao buscar URLs pendentes: {str(e)}")
            return []

    def mark_url_as_processed(self, url: str) -> None:
        """
        Marca uma URL como processada
        """
        try:
            self.db.mark_as_processed(url)
            self.logger.info(f"URL marcada como processada: {url}")
        except Exception as e:
            self.logger.error(f"Erro ao marcar URL como processada: {str(e)}")

    def get_processing_status(self) -> Dict:
        """
        Retorna o status atual do processamento
        """
        try:
            return self.db.get_processing_status()
        except Exception as e:
            self.logger.error(f"Erro ao obter status do processamento: {str(e)}")
            return {'total': 0, 'pending': 0, 'locations': {}}
