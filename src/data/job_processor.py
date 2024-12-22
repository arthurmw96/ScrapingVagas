import pandas as pd
import logging
from datetime import datetime
from .supabase_client import SupabaseClient
from .job_categorizer import JobCategorizer

class JobProcessor:
    def __init__(self):
        self.setup_logging()
        self.db = SupabaseClient()
        self.categorizer = JobCategorizer()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def save_jobs(self, jobs):
        """
        Salva as vagas no banco de dados
        """
        if isinstance(jobs, dict):
            jobs = [jobs]
        
        saved_count = 0
        for job in jobs:
            # Adiciona categorias à vaga
            categories = self.categorizer.categorize_job(job)
            job['category'] = ','.join(categories)  # Converte lista em string

            # Adiciona hierarquia à vaga
            hierarchies = self.categorizer.classify_hierarchy(job)
            job['hierarchy'] = ','.join(hierarchies)  # Converte lista em string
            
            if self.db.insert_job(job):
                saved_count += 1
                self.logger.info(f"Vaga salva: {job.get('titulo', 'Sem título')} | Categorias: {job['category']} | Hierarquia: {job['hierarchy']}")
        
        self.logger.info(f"Salvas {saved_count} vagas no banco de dados")
        return saved_count

    def format_message(self, job):
        """
        Formata uma vaga para envio via WhatsApp
        Usa formatações do WhatsApp:
        * para negrito
        _ para itálico
        ~ para tachado
        ``` para monospace
        """
        # Trata valores None ou vazios
        company = job.get('company')
        company = "EMPRESA CONFIDENCIAL" if not company else company

        return f"""🔍 *NOVA VAGA*

📌 Cargo: *{job.get('title', 'Não informado')}*
🏢 Empresa: _{company}_
📍 Local: {job.get('location', 'Não informado')}
💰 Salário: *{job.get('salary', 'Não informado')}*

ℹ️ Link da vaga: {job.get('url', '')}
➖➖➖➖➖➖➖➖"""
