from src.scraper.job_list_scraper import JobListScraper
from src.data.url_processor import URLProcessor
import argparse
import logging
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()
    
    # Configurar argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Coletar URLs de vagas de emprego')
    parser.add_argument('base_url', help='URL base para coleta de vagas')
    parser.add_argument('--target-date', help='Data limite para coleta (YYYY-MM-DD)', required=True)
    args = parser.parse_args()

    # Converter a data alvo para objeto datetime
    target_date = datetime.strptime(args.target_date, "%Y-%m-%d").date()
    
    # Inicializar scraper e processor
    scraper = JobListScraper(args.base_url)
    processor = URLProcessor()

    logger.info(f"Coletando vagas até a data {target_date.strftime('%d/%m/%Y')}")
    
    # Coleta vagas até atingir a data alvo
    jobs_data = scraper.fetch_jobs_until_date(target_date)
    
    if jobs_data:
        # Salvar dados
        processor.save_urls(jobs_data)
        
        # Mostrar status
        status = processor.get_processing_status()
        logger.info("\nStatus da coleta:")
        logger.info(f"Total de vagas: {status['total']}")
        logger.info(f"Vagas pendentes: {status['pending']}")
        logger.info("\nVagas por localização:")
        for location, count in status.get('locations', {}).items():
            logger.info(f"- {location}: {count}")
    else:
        logger.warning("Nenhuma vaga encontrada")

if __name__ == "__main__":
    main()
