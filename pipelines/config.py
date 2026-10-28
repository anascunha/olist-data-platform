"""
Configuração central do Unity Catalog usada pelos pipelines locais e pelos notebooks.

Estrutura (espelhando o projeto Adventure Works):

    raw.source_olist          ← tabelas Bronze do Olist (Kaggle)
    raw.source_olist.landing  ← Volume com os CSVs brutos do Olist
    raw.source_crm            ← tabelas Bronze do CRM fictício
    raw.source_crm.landing    ← Volume com os CSVs brutos do CRM

Todos os nomes podem ser sobrescritos por variáveis de ambiente.
"""

import os

RAW_CATALOG = os.getenv("UC_RAW_CATALOG", "raw")
LANDING_VOLUME = os.getenv("UC_LANDING_VOLUME", "landing")

SOURCES = {
    "olist": {
        "schema": os.getenv("UC_OLIST_SCHEMA", "source_olist"),
        "source_database": "kaggle:olistbr/brazilian-ecommerce",
    },
    "crm": {
        "schema": os.getenv("UC_CRM_SCHEMA", "source_crm"),
        "source_database": "crm_generator",
    },
}


def volume_path(source: str) -> str:
    """Caminho POSIX do Volume de landing de uma fonte (ex: /Volumes/raw/source_olist/landing)."""
    return f"/Volumes/{RAW_CATALOG}/{SOURCES[source]['schema']}/{LANDING_VOLUME}"


def target_table(source: str, table: str) -> str:
    """Nome totalmente qualificado da tabela Bronze (ex: raw.source_olist.orders)."""
    return f"{RAW_CATALOG}.{SOURCES[source]['schema']}.{table}"
