import streamlit as st
import json
import os
from typing import Dict, List
import unicodedata

def normalize_key(text: str) -> str:
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

def load_json_config(filename: str) -> Dict[str, List[str]]:
    """Carrega um arquivo JSON de configuração"""
    config_path = os.path.join('src', 'config', filename)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar {filename}: {str(e)}")
        return {}

def save_json_config(data: Dict[str, List[str]], filename: str):
    """Salva um dicionário em um arquivo JSON"""
    config_path = os.path.join('src', 'config', filename)
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        st.success(f"Arquivo {filename} salvo com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar {filename}: {str(e)}")

def edit_category_section(title: str, json_file: str):
    """Cria uma seção para editar categorias/hierarquias"""
    st.header(title)
    
    # Carrega os dados
    data = load_json_config(json_file)
    
    # Adicionar nova categoria
    with st.expander("Adicionar Nova Categoria", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_category = st.text_input("Nome da Categoria", key=f"new_cat_{json_file}")
        with col2:
            if st.button("Adicionar", key=f"add_cat_{json_file}"):
                if new_category:
                    normalized_key = normalize_key(new_category)
                    if normalized_key not in data:
                        data[normalized_key] = []
                        save_json_config(data, json_file)
                    else:
                        st.warning("Categoria já existe!")
    
    # Editar categorias existentes
    for category in sorted(data.keys()):
        with st.expander(f"📁 {category}", expanded=False):
            # Remover categoria
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑️ Remover Categoria", key=f"del_{category}_{json_file}"):
                    del data[category]
                    save_json_config(data, json_file)
                    st.rerun()
            
            # Adicionar palavra-chave
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_keyword = st.text_input("Nova palavra-chave", key=f"new_key_{category}")
                with col2:
                    if st.button("Adicionar", key=f"add_{category}"):
                        if new_keyword and new_keyword.lower() not in [k.lower() for k in data[category]]:
                            data[category].append(new_keyword.lower())
                            save_json_config(data, json_file)
                            st.rerun()
            
            # Lista de palavras-chave
            keywords = data[category]
            for i, keyword in enumerate(keywords):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(keyword)
                with col2:
                    if st.button("🗑️", key=f"del_{category}_{i}"):
                        keywords.pop(i)
                        save_json_config(data, json_file)
                        st.rerun()

st.set_page_config(
    page_title="Gerenciar categorização",
    page_icon="📝",
    layout="wide"
)

st.title("Gerenciar Categorias e Hierarquias")

tab1, tab2 = st.tabs(["Hierarquias", "Categorias"])

with tab1:
    edit_category_section("Níveis Hierárquicos", "hierarchies.json")

with tab2:
    edit_category_section("Categorias de Vagas", "categories.json")
