import pandas as pd
import json
import os
import unicodedata

def normalize_key(text):
    """
    Remove acentos e caracteres especiais, converte para minúsculas
    e substitui espaços por underline
    """
    # Remove acentos
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Converte para minúsculas e substitui espaços por underline
    text = text.lower().replace(' ', '_')
    
    return text

# Define o caminho absoluto para o arquivo Excel
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
excel_file = os.path.join(base_dir, 'src', 'config', 'Cargos para webscrapping.xlsx')
output_file = os.path.join(base_dir, 'src', 'config', 'hierarchies.json')


# Lê o arquivo Excel
df = pd.read_excel(excel_file)


# Inicializa o dicionário que vai virar JSON
hierarchies = {}

# Itera sobre as linhas do DataFrame
for _, row in df.iterrows():
    cargo = str(row['Cargo']).lower().strip()
    nivel = str(row['Nível Hierárquico']).strip()
    
    # Pula linhas vazias
    if cargo == 'nan' or nivel == 'nan':
        continue
    
    # Normaliza a chave (nível) mas mantém o cargo original
    nivel_key = normalize_key(nivel)
    
    # Inicializa a lista se o nível não existir
    if nivel_key not in hierarchies:
        hierarchies[nivel_key] = []
    
    # Adiciona o cargo como palavra-chave
    if cargo not in hierarchies[nivel_key]:
        hierarchies[nivel_key].append(cargo)

# Salva o JSON
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(hierarchies, f, ensure_ascii=False, indent=4)

print(f"\nJSON gerado com sucesso em {output_file}")
print("\nConteúdo do JSON:")
print(json.dumps(hierarchies, ensure_ascii=False, indent=4))
