"""Funções puras compartilhadas entre a ingestão local e o notebook Bronze."""

import re


def table_name_from_file(file_name: str) -> str:
    """
    Converte o nome do CSV no nome da tabela Bronze.

    olist_orders_dataset.csv            -> orders
    product_category_name_translation.csv -> product_category_name_translation
    crm_contacts.csv                     -> contacts
    """
    name = file_name.rsplit("/", 1)[-1].lower()
    name = re.sub(r"\.csv$", "", name)
    name = re.sub(r"^(olist|crm)_", "", name)
    return re.sub(r"_dataset$", "", name)


def sanitize_column_name(column: str) -> str:
    """
    Normaliza nomes de colunas para compatibilidade com Delta Lake.
    Remove o BOM (\\ufeff) presente no header de product_category_name_translation.csv.
    """
    clean = column.replace("\ufeff", "").strip().lower()
    clean = re.sub(r"[ ()\{\};.\-]", "_", clean)
    clean = re.sub(r"_+", "_", clean)
    return clean.strip("_")


def get_allowed_tables(rules):
    """Retorna a lista `allowed_tables` das regras da AI Validation Layer (ou None)."""
    for rule in rules or []:
        if isinstance(rule, dict) and "allowed_tables" in rule:
            return rule["allowed_tables"]
    return None
