# 🛒 Olist Data & AI Platform: End-to-End Zero-Budget Architecture

## 📌 Visão Geral
Este projeto implementa uma plataforma de dados moderna e escalável para o ecossistema de marketplace da **Olist**. O objetivo é processar volumes reais de dados (pedidos, logística, pagamentos e vendedores) para gerar insights estratégicos e democratizar o acesso à informação através de uma interface de **IA Generativa**.

O grande diferencial deste projeto é a **Estratégia Zero-Budget**: toda a infraestrutura e processamento rodam em camadas gratuitas (Free Editions) de ferramentas líderes de mercado, demonstrando como o rigor da engenharia e a otimização de recursos podem entregar valor corporativo sem custos iniciais de licenciamento.

## 🏗️ Arquitetura de Dados (Medallion)
A plataforma adota a **Arquitetura Medalhão** para garantir governança, qualidade e rastreabilidade:

* **Bronze (Raw):** CSVs do Kaggle e de um **CRM fictício** enviados a **Volumes do Unity Catalog** e convertidos em tabelas Delta gerenciadas (`raw.source_olist.*`, `raw.source_crm.*`) por um notebook **PySpark**.
* **Silver (Staging + Trusted):** Tipagem, padronização, regras de negócio e deduplicação via **dbt** (`producao.staging`, `producao.trusted`).
* **Gold (Marts):** Modelagem dimensional (**Kimball**) via **dbt** (`producao.marts`), respondendo **quais clientes do CRM compram no marketplace, quanto e com que frequência**.

### 🔗 CRM x Marketplace
Um gerador determinístico (Faker, `seed 42`) cria um CRM genérico com 20 mil contatos, campanhas, responsáveis e atividades. 75% dos contatos são ligados a clientes reais do Olist pelo `customer_unique_id`; os demais são leads que nunca compraram. A Gold cruza as duas fontes:

| Resultado (dados reais do Olist + CRM fictício) | |
|---|---:|
| Contatos do CRM que compram no marketplace | **74,3%** |
| Recompradores entre os compradores | 7,8% |
| Ticket médio | R$ 158,68 |
| Intervalo médio entre pedidos (recompradores) | 82,5 dias |
| Contatos que compram mas o CRM ainda trata como lead | **3.588** |

## 🛠️ Stack Tecnológica
* **Processamento & Data Lake:** [Databricks Free Edition](https://www.databricks.com/learn/free-edition) (Spark, Delta Lake & Unity Catalog).
* **Engenharia Analítica:** [dbt Core](https://www.getdbt.com/) para transformações modulares e governança.
* **Inteligência Artificial:** Agente **NL2SQL** utilizando Llama 3 via **Groq API** para consultas em linguagem natural.
* **CI/CD:** **GitHub Actions** para automação de testes de qualidade e linting de SQL.

## 🤖 Inovação: Interface NL2SQL & AI Validation Layer
Para eliminar a barreira técnica entre os dados e os tomadores de decisão, integramos um agente de IA que traduz perguntas em linguagem natural diretamente para consultas SQL otimizadas.
* **Exemplo:** *"Qual região teve o maior faturamento no último trimestre?"* → O agente identifica as tabelas Fato/Dimensão e gera a query em tempo real.

### 🔴 AI Validation Layer (Data Engineering + AI Governance)
To ensure reliability and reduce hallucinations from LLM-generated code, this project implements an **AI Validation Layer**. 

> **Toda saída gerada por IA passa por validação manual antes da execução.** A IA é usada como um acelerador — não como fonte de verdade.

This layer enforces:
* **Schema validation:** Valida a existência de tabelas e colunas (ex: `customer_id` existe?).
* **SQL quality rules:** Usa o `sqlfluff` para validar a sintaxe e regras como evitar `SELECT *` e garantir a cláusula `WHERE`.
* **Documentation alignment:** Garante que a IA não divirja das regras de negócio e dicionário de dados estabelecidos na documentação.
* **Human-in-the-loop review:** Aprovação humana para mitigar riscos operacionais.

## 🗂️ Estrutura do Repositório
```text
├── .github/workflows/   # Automação de CI/CD (Linter e dbt Test)
├── docs/                # Documentação técnica e dicionário de dados
├── databricks/          # Notebooks Databricks (Bronze, setup do Unity Catalog e do Job)
├── pipelines/           # Ingestão Kaggle, gerador do CRM e lógica Bronze (PySpark)
├── transform/           # Projeto dbt (staging, trusted, marts, testes)
└── ml_ops/              # Implementação de IA e Governança
    ├── ai_agent/        # Interface NL2SQL
    └── validation_layer/# Camada de validação de queries (Schema, SQL, Docs)
```

## 🚀 Como Começar (Quick Start)

Este projeto utiliza um **Ambiente Virtual Python (venv)** para execução local.

### 1. Clonar e Preparar
```bash
git clone https://github.com/anascunha/olist-data-platform.git
cd olist-data-platform
cp .env.example .env
```
*(Preencha as credenciais no arquivo `.env` seguindo a documentação)*

### 2. Configurar o Ambiente Local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 📚 Documentação Técnica

Para o passo a passo completo sobre como configurar o Databricks Community Edition e provisionar o projeto, consulte os guias na pasta `docs/`:

* 📖 [Fase 1 — Infraestrutura e Configuração do Ambiente](./docs/phase-01-infrastructure.md)
* 📖 [Fase 2 — Pipeline de Ingestão (Bronze)](./docs/phase-02-ingestion.md)
* 📖 [Fase 3 — CRM Fictício ligado ao Olist](./docs/phase-03-crm.md)
* 📖 [Fase 4 — Transformação com dbt (Silver e Gold)](./docs/phase-04-dbt.md)
* *(Mais fases em breve...)*