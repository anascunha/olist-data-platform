# 🛒 Olist Data & AI Platform: End-to-End Zero-Budget Architecture

## 📌 Visão Geral
Este projeto implementa uma plataforma de dados moderna e escalável para o ecossistema de marketplace da **Olist**. O objetivo é processar volumes reais de dados (pedidos, logística, pagamentos e vendedores) para gerar insights estratégicos e democratizar o acesso à informação através de uma interface de **IA Generativa**.

O grande diferencial deste projeto é a **Estratégia Zero-Budget**: toda a infraestrutura e processamento rodam em camadas gratuitas (Free Editions) de ferramentas líderes de mercado, demonstrando como o rigor da engenharia e a otimização de recursos podem entregar valor corporativo sem custos iniciais de licenciamento.

## 🏗️ Arquitetura de Dados (Medallion)
A plataforma adota a **Arquitetura Medalhão** para garantir governança, qualidade e rastreabilidade:

* **Bronze (Raw):** Ingestão de dados brutos em formato Parquet/Delta armazenados em **Azure Blob Storage**.
* **Silver (Trusted):** Limpeza, padronização e deduplicação utilizando **PySpark** no **Databricks**.
* **Gold (Curated):** Modelagem dimensional (**Star Schema/Kimball**) via **dbt Core**, otimizada para consumo analítico e IA.

## 🛠️ Stack Tecnológica
* **Infraestrutura (IaC):** [Terraform](https://www.terraform.io/) para provisionamento na Azure (Free Tier).
* **Processamento:** [Databricks Community Edition](https://community.cloud.databricks.com/) (Spark & Delta Lake).
* **Engenharia Analítica:** [dbt Core](https://www.getdbt.com/) para transformações modulares e governança.
* **Inteligência Artificial:** Agente **NL2SQL** utilizando Llama 3 via **Groq API** para consultas em linguagem natural.
* **CI/CD:** **GitHub Actions** para automação de testes de qualidade e linting de SQL.

## 🤖 Inovação: Interface NL2SQL
Para eliminar a barreira técnica entre os dados e os tomadores de decisão, integramos um agente de IA que traduz perguntas em linguagem natural diretamente para consultas SQL otimizadas.
* **Exemplo:** *"Qual região teve o maior faturamento no último trimestre?"* → O agente identifica as tabelas Fato/Dimensão e gera a query em tempo real.

## 🗂️ Estrutura do Repositório
```text
├── .github/workflows/   # Automação de CI/CD (Linter e dbt Test)
├── docs/                # Documentação técnica e dicionário de dados
├── infra/               # Código Terraform para provisionamento na Azure
├── pipelines/           # Scripts de ingestão e processamento Spark
├── transform/           # Projeto dbt (Models, Macros, Snapshots)
└── ml_ops/              # Implementação do Agente de IA e integração LLM
```

## 🚀 Como Começar (Quick Start)

Este projeto utiliza **Docker** e um **Makefile** para simplificar a configuração do ambiente local.

### 1. Clonar e Preparar
```bash
git clone https://github.com/<seu-usuario>/olist-data-platform.git
cd olist-data-platform
cp .env.example .env
```
*(Preencha as credenciais no arquivo `.env` seguindo a documentação)*

### 2. Subir o Ambiente
```bash
make setup   # Constrói a imagem Docker base (Python 3.11, dbt, PySpark)
make up      # Inicia o contêiner de desenvolvimento
make shell   # Abre um terminal dentro do ambiente isolado
```

## 📚 Documentação Técnica

Para o passo a passo completo sobre como configurar as nuvens gratuitas (Azure e Databricks) e provisionar a infraestrutura, consulte os guias na pasta `docs/`:

* 📖 [Fase 1 — Infraestrutura e Configuração do Ambiente](./docs/phase-01-infrastructure.md)
* *(Mais fases em breve...)*