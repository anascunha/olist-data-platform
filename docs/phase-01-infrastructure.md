# Fase 1 — Infraestrutura e Configuração do Ambiente

Este documento guia a configuração do ambiente local e do workspace **Databricks Free Edition**, seguindo a estratégia Zero-Budget. Os dados ficam no **Unity Catalog**: arquivos em **Volumes** e tabelas **Delta gerenciadas**.

---

## Pré-requisitos

| Ferramenta | Versão | Observação |
|---|---|---|
| Python | **3.11** (mínimo 3.10) | Mesma versão do CI. Dependências como `faker==40.44.0` e o dbt atual não instalam em 3.9 |
| Java | **17** | Só para os testes com Spark local; sem Java, esses testes são pulados |
| Databricks CLI | v0.205+ (CLI nova, binário) | Não usar o pacote `databricks-cli` do pip, que foi descontinuado |
| Git | qualquer | |
| Conta Databricks | [Free Edition](https://www.databricks.com/learn/free-edition) | Workspace serverless com Unity Catalog |

---

## 1. Clonar o repositório

```bash
git clone https://github.com/anascunha/olist-data-platform.git
cd olist-data-platform
```

---

## 2. Ambiente virtual Python

```bash
make setup     # cria .venv e instala requirements.txt
make test      # 45 testes unitários
```

> ⚠️ O `make setup` usa o `python3` do sistema. Se ele for anterior ao 3.10, crie a `.venv` com a versão certa antes, por exemplo com o [uv](https://docs.astral.sh/uv/):
> ```bash
> uv python install 3.11
> uv venv --python 3.11 .venv
> source .venv/bin/activate
> uv pip install -r requirements.txt
> ```

Java 17 no Ubuntu/WSL:
```bash
sudo apt update && sudo apt install -y openjdk-17-jdk-headless
```

---

## 3. Credenciais do Kaggle

O dataset da Olist vem do Kaggle:

1. Acesse [kaggle.com](https://www.kaggle.com) → **Settings → API → Create New Token**.
2. Copie o arquivo de exemplo e preencha:
   ```bash
   cp .env.example .env
   ```
   ```bash
   KAGGLE_USERNAME=seu_usuario
   KAGGLE_KEY=sua_chave
   ```

O `.env` **nunca deve ser commitado** (já está no `.gitignore`).

---

## 4. Databricks CLI com OAuth

### 4.1. Instalar

```bash
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sudo sh
databricks --version
```

### 4.2. Autenticar (OAuth, recomendado)

```bash
databricks auth login --host https://<seu-workspace>.cloud.databricks.com
databricks current-user me      # confirma o login
```

O login abre o navegador e a CLI guarda um token de **curta duração**, renovado automaticamente, em `~/.databricks/` — fora do repositório. Não é preciso criar token pessoal (PAT).

> ⚠️ **Não coloque `DATABRICKS_HOST`/`DATABRICKS_TOKEN` no `.env` da raiz.** Os scripts carregam o `.env`, e variáveis de ambiente têm **prioridade** sobre o perfil da CLI: um token antigo ali faz o upload falhar mesmo com o OAuth funcionando.
>
> Se o `databricks current-user me` falhar com *Invalid access token*, confira em `~/.databrickscfg` se um perfil antigo com `token =` está como padrão (`default_profile`).

### 4.3. HTTP Path do SQL Warehouse (para o dbt)

**SQL Warehouses** → seu warehouse (no Free Edition, *Serverless Starter Warehouse*) → **Connection details** → copie o **HTTP Path** (`/sql/1.0/warehouses/...`). Ele vai no `transform/.env` (ver [Fase 4](./phase-04-dbt.md)).

---

## 5. Provisionar o Unity Catalog

No **SQL Editor**, execute [`databricks/setup/setup_catalogs_schemas.sql`](../databricks/setup/setup_catalogs_schemas.sql). O script é idempotente (`IF NOT EXISTS`).

```text
Databricks Free Edition — Unity Catalog
├── raw.source_olist / raw.source_crm   ← Bronze (Volumes de landing + tabelas Delta)
├── sandbox.dbt_<nome>                  ← desenvolvimento dbt
├── producao.staging / producao.trusted ← Silver (dbt)
└── producao.marts                      ← Gold (dbt)

Local
└── .venv (Python 3.11): pipelines de landing, testes e dbt-databricks
```

---

## Próxima fase

→ [Fase 2 — Pipeline de Ingestão](./phase-02-ingestion.md)
