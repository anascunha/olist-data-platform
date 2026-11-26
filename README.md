# 🛒 Olist Data Platform: End-to-End Zero-Budget Architecture

## 📌 Visão Geral
Este projeto implementa uma plataforma de dados de ponta a ponta para o marketplace da **Olist**: dados reais de pedidos, pagamentos, produtos e vendedores (dataset público do Kaggle) cruzados com um **CRM fictício**, para responder **quais clientes do CRM compram no marketplace, quanto e com que frequência**.

O diferencial é a **Estratégia Zero-Budget**: toda a infraestrutura roda em camadas gratuitas — **Databricks Free Edition** (serverless), dbt Core e GitHub Actions — sem custo de licenciamento.

## 🏗️ Arquitetura de Dados (Medallion)

```text
Kaggle ──make ingest──┐
                      ├──▶ Volumes do Unity Catalog ──notebook PySpark──▶ Bronze (Delta) ──dbt──▶ Silver ──dbt──▶ Gold
CRM fictício ─make crm┘     (raw.source_*.landing)                       raw.source_*          staging/trusted    marts
```

* **Bronze (Raw):** CSVs do Kaggle e do CRM fictício enviados a **Volumes do Unity Catalog** e convertidos em **tabelas Delta gerenciadas** (`raw.source_olist.*`, `raw.source_crm.*`) por um notebook **PySpark**. Todas as colunas como texto, mais colunas de rastreabilidade (`_ingestion_timestamp`, `_source_table`…).
* **Silver (Staging + Trusted):** tipagem explícita, padronização, regras de negócio e deduplicação via **dbt** (`producao.staging`, `producao.trusted`).
* **Gold (Marts):** modelagem dimensional (**Kimball**) via **dbt** (`producao.marts`).

No desenvolvimento, o dbt grava tudo em um schema pessoal (`sandbox.dbt_<nome>`); em produção, cada camada tem seu schema em `producao`.

### 🔗 CRM x Marketplace
Um gerador determinístico (Faker, `seed 42`) cria um CRM genérico com 20 mil contatos, campanhas, responsáveis e atividades — com problemas de qualidade propositais (2% de duplicatas, e-mails sujos, telefones em 3 formatos). 75% dos contatos são ligados a clientes reais do Olist pelo `customer_unique_id`; os demais são leads que nunca compraram.

| Resultado (execução no Databricks Free Edition) | |
|---|---:|
| Contatos do CRM que compram no marketplace | **74,3%** (14.854 de 20.000) |
| Recompradores entre os compradores | 7,8% |
| Ticket médio | R$ 158,63 |
| Intervalo médio entre pedidos (recompradores) | 82,5 dias |
| Contatos que compram mas o CRM ainda trata como lead/opportunity | **3.588** |

> As compras são dados reais do Olist; o CRM é fictício. O valor do projeto está no pipeline e na modelagem.

## ✅ Execução validada

Rodado de ponta a ponta no **Databricks Free Edition** (serverless):

| Etapa | Resultado |
|---|---|
| Landing | 9 CSVs do Olist + 4 do CRM nos Volumes |
| Bronze | 13 tabelas Delta gerenciadas — **1.550.922** linhas do Olist em ~1 min, contagens conferidas com a fonte |
| Silver + Gold | `dbt build`: **13 views, 5 tabelas e 114 testes de dados — PASS=132** |
| Deduplicação do CRM | 20.400 linhas na Bronze → 20.000 contatos na Silver |
| Orquestração | Lakeflow Job `Pipeline_Olist_Bronze_dbt` (Bronze → task dbt em serverless), executado manualmente, gravando em `producao.*` — a Gold de produção bate com a de dev |
| Governança (Unity Catalog) | Grupos de conta `analistas` e `leitores_pii`; `analistas` leem só `producao.marts`; máscaras em `email` e `phone_e164` da `dim_crm_contact` (só `leitores_pii` vê completo); tags `pii` nas colunas pessoais da Bronze do CRM — aplicados pelo painel do Databricks |

> **Validação com gabarito:** como o CRM é gerado, as respostas são conhecidas — 75% dos contatos ligados ao Olist, 2% de duplicatas, parte dos compradores marcada como lead. O pipeline reencontra esses valores (74,3% compradores; 20.400 → 20.000; 3.588 estágios desatualizados), o que valida a lógica de ligação, deduplicação e regras de negócio.

