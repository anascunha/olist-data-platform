# Fase 1 — Infraestrutura e Configuração do Ambiente

Este documento guia a configuração completa da infraestrutura necessária para rodar a plataforma, utilizando o **Databricks File System (DBFS)** como Data Lake, adotando a estratégia Zero-Budget.

---

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

| Ferramenta | Versão | Link |
|---|---|---|
| Python | 3.9+ | https://www.python.org/downloads/ |
| Databricks CLI | 0.200+ | https://github.com/databricks/cli |
| Git | qualquer | https://git-scm.com |

---

## 1. Clonar o repositório

```bash
git clone https://github.com/<seu-usuario>/olist-data-platform.git
cd olist-data-platform
```

---

## 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha as credenciais nas próximas etapas:

```bash
cp .env.example .env
```

O arquivo `.env` **nunca deve ser commitado**. Ele já está no `.gitignore`.

---

## 3. Credenciais do Kaggle

O dataset da Olist vem da plataforma Kaggle. É necessário gerar um token de API:

1. Acesse [kaggle.com](https://www.kaggle.com) e faça login
2. Vá em **Settings → API → Create New Token**
3. Preencha no `.env`:
   ```bash
   KAGGLE_USERNAME=seu_usuario
   KAGGLE_KEY=sua_chave
   ```

---

## 4. Configurar o Databricks Workspace (Processamento & Data Lake)

Nesta arquitetura, utilizamos o **Databricks** tanto para o processamento (Apache Spark) quanto para o armazenamento (DBFS) das camadas Bronze, Silver e Gold.

### 4.1. Gerar token de acesso

1. No seu workspace Databricks, clique no seu nome (canto superior direito) → **User Settings → Developer**.
2. Vá em **Access Tokens → Manage → Generate New Token**.
3. Copie o token gerado.

### 4.2. Obter o HTTP Path do cluster

1. No menu lateral, vá em **Compute → seu cluster → Configuration → Advanced Options → JDBC/ODBC**.
2. Copie o valor de **HTTP Path** (formato: `/sql/1.0/warehouses/...`).

### 4.3. Preencher o `.env`

```bash
DATABRICKS_HOST=https://<seu-workspace>.cloud.databricks.com
DATABRICKS_TOKEN=<token gerado>
DATABRICKS_HTTP_PATH=<http path do cluster>
```

---

## 5. Configurar a CLI do Databricks e Ambiente Virtual

### 5.1. Ambiente Virtual Python

Crie e ative uma virtual environment, em seguida instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5.2. Instalar a Databricks CLI

Instale a versão mais recente da CLI para gerenciar os **Asset Bundles**:

```bash
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/setup.sh | sh
```

Autentique utilizando suas credenciais recém configuradas:

```bash
databricks configure
```

---

## 6. Estrutura provisionada

Ao final desta fase, a seguinte arquitetura estará configurada:

```text
Databricks (Workspace Cloud)
└── DBFS (Databricks File System)
    ├── /olist/bronze/   ← dados brutos (Parquet/Delta/CSV)
    ├── /olist/silver/   ← dados limpos e padronizados
    └── /olist/gold/     ← dados modelados para analytics e IA

Local
└── Ambientes
    ├── .venv (Python 3)
    ├── dbt-databricks (Transformações)
    └── ML Ops Validation Layer (Camada de governança e validação de código IA)
```

---

## Próxima fase

Com a infraestrutura e credenciais prontas, o próximo passo é configurar o script de download automatizado:
→ [Fase 2 — Pipeline de Ingestão](./phase-02-ingestion.md) *(em breve)*
