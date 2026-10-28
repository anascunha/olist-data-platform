-- ================================================================================
-- CRIAÇÃO DE CATÁLOGOS, SCHEMAS E VOLUMES - OLIST DATA PLATFORM
-- ================================================================================
-- Executar este script UMA VEZ (SQL Editor ou notebook) para provisionar a
-- estrutura completa no Unity Catalog. Mesma organização do projeto Adventure Works.
-- ================================================================================

-- ================================================================================
-- 1. CATÁLOGO RAW - Camada Bronze (dados brutos)
-- ================================================================================
CREATE CATALOG IF NOT EXISTS raw
COMMENT 'Raw - Dados brutos de ingestão (Bronze)';

CREATE SCHEMA IF NOT EXISTS raw.source_olist
COMMENT 'Source - Olist Brazilian E-Commerce (Kaggle: olistbr/brazilian-ecommerce)';

CREATE SCHEMA IF NOT EXISTS raw.source_crm
COMMENT 'Source - CRM genérico com dados fictícios (pipelines/generate_crm.py)';

-- Volumes de landing: recebem os CSVs antes da conversão para Delta
CREATE VOLUME IF NOT EXISTS raw.source_olist.landing
COMMENT 'Landing - CSVs do Kaggle enviados por pipelines/download_data.py';

CREATE VOLUME IF NOT EXISTS raw.source_crm.landing
COMMENT 'Landing - CSVs do CRM fictício enviados por pipelines/generate_crm.py';

-- ================================================================================
-- 2. CATÁLOGO SANDBOX - Workspace individual de desenvolvimento (dbt target dev)
-- ================================================================================
CREATE CATALOG IF NOT EXISTS sandbox
COMMENT 'Sandbox - Workspace individual para desenvolvimento com dbt';

CREATE SCHEMA IF NOT EXISTS sandbox.dbt_sara
COMMENT 'Workspace dbt - Sara';

-- ================================================================================
-- 3. CATÁLOGO PRODUCAO - Modelos dbt validados (dbt target prod)
-- ================================================================================
CREATE CATALOG IF NOT EXISTS producao
COMMENT 'Produção - Modelos dbt validados';

CREATE SCHEMA IF NOT EXISTS producao.staging
COMMENT 'Staging (Silver) - Dados limpos, tipados e padronizados';

CREATE SCHEMA IF NOT EXISTS producao.trusted
COMMENT 'Trusted (Silver) - Regras de negócio e integração Olist x CRM';

CREATE SCHEMA IF NOT EXISTS producao.marts
COMMENT 'Marts (Gold) - Modelos dimensionais e agregados para BI/Analytics';

-- ================================================================================
-- VERIFICAÇÃO
-- ================================================================================
SHOW SCHEMAS IN raw;
SHOW VOLUMES IN raw.source_olist;
SHOW VOLUMES IN raw.source_crm;
SHOW SCHEMAS IN sandbox;
SHOW SCHEMAS IN producao;

-- ================================================================================
-- ESTRUTURA FINAL:
-- ================================================================================
-- raw.source_olist          → 9 tabelas Bronze do Olist
-- raw.source_olist.landing  → Volume com os CSVs do Kaggle
-- raw.source_crm            → 4 tabelas Bronze do CRM fictício
-- raw.source_crm.landing    → Volume com os CSVs do CRM
--
-- sandbox.dbt_sara          → Workspace individual dbt (target dev)
--
-- producao.staging          → Silver - staging
-- producao.trusted          → Silver - trusted
-- producao.marts            → Gold   - marts
-- ================================================================================