## 🛠️ Stack Tecnológica
* **Processamento & Data Lake:** [Databricks Free Edition](https://www.databricks.com/learn/free-edition) — Spark, Delta Lake, Unity Catalog, SQL Warehouse serverless.
* **Engenharia Analítica:** [dbt Core](https://www.getdbt.com/) + `dbt-databricks`.
* **Qualidade:** `pytest` (incluindo testes com Spark local) e 114 testes de dados do dbt.
* **CI:** **GitHub Actions** — a cada push e pull request roda `ruff` (lint Python), `pytest` e `dbt parse` nos targets `dev` e `prod`. Ainda **não há CD** (deploy automático); a execução no Databricks é manual.
* **Autenticação:** OAuth (`databricks auth login`) na CLI e no dbt de desenvolvimento — sem token fixo em arquivo.

## 🧭 Próximos passos (melhorias)
* **Identidade do Job:** rodar com um **service principal** (OAuth M2M) em vez de usuário pessoal, e agendar conforme a necessidade de atualização do negócio.
* **Governança como código:** declarar máscaras (`column_mask` do `dbt-databricks`), `GRANT`s e tags no repositório, em vez de aplicá-los pelo painel — e evitar que a ingestão sobrescreva os comentários da Bronze. Próximo nível: política **ABAC** por tag (`pii`), para tabelas novas já nascerem protegidas.
* **CD:** deploy do Job e dos notebooks com **Declarative Automation Bundles** (antigo *Databricks Asset Bundles*) a partir do GitHub Actions, e `dbt build` no CI com um service principal.
* **Carga incremental:** Auto Loader na Bronze e modelos incrementais (`MERGE`) no dbt, no lugar do overwrite completo.
* **Filtro de governança fail-closed:** hoje, se a lista de tabelas permitidas vier vazia, tudo passa; o correto é bloquear.
* **Agente NL2SQL (planejado):** perguntas em linguagem natural traduzidas para SQL sobre a Gold, com Llama 3 via **Groq** e uma **camada de validação** (schema, qualidade do SQL, aprovação humana antes da execução). Hoje existem apenas as regras e a estrutura em `ml_ops/validation_layer/` — o agente ainda não foi implementado.

## 🗂️ Estrutura do Repositório
```text
├── .github/workflows/   # CI: ruff, pytest e dbt parse
├── docs/                # Guias por fase
├── databricks/          # Notebook Bronze, setup do Unity Catalog e do Job
├── pipelines/           # Download do Kaggle, gerador do CRM e lógica Bronze (PySpark)
├── tests/               # Testes unitários (pytest), espelhando pipelines/
├── transform/           # Projeto dbt (staging, trusted, marts, testes)
└── ml_ops/
    └── validation_layer/# Regras de governança (rules.yaml) e estrutura da validação planejada
```

## 🚀 Como Começar (Quick Start)

**Pré-requisitos:** Python **3.11**, Java **17** (para os testes com Spark local), Git e [Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/install).

```bash
git clone https://github.com/anascunha/olist-data-platform.git
cd olist-data-platform
cp .env.example .env        # credenciais do Kaggle

make setup                  # cria a .venv e instala as dependências
make test                   # 45 testes unitários

databricks auth login --host https://<seu-workspace>.cloud.databricks.com
```

Fluxo completo no Databricks:
1. Rodar `databricks/setup/setup_catalogs_schemas.sql` no SQL Editor (uma vez).
2. `make ingest` e `make crm` — enviam os CSVs aos Volumes.
3. Abrir o repositório como *Git folder* e rodar `databricks/ingestao_bronze.py` com `source = all`.
4. `cd transform && dbt build --profiles-dir .` (ver [Fase 4](./docs/phase-04-dbt.md)).

Ou tudo de uma vez em produção: rodar `databricks/setup/setup_pipeline_olist.py` (cria o Job) e **Run now** no Job `Pipeline_Olist_Bronze_dbt`.

## 📚 Documentação Técnica

* 📖 [Fase 1 — Infraestrutura e Configuração do Ambiente](./docs/phase-01-infrastructure.md)
* 📖 [Fase 2 — Pipeline de Ingestão (Bronze)](./docs/phase-02-ingestion.md)
* 📖 [Fase 3 — CRM Fictício ligado ao Olist](./docs/phase-03-crm.md)
* 📖 [Fase 4 — Transformação com dbt (Silver e Gold)](./docs/phase-04-dbt.md)
