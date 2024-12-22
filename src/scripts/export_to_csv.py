import os
from src.data.supabase_client import SupabaseClient
import csv
from datetime import datetime

def export_jobs_to_csv():
    # Inicializa o cliente do Supabase
    client = SupabaseClient()
    
    try:
        # Query para buscar todos os jobs
        client.cursor.execute("""
            SELECT id, url, title, company, location, salary, 
                   description, collected_at, category
            FROM jobs
            ORDER BY collected_at DESC
        """)
        
        # Busca todos os resultados
        rows = client.cursor.fetchall()
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'jobs_export_{timestamp}.csv'
        
        # Cria o arquivo CSV
        with open(filename, 'w', newline='', encoding='latin1') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            
            # Escreve o cabeçalho
            writer.writerow(['ID', 'URL', 'Título', 'Empresa', 'Localização', 
                           'Salário', 'Descrição', 'Data Coleta', 'Categoria'])
            
            # Escreve os dados
            for row in rows:
                # Trata possíveis erros de encoding
                processed_row = []
                for item in row:
                    if isinstance(item, str):
                        # Substitui caracteres que possam causar problemas no encoding latin1
                        processed_item = item.encode('latin1', errors='replace').decode('latin1')
                    else:
                        processed_item = item
                    processed_row.append(processed_item)
                writer.writerow(processed_row)
                
        print(f'Arquivo CSV gerado com sucesso: {filename}')
        print(f'Total de registros exportados: {len(rows)}')
        
    except Exception as e:
        print(f'Erro ao exportar dados: {str(e)}')
    
    finally:
        client.cursor.close()
        client.connection.close()

if __name__ == '__main__':
    export_jobs_to_csv()
