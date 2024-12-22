import os
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")
URLS_DIR = os.path.join(DATA_DIR, "urls")
JOBS_DIR = os.path.join(DATA_DIR, "jobs")

# Arquivos
URLS_FILE = os.path.join(URLS_DIR, "job_urls.csv")
PROCESSED_URLS_FILE = os.path.join(URLS_DIR, "processed_urls.csv")

# Configurações de scraping
RATE_LIMIT_DELAY = 1  # segundos entre requisições
MAX_RETRIES = 3

# Criar diretórios se não existirem
for directory in [DATA_DIR, URLS_DIR, JOBS_DIR]:
    os.makedirs(directory, exist_ok=True)
