import streamlit as st
from src.data.job_processor import JobProcessor
from src.data.url_processor import URLProcessor
from src.scraper.job_list_scraper import JobListScraper
from src.scraper.job_scraper import JobScraper
from src.data.supabase_client import SupabaseClient
from dotenv import load_dotenv
import subprocess
import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Instala o Playwright e seus navegadores se estiver no Streamlit Cloud
if not os.path.exists("venv"):  # Estamos no Streamlit Cloud
    try:
        st.info("Instalando Playwright e suas dependências...")
        # Instala o browser e suas dependências
        os.system("playwright install-deps")
        os.system("playwright install chromium")
        st.success("Playwright instalado com sucesso!")
    except Exception as e:
        st.error("Erro ao instalar dependências do Playwright")
        st.code(str(e))
        st.stop()

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="ZipVagas",
    page_icon="💼",
    layout="wide"
)

# Detecta se estamos rodando localmente ou no Streamlit Cloud
IS_LOCAL = os.path.exists("venv")
if IS_LOCAL:
    PYTHON_CMD = os.path.join("venv", "Scripts", "python.exe")
    PIP_CMD = os.path.join("venv", "Scripts", "pip.exe")
else:
    PYTHON_CMD = sys.executable
    PIP_CMD = [sys.executable, "-m", "pip"]

# Título principal
st.title("ZipVagas 💼")
st.subheader("Gerenciador de Coleta de Vagas")

# Sidebar para configurações
with st.sidebar:
    st.header("Configurações")
    
    # Botão para limpar banco de dados
    if 'show_confirmation' not in st.session_state:
        st.session_state.show_confirmation = False
    if 'db_cleared' not in st.session_state:
        st.session_state.db_cleared = False

    if not st.session_state.db_cleared:
        if st.button("🗑️ Limpar Banco de Dados", key="btn_clear_db"):
            st.session_state.show_confirmation = True

        if st.session_state.show_confirmation:
            st.warning("⚠️ Tem certeza? Isso irá remover todas as vagas!", icon="⚠️")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✓ Sim, limpar tudo", key="btn_confirm_clear"):
                    client = SupabaseClient()
                    success = client.clear_database()
                    if success:
                        st.session_state.db_cleared = True
                        st.session_state.show_confirmation = False
                    else:
                        st.error("Erro ao limpar o banco de dados")
            with col2:
                if st.button("❌ Não, cancelar", key="btn_cancel_clear"):
                    st.session_state.show_confirmation = False
                    st.info("Operação cancelada")
    
    if st.session_state.db_cleared:
        st.success("Banco de dados limpo com sucesso!")
        # Reset o estado após mostrar a mensagem
        st.session_state.db_cleared = False
    
    base_url = st.text_input(
        "URL Base:", 
        value="https://www.infojobs.com.br/empregos-em-rio-janeiro,-rj.aspx?campo=griddate&orden=desc",
        help="URL base para coleta de vagas"
    )
    
    # Seletor de data
    min_date = datetime.now() - timedelta(days=30)  # Limita a 30 dias atrás
    max_date = datetime.now()
    default_date = (datetime.now() - timedelta(days=1)).date()  # Data de ontem
    
    selected_date = st.date_input(
        "Coletar vagas até a data:",
        value=default_date,
        min_value=min_date.date(),
        max_value=max_date.date(),
        help="O sistema coletará vagas de hoje até esta data"
    )

# Área principal dividida em três seções
tab1, tab2, tab3 = st.tabs(["Coleta de URLs", "Processamento de Vagas", "Gerar Mensagens"])

# Tab 1: Coleta de URLs
with tab1:
    st.markdown("### Coleta de URLs")
    if st.button("Iniciar Coleta de URLs"):
        with st.spinner("Coletando URLs..."):
            try:
                st.info(f"Executando coleta de URLs até {selected_date.strftime('%d/%m/%Y')}...")
                
                process = subprocess.run(
                    [PYTHON_CMD, "collect_urls.py", base_url, "--target-date", selected_date.strftime("%Y-%m-%d")],
                    capture_output=True,
                    text=True
                )
                
                if process.returncode == 0:
                    st.success(f"Coleta finalizada com sucesso!")
                    if process.stdout:
                        st.code(process.stdout)
                else:
                    st.error("Erro durante a coleta de URLs")
                    st.code(process.stderr)
            except Exception as e:
                st.error(f"Erro: {str(e)}")

