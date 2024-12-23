# ZapVagas

Sistema de webscraping de vagas de emprego.

## Configuração do Ambiente

1. Crie um ambiente virtual Python:
```bash
python -m venv venv
```

2. Ative o ambiente virtual:
- Windows:
```bash
venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Estrutura do Projeto

- `src/`: Código fonte principal
  - `scraper/`: Módulos relacionados ao webscraping
  - `data/`: Módulos para processamento de dados
- `data/`: Arquivos de dados
- `config/`: Arquivos de configuração
- `tests/`: Testes unitários

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as variáveis de acesso ao banco de dados.
