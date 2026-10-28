"""Unit tests for pipelines/utils.py and pipelines/config.py"""

import pytest

from pipelines.config import target_table, volume_path
from pipelines.utils import get_allowed_tables, sanitize_column_name, table_name_from_file


class TestTableNameFromFile:
    @pytest.mark.parametrize(
        "file_name, expected",
        [
            ("olist_orders_dataset.csv", "orders"),
            ("olist_order_items_dataset.csv", "order_items"),
            ("product_category_name_translation.csv", "product_category_name_translation"),
            ("crm_contacts.csv", "contacts"),
            ("/Volumes/raw/source_olist/landing/olist_customers_dataset.csv", "customers"),
            ("OLIST_SELLERS_DATASET.CSV", "sellers"),
        ],
    )
    def test_conversion(self, file_name, expected):
        assert table_name_from_file(file_name) == expected


class TestSanitizeColumnName:
    def test_removes_bom(self):
        assert sanitize_column_name("\ufeffproduct_category_name") == "product_category_name"

    def test_replaces_invalid_characters(self):
        assert sanitize_column_name("Order (ID).Value") == "order_id_value"

    def test_keeps_valid_name(self):
        assert sanitize_column_name("customer_unique_id") == "customer_unique_id"


class TestGetAllowedTables:
    def test_returns_list(self):
        assert get_allowed_tables([{"no_select_star": True}, {"allowed_tables": ["a"]}]) == ["a"]

    def test_returns_none_without_rule(self):
        assert get_allowed_tables([{"no_select_star": True}]) is None
        assert get_allowed_tables(None) is None


class TestConfig:
    def test_volume_path(self):
        assert volume_path("olist") == "/Volumes/raw/source_olist/landing"
        assert volume_path("crm") == "/Volumes/raw/source_crm/landing"

    def test_target_table(self):
        assert target_table("crm", "contacts") == "raw.source_crm.contacts"