# Tab 2: Processamento de Vagas
with tab2:
    def process_jobs_tab():
        st.header("Processamento de Vagas")
        
        # Buscar vagas não processadas
        client = SupabaseClient()
        unprocessed_urls = client.get_unprocessed_urls()
        
        if unprocessed_urls:
            # Converter para DataFrame
            df = pd.DataFrame(unprocessed_urls, columns=['URL', 'Localização', 'Data Postagem', 'Data Coleta'])
            total_vagas = len(df)
            
            # Mostrar total de vagas
            st.info(f"Total de vagas para processar: {total_vagas}")
            
            # Exibir amostra
            st.markdown("### Amostra de Vagas Pendentes (5 primeiras)")
            st.dataframe(
                df.head(5),
                hide_index=True,
                use_container_width=True
            )
            
            if total_vagas > 5:
                st.caption(f"* Mostrando apenas 5 vagas de um total de {total_vagas}")
        else:
            st.info("Não há vagas pendentes para processamento.")
        
        # Botão para processar vagas
        if st.button("Processar Vagas Pendentes"):
            with st.spinner("Processando vagas..."):
                try:
                    venv_python = os.path.join("venv", "Scripts", "python.exe") if IS_LOCAL else sys.executable
                    
                    # Mostra o comando que será executado
                    cmd = [venv_python, "process_jobs.py"]
                    
                    process = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=os.getcwd()  # Garante que está executando no diretório correto
                    )
                    
                    if process.returncode == 0:
                        st.success("Processamento finalizado com sucesso!")
                        
                        # Obtém estatísticas atualizadas
                        client = SupabaseClient()
                        jobs = client.get_all_jobs()
                        
                        if jobs:
                            # Inicializa contadores
                            category_counts = {}
                            hierarchy_counts = {}
                            
                            # Conta vagas por categoria e hierarquia
                            for job in jobs:
                                # Processa categorias
                                category = job.get('category', '')
                                if isinstance(category, str) and category:
                                    categories = [cat.strip() for cat in category.split(',')]
                                    for cat in categories:
                                        category_counts[cat] = category_counts.get(cat, 0) + 1
                                elif isinstance(category, list):
                                    for cat in category:
                                        category_counts[cat] = category_counts.get(cat, 0) + 1
                                
                                # Processa hierarquias
                                hierarchy = job.get('hierarchy', '')
                                if isinstance(hierarchy, str) and hierarchy:
                                    hierarchies = [h.strip() for h in hierarchy.split(',')]
                                    for h in hierarchies:
                                        hierarchy_counts[h] = hierarchy_counts.get(h, 0) + 1
                                elif isinstance(hierarchy, list):
                                    for h in hierarchy:
                                        hierarchy_counts[h] = hierarchy_counts.get(h, 0) + 1
                            
                            # Nomes amigáveis para as categorias
                            category_names = {
                                'administrativa': 'Vagas adm.',
                                'comercial': 'Vagas com.',
                                'construcao': 'Vagas cons.',
                                'educacao': 'Vagas educ.',
                                'financeira': 'Vagas fina.',
                                'juridica': 'Vagas juríd.',
                                'logistica': 'Vagas logís.',
                                'marketing': 'Vagas mar.',
                                'operacional': 'Vagas oper.',
                                'rh': 'Vagas rh',
                                'saude': 'Vagas saude',
                                'tecnologia': 'Vagas tecn.',
                                'turismo': 'Vagas turís.',
                                'estagio': 'Estágio',
                                'outros': 'Outros'
                            }

                            # Cria gráfico de barras para categorias
                            st.header("Estatísticas por Categoria")
                            
                            # Prepara dados para o gráfico
                            categories = []
                            counts = []
                            for category, count in category_counts.items():
                                categories.append(category_names.get(category, category))
                                counts.append(count)
                            
                            # Cria o gráfico de barras
                            fig_categories = go.Figure(data=[
                                go.Bar(
                                    x=categories,
                                    y=counts,
                                    text=counts,  # Mostra os valores sobre as barras
                                    textposition='auto',
                                    marker_color='#1f77b4'  # Cor azul padrão
                                )
                            ])
                            
                            # Personaliza o layout
                            fig_categories.update_layout(
                                title="Distribuição de Vagas por Categoria",
                                xaxis_title="Categorias",
                                yaxis_title="Número de Vagas",
                                showlegend=False,
                                height=400,
                                margin=dict(t=30, b=0, l=0, r=0)
                            )
                            
                            # Rotaciona os rótulos do eixo x para melhor legibilidade
                            fig_categories.update_xaxes(tickangle=45)
                            
                            # Mostra o gráfico
                            st.plotly_chart(fig_categories, use_container_width=True)
                            
                            # Nomes amigáveis para as hierarquias
                            hierarchy_names = {
                                'alta_direcao': 'Alta Direção',
                                'gerencia': 'Gerência',
                                'supervisao_e_coordenacao': 'Supervisão',
                                'operacional_escritorio': 'Operacional',
                                'operacional_industria_e_logistica': 'Ind/Log',
                                'estagio_e_aprendizado': 'Estágio',
                                'outros': 'Outros'
                            }
                            
                            # Cria gráfico de barras para hierarquias
                            st.header("Estatísticas por Hierarquia")
                            
                            # Prepara dados para o gráfico
                            hierarchies = []
                            counts = []
                            for hierarchy, count in hierarchy_counts.items():
                                hierarchies.append(hierarchy_names.get(hierarchy, hierarchy))
                                counts.append(count)
                            
                            # Cria o gráfico de barras
                            fig_hierarchies = go.Figure(data=[
                                go.Bar(
                                    x=hierarchies,
                                    y=counts,
                                    text=counts,  # Mostra os valores sobre as barras
                                    textposition='auto',
                                    marker_color='#2ca02c'  # Cor verde
                                )
                            ])
                            
                            # Personaliza o layout
                            fig_hierarchies.update_layout(
                                title="Distribuição de Vagas por Hierarquia",
                                xaxis_title="Níveis Hierárquicos",
                                yaxis_title="Número de Vagas",
                                showlegend=False,
                                height=400,
                                margin=dict(t=30, b=0, l=0, r=0)
                            )
                            
                            # Rotaciona os rótulos do eixo x para melhor legibilidade
                            fig_hierarchies.update_xaxes(tickangle=45)
                            
                            # Mostra o gráfico
                            st.plotly_chart(fig_hierarchies, use_container_width=True)
                    else:
                        st.error("Erro durante o processamento das vagas")
                        st.code(process.stderr)
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
    
    process_jobs_tab()

