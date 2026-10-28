# Fase 2 — Pipeline de Ingestão (Bronze Layer)

Este documento detalha o pipeline de ingestão desta fase. O objetivo é buscar o dataset completo da Olist no Kaggle e carregá-lo de forma automatizada no **Unity Catalog** do Databricks, estabelecendo a fundação da **Camada Bronze**.

A organização segue o mesmo padrão do projeto Adventure Works: um catálogo `raw` com um schema por fonte de dados, tabelas Delta gerenciadas e colunas de rastreabilidade em todas as tabelas.

---

## 🗂️ Estrutura no Unity Catalog

Provisionada uma única vez por [`databricks/setup/setup_catalogs_schemas.sql`](../databricks/setup/setup_catalogs_schemas.sql):

```text
raw                              ← Bronze
├── source_olist                 ← tabelas Delta do Olist
│   └── landing (Volume)         ← CSVs vindos do Kaggle
└── source_crm                   ← tabelas Delta do CRM fictício (Fase 3)
    └── landing (Volume)

sandbox.dbt_sara                 ← desenvolvimento dbt (Fase 4)
producao.staging / trusted       ← Silver (Fase 4)
producao.marts                   ← Gold   (Fase 4)
```

Os nomes podem ser alterados por variáveis de ambiente (`UC_RAW_CATALOG`, `UC_OLIST_SCHEMA`, `UC_CRM_SCHEMA`, `UC_LANDING_VOLUME`); ver [`pipelines/config.py`](../pipelines/config.py).

---

## 🏗️ Como a Ingestão Funciona?

A ingestão tem duas etapas: **landing** (local → Volume) e **Bronze** (Volume → Delta).

### Etapa 1 — Landing (`pipelines/download_data.py`, roda localmente)

1. **Extração automática (Kaggle CLI):** baixa o pacote `olistbr/brazilian-ecommerce` em `data/raw/`.
2. **Unzip & preparação:** descompacta os 9 CSVs.
3. **Governança ativa (AI Validation Layer):** apenas tabelas mapeadas em `allowed_tables` de [`ml_ops/validation_layer/rules.yaml`](../ml_ops/validation_layer/rules.yaml) seguem adiante. Tabelas desconhecidas são ignoradas.
4. **Upload para o Unity Catalog:** a Databricks CLI copia os arquivos aprovados para o Volume `/Volumes/raw/source_olist/landing/`.
5. **Sanitização local:** o diretório temporário é removido.

### Etapa 2 — Bronze (`databricks/ingestao_bronze.py`, roda no Databricks)

Notebook PySpark (formato *source*, versionado no Git) que, para cada CSV do Volume:

* lê o arquivo **sem inferência de tipos**, porque a tipagem fica no staging do dbt e a Bronze preserva o dado como veio;
* trata `multiLine` (comentários de reviews com quebra de linha) e o **BOM** no header de `product_category_name_translation.csv`;
* normaliza os nomes de colunas para Delta Lake;
* adiciona as colunas de rastreabilidade `_ingestion_timestamp`, `_source_schema`, `_source_table`, `_source_database` e `_storage_type`;
* grava uma **tabela Delta gerenciada** `raw.source_olist.<tabela>` e registra um `COMMENT` com origem, volume de registros e data de carga.

| Widget | Valores | Descrição |
|---|---|---|
| `source` | `olist`, `crm`, `all` | Fonte a ser ingerida |
| `mode` | `full`, `incremental` | `incremental` pula tabelas já existentes |

A lógica fica em [`pipelines/bronze.py`](../pipelines/bronze.py), coberta por testes unitários com Spark local. O notebook só lê os widgets e chama `run_bronze_pipeline`.

---

## 🚀 Como Executar

1. **Provisionar o Unity Catalog** (uma vez): rode `databricks/setup/setup_catalogs_schemas.sql` no SQL Editor.
2. **Landing:** na raiz do projeto, com a `venv` ativada:
   ```bash
   make ingest
   ```
   Para apenas baixar e filtrar, sem enviar ao Databricks: `python -m pipelines.download_data --skip-upload`.
3. **Bronze:** no workspace, abra o repositório como *Git folder* e execute `databricks/ingestao_bronze.py` com `source = olist`.

### 💡 Validando a ingestão

```bash
databricks fs ls dbfs:/Volumes/raw/source_olist/landing/
```

```sql
SHOW TABLES IN raw.source_olist;
SELECT COUNT(*) FROM raw.source_olist.orders;   -- 99.441
```

---

## 📊 Tabelas disponibilizadas na Bronze

| Tabela | Registros |
|---|---:|
| `raw.source_olist.customers` | 99.441 |
| `raw.source_olist.geolocation` | 1.000.163 |
| `raw.source_olist.order_items` | 112.650 |
| `raw.source_olist.order_payments` | 103.886 |
| `raw.source_olist.order_reviews` | 99.224 |
| `raw.source_olist.orders` | 99.441 |
| `raw.source_olist.products` | 32.951 |
| `raw.source_olist.sellers` | 3.095 |
| `raw.source_olist.product_category_name_translation` | 71 |

---

## Próxima Fase
Com a Bronze do Olist populada, a Fase 3 gera um **CRM fictício** ligado aos clientes do marketplace pelo `customer_unique_id` e o ingere pelo mesmo notebook Bronze (`source = crm`).

→ [Fase 3 — CRM Fictício](./phase-03-crm.md)
