import logging
import json
import os

class JobCategorizer:
    def __init__(self):
        # Configura o logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Carrega as categorias e hierarquias dos arquivos JSON
        self.categories = self._load_json_config('categories.json')
        self.hierarchies = self._load_json_config('hierarchies.json')
    
    def _load_json_config(self, filename):
        """
        Carrega um arquivo JSON de configuração
        """
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', filename)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Erro ao carregar {filename}: {str(e)}")
            return {}

    def _classify_text(self, text, classifications):
        """
        Método genérico para classificar texto baseado em um dicionário de classificações
        """
        text = text.lower()
        words = text.split()
        found = []
        
        for classification, keywords in classifications.items():
            for keyword in keywords:
                keyword_parts = keyword.split()
                if len(keyword_parts) > 1:
                    # Para palavras compostas, verifica se todas as palavras aparecem em sequência
                    for i in range(len(words) - len(keyword_parts) + 1):
                        if words[i:i + len(keyword_parts)] == keyword_parts:
                            found.append(classification)
                            self.logger.info(f"Classificação encontrada: {classification} (palavra-chave composta: {keyword})")
                            break
                else:
                    # Para palavras simples, procura a palavra exata
                    if keyword in words:
                        found.append(classification)
                        self.logger.info(f"Classificação encontrada: {classification} (palavra-chave: {keyword})")
                        break
        
        return found

    def categorize_job(self, job):
        """
        Categoriza uma vaga com base em suas informações
        """
        job_text = f"{job.get('titulo', '')} {job.get('descricao', '')}".lower()
        self.logger.info(f"Texto para categorização: {job_text[:200]}...")
        
        categories = self._classify_text(job_text, self.categories)
        
        if not categories:
            self.logger.info("Nenhuma categoria encontrada - marcando como 'outros'")
            categories = ['outros']
        
        self.logger.info(f"Categorias finais: {categories}")
        return categories

    def classify_hierarchy(self, job):
        """
        Classifica o nível hierárquico da vaga
        """
        job_text = f"{job.get('titulo', '')} {job.get('descricao', '')}".lower()
        self.logger.info(f"Texto para classificação hierárquica: {job_text[:200]}...")
        
        hierarchies = self._classify_text(job_text, self.hierarchies)
        
        if not hierarchies:
            self.logger.info("Nenhuma hierarquia encontrada - marcando como 'outros'")
            hierarchies = ['outros']
        
        self.logger.info(f"Hierarquias finais: {hierarchies}")
        return hierarchies

    def get_all_categories(self):
        """
        Retorna todas as categorias disponíveis
        """
        return list(self.categories.keys())

    def get_all_hierarchies(self):
        """
        Retorna todas as hierarquias disponíveis
        """
        return list(self.hierarchies.keys())

    def get_categories_stats(self):
        """
        Retorna um dicionário com o número de vagas em cada categoria
        """
        from src.data.supabase_client import SupabaseClient
        
        client = SupabaseClient()
        jobs = client.get_pending_jobs()
        
        stats = {category: 0 for category in self.categories.keys()}
        stats['outros'] = 0  # Adiciona categoria 'outros'
        
        for job in jobs:
            categories = self.categorize_job(job)
            for category in categories:
                stats[category] += 1
        
        return stats

    def get_hierarchy_stats(self):
        """
        Retorna um dicionário com o número de vagas em cada nível hierárquico
        """
        from src.data.supabase_client import SupabaseClient
        
        client = SupabaseClient()
        jobs = client.get_pending_jobs()
        
        stats = {hierarchy: 0 for hierarchy in self.hierarchies.keys()}
        stats['outros'] = 0
        
        for job in jobs:
            hierarchies = self.classify_hierarchy(job)
            for hierarchy in hierarchies:
                stats[hierarchy] += 1
        
        return stats
