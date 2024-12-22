import os
import psycopg2
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

class SupabaseClient:
    def __init__(self):
        self.connection = psycopg2.connect(
            user=os.getenv("user"),
            password=os.getenv("password"),
            host=os.getenv("host"),
            port=os.getenv("port"),
            dbname=os.getenv("dbname")
        )
        self.cursor = self.connection.cursor()
        self._create_tables_if_not_exist()

    def _create_tables_if_not_exist(self):
        """
        Cria as tabelas necessárias se não existirem
        """
        try:
            # Tabela de URLs
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    location TEXT,
                    posted_date TIMESTAMP,
                    collected_at TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE
                )
            """)

            # Tabela de vagas
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    salary TEXT,
                    description TEXT,
                    category TEXT,
                    hierarchy TEXT,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (url) REFERENCES urls(url)
                )
            """)
            
            self.connection.commit()
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            self.connection.rollback()

    def insert_jobs(self, jobs_data: List[Dict]):
        """
        Insere dados de vagas no Supabase
        """
        try:
            for job in jobs_data:
                self.cursor.execute(
                    """
                    INSERT INTO urls (url, location, posted_date, collected_at, processed)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                    (job['url'], job['location'], job['date'], job['collected_at'], False)
                )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Erro ao inserir vagas: {e}")
            self.connection.rollback()
            return False

    def insert_job(self, job_data: Dict):
        """
        Insere dados de uma vaga específica
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO jobs (url, title, company, location, salary, description, category, hierarchy)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    salary = EXCLUDED.salary,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    hierarchy = EXCLUDED.hierarchy,
                    collected_at = CURRENT_TIMESTAMP
                """,
                (
                    job_data['url'],
                    job_data.get('titulo'),
                    job_data.get('empresa'),
                    job_data.get('local'),
                    job_data.get('salario'),
                    job_data.get('descricao'),
                    job_data.get('category'),
                    job_data.get('hierarchy')
                )
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Erro ao inserir vaga: {e}")
            self.connection.rollback()
            return False

    def get_pending_urls(self):
        """
        Retorna URLs que ainda não foram processadas
        """
        try:
            self.cursor.execute(
                """
                SELECT url 
                FROM urls
                WHERE processed = FALSE
                """
            )
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar URLs pendentes: {e}")
            return []

    def get_all_jobs(self):
        """
        Retorna todas as vagas processadas
        """
        try:
            self.cursor.execute(
                """
                SELECT 
                    j.url,
                    j.title,
                    j.company,
                    j.location,
                    j.salary,
                    j.description,
                    j.category,
                    j.hierarchy,
                    j.collected_at
                FROM jobs j
                """
            )
            columns = ['url', 'title', 'company', 'location', 'salary', 'description', 'category', 'hierarchy', 'collected_at']
            jobs = []
            for row in self.cursor.fetchall():
                job = dict(zip(columns, row))
                if job['category']:
                    job['category'] = job['category'].split(',')
                else:
                    job['category'] = []
                jobs.append(job)
            return jobs
        except Exception as e:
            print(f"Erro ao buscar vagas processadas: {e}")
            return []

    def get_unprocessed_urls(self):
        """
        Retorna URLs não processadas com informações adicionais
        """
        try:
            self.cursor.execute(
                """
                SELECT 
                    url,
                    location,
                    posted_date,
                    collected_at
                FROM urls
                WHERE processed = FALSE
                ORDER BY collected_at DESC
                """
            )
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Erro ao buscar URLs não processadas: {e}")
            return []

    def get_processed_jobs(self):
        """
        Retorna todas as vagas que foram processadas (processed = True)
        """
        try:
            self.cursor.execute(
                """
                SELECT 
                    j.url,
                    j.title,
                    j.company,
                    j.location,
                    j.salary,
                    j.description,
                    j.category,
                    j.hierarchy,
                    j.collected_at
                FROM jobs j
                INNER JOIN urls u ON j.url = u.url
                WHERE u.processed = TRUE
                ORDER BY j.collected_at DESC
                """
            )
            columns = ['url', 'title', 'company', 'location', 'salary', 'description', 'category', 'hierarchy', 'collected_at']
            jobs = []
            for row in self.cursor.fetchall():
                job = dict(zip(columns, row))
                if job['category']:
                    job['category'] = job['category'].split(',')
                else:
                    job['category'] = []
                jobs.append(job)
            return jobs
        except Exception as e:
            print(f"Erro ao buscar vagas processadas: {e}")
            return []

    def mark_as_processed(self, url: str):
        """
        Marca uma vaga como processada
        """
        try:
            self.cursor.execute(
                """
                UPDATE urls
                SET processed = TRUE
                WHERE url = %s
                """,
                (url,)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Erro ao marcar vaga como processada: {e}")
            self.connection.rollback()
            return False

    def get_processing_status(self):
        """
        Retorna o status atual do processamento
        """
        try:
            # Total de vagas
            self.cursor.execute("SELECT COUNT(*) FROM urls")
            total = self.cursor.fetchone()[0]

            # Vagas pendentes
            self.cursor.execute("SELECT COUNT(*) FROM urls WHERE processed = FALSE")
            pending = self.cursor.fetchone()[0]

            # Contagem por localização
            self.cursor.execute(
                """
                SELECT location, COUNT(*) 
                FROM urls 
                GROUP BY location
                """
            )
            locations = {row[0]: row[1] for row in self.cursor.fetchall()}

            return {
                'total': total,
                'pending': pending,
                'locations': locations
            }
        except Exception as e:
            print(f"Erro ao obter status: {e}")
            return {
                'total': 0,
                'pending': 0,
                'locations': {}
            }

    def clear_database(self):
        """
        Limpa todas as tabelas do banco de dados
        """
        try:
            # Primeiro limpa a tabela jobs devido à chave estrangeira
            self.cursor.execute("DELETE FROM jobs")
            # Depois limpa a tabela urls
            self.cursor.execute("DELETE FROM urls")
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Erro ao limpar banco de dados: {e}")
            self.connection.rollback()
            return False

    def __del__(self):
        """
        Fecha a conexão quando o objeto é destruído
        """
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
