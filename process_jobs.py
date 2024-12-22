from src.scraper.job_scraper import JobScraper
from src.data.job_processor import JobProcessor
from src.data.url_processor import URLProcessor
from src.data.job_categorizer import JobCategorizer
import logging
import time
from typing import Optional
import argparse

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def process_single_job(url: str, job_scraper: JobScraper) -> Optional[dict]:
    """
    Processa uma única vaga e retorna os dados coletados
    """
    try:
        logging.info(f"Processando vaga: {url}")
        job = job_scraper.fetch_jobs()
        
        if job:
            # Categorizar a vaga
            categorizer = JobCategorizer()
            categories = categorizer.categorize_job(job)
            job['category'] = ','.join(categories)  # Converte lista em string separada por vírgulas
            
            logging.info(f"Vaga processada com sucesso: {job.get('titulo', 'Sem título')}")
            logging.info(f"Categorias encontradas: {categories}")
            return job
            
        logging.warning(f"Nenhum dado encontrado para a vaga: {url}")
    except Exception as e:
        logging.error(f"Erro ao processar vaga {url}: {str(e)}")
    return None

def main():
    logger = setup_logging()
    logger.info("Iniciando processamento de vagas...")
    
    # Configurar argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Processar URLs de vagas coletadas')
    parser.add_argument('--delay', type=int, default=1, help='Delay entre requisições em segundos')
    parser.add_argument('--limit', type=int, help='Limite de vagas para processar', default=None)
    args = parser.parse_args()

    try:
        # Inicializar processors
        url_processor = URLProcessor()
        job_processor = JobProcessor()

        # Obter URLs pendentes
        pending_urls = url_processor.get_pending_urls()
        
        if not pending_urls:
            logger.info("Não há URLs pendentes para processar")
            return
        
        logger.info(f"Encontradas {len(pending_urls)} URLs para processar")
        
        # Limitar número de vagas se especificado
        if args.limit:
            pending_urls = pending_urls[:args.limit]

        # Processar cada URL
        for i, url in enumerate(pending_urls, 1):
            logger.info(f"Processando vaga {i}/{len(pending_urls)}: {url}")
            
            # Criar scraper para esta URL
            scraper = JobScraper(url)
            job = process_single_job(url, scraper)
            
            if job:
                # Salvar no banco
                job_processor.save_jobs([job])
                url_processor.mark_url_as_processed(url)
                logger.info(f"Vaga salva com sucesso: {job.get('titulo', 'Sem título')}")
            
            # Aguardar um pouco entre requisições
            time.sleep(args.delay)
        
        # Mostrar status final
        status = url_processor.get_processing_status()
        logger.info("\nStatus final do processamento:")
        logger.info(f"Total de URLs: {status['total']}")
        logger.info(f"URLs pendentes: {status['pending']}")
        logger.info("\nVagas por localização:")
        for location, count in status.get('locations', {}).items():
            logger.info(f"- {location}: {count}")

    except Exception as e:
        logger.error(f"Erro durante o processamento das vagas: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