# Tab 3: Geração de Mensagens
with tab3:
    st.markdown("### Geração de Mensagens por Data de Publicação")
    
    job_processor = JobProcessor()
    client = SupabaseClient()
    
    # Obtém todas as vagas processadas
    processed_jobs = client.get_processed_jobs()
    
    if not processed_jobs:
        st.warning("Nenhuma vaga processada encontrada. Por favor, processe algumas vagas primeiro.")
    else:
        # Obtém todas as datas de publicação disponíveis
        dates = set()
        for job in processed_jobs:
            posted_date = job.get('posted_date')
            if posted_date:
                # Converte para data
                date = posted_date.date()
                dates.add(date)
        
        if not dates:
            st.warning("Nenhuma data de publicação encontrada nas vagas.")
        else:
            # Ordena as datas em ordem decrescente
            sorted_dates = sorted(dates, reverse=True)
            
            # Seletor de data
            selected_date = st.date_input(
                "Selecione a data de publicação:",
                value=sorted_dates[0],  # Data mais recente como padrão
                min_value=min(dates),
                max_value=max(dates)
            )

            # Filtra vagas pela data selecionada
            date_jobs = []
            for job in processed_jobs:
                posted_date = job.get('posted_date')
                if posted_date and posted_date.date() == selected_date:
                    date_jobs.append(job)

            if not date_jobs:
                st.warning(f"Nenhuma vaga encontrada publicada em {selected_date}")
            else:
                st.info(f"Encontradas {len(date_jobs)} vagas publicadas em {selected_date}")

                # Obtém lista de hierarquias com vagas
                hierarchies_with_jobs = set()
                for job in date_jobs:
                    hierarchy = job.get('hierarchy', '')
                    if isinstance(hierarchy, str) and hierarchy:
                        hierarchies = [h.strip() for h in hierarchy.split(',')]
                        hierarchies_with_jobs.update(hierarchies)
                    elif isinstance(hierarchy, list):
                        hierarchies_with_jobs.update(hierarchy)

                # Obtém lista de categorias com vagas
                categories_with_jobs = set()
                for job in date_jobs:
                    category = job.get('category', '')
                    if isinstance(category, str) and category:
                        categories = [cat.strip() for cat in category.split(',')]
                        categories_with_jobs.update(categories)
                    elif isinstance(category, list):
                        categories_with_jobs.update(category)

                # Seletores de hierarquia e categoria
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Hierarquia")
                    all_hierarchies = st.checkbox("Todas as hierarquias")
                    if not all_hierarchies and hierarchies_with_jobs:
                        selected_hierarchy = st.selectbox(
                            "Selecione a hierarquia:",
                            sorted(list(hierarchies_with_jobs))
                        )
                
                with col2:
                    st.markdown("#### Categoria")
                    all_categories = st.checkbox("Todas as categorias")
                    if not all_categories and categories_with_jobs:
                        selected_category = st.selectbox(
                            "Selecione a categoria:",
                            sorted(list(categories_with_jobs))
                        )

                if st.button("Gerar Mensagem"):
                    with st.spinner("Gerando mensagem..."):
                        try:
                            # Filtra vagas pela hierarquia e categoria selecionadas
                            filtered_jobs = []
                            for job in date_jobs:
                                include_job = True
                                
                                # Verifica hierarquia
                                if not all_hierarchies:
                                    hierarchy = job.get('hierarchy', '')
                                    if isinstance(hierarchy, str):
                                        hierarchies = [h.strip() for h in hierarchy.split(',')]
                                    elif isinstance(hierarchy, list):
                                        hierarchies = hierarchy
                                    else:
                                        hierarchies = []
                                    
                                    if selected_hierarchy not in hierarchies:
                                        include_job = False
                                
                                # Verifica categoria
                                if include_job and not all_categories:
                                    category = job.get('category', '')
                                    if isinstance(category, str):
                                        categories = [cat.strip() for cat in category.split(',')]
                                    elif isinstance(category, list):
                                        categories = category
                                    else:
                                        categories = []
                                    
                                    if selected_category not in categories:
                                        include_job = False
                                
                                if include_job:
                                    filtered_jobs.append(job)
                            
                            if filtered_jobs:
                                # Ordena as vagas por data de coleta (mais recentes primeiro)
                                filtered_jobs.sort(key=lambda x: x.get('collected_at', ''), reverse=True)
                                
                                # Gera mensagem para cada vaga
                                messages = []
                                for job in filtered_jobs:
                                    message = job_processor.format_message(job)
                                    messages.append(message)
                                
                                # Combina todas as mensagens
                                final_message = "\n\n".join(messages)
                                
                                # Mostra a mensagem em uma área de código
                                st.code(final_message, language="text")
                                st.caption("ℹ️ Para copiar a mensagem, clique no botão que aparece no canto superior direito do bloco de código ao passar o mouse.")
                        except Exception as e:
                            st.error(f"Erro ao gerar mensagem: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Desenvolvido usando Streamlit")


#vagas sao paulo:       https://www.infojobs.com.br/empregos-em-sao-paulo,-sp.aspx?campo=griddate&orden=desc
#vagas rio de janeiro:  https://www.infojobs.com.br/empregos-em-rio-janeiro,-rj.aspx?campo=griddate&orden=desc
#vagas belo horizonte:  https://www.infojobs.com.br/empregos-em-belo-horizonte,-mg.aspx?campo=griddate&orden=desc
#vagas salvador:        https://www.infojobs.com.br/empregos-em-salvador,-ba.aspx?campo=griddate&orden=desc