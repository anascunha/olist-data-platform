"""
Unit tests for pipelines/generate_crm.py

Strategy: build a tiny synthetic Olist (customers + orders CSVs) in tmp_path and
check the business invariants of the generated CRM.
"""

import csv
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipelines import generate_crm

N_CUSTOMERS = 400


@pytest.fixture
def olist_dir(tmp_path):
    """400 clientes únicos; os 40 primeiros com 2 pedidos (recompradores)."""
    directory = tmp_path / "olist"
    directory.mkdir()
    customers, orders = [], []
    base = datetime(2017, 1, 1)
    for i in range(N_CUSTOMERS):
        uid = f"u{i:04d}"
        n_orders = 2 if i < 40 else 1
        for j in range(n_orders):
            cid = f"c{i:04d}_{j}"
            customers.append([cid, uid, "01000", "sao paulo", "SP"])
            orders.append([f"o{i:04d}_{j}", cid, "delivered",
                           (base + timedelta(days=i + 30 * j)).strftime("%Y-%m-%d %H:%M:%S")])

    with open(directory / "olist_customers_dataset.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "customer_unique_id", "customer_zip_code_prefix",
                    "customer_city", "customer_state"])
        w.writerows(customers)
    with open(directory / "olist_orders_dataset.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer_id", "order_status", "order_purchase_timestamp"])
        w.writerows(orders)
    return directory


@pytest.fixture
def profiles(olist_dir):
    return generate_crm.load_olist_customers(olist_dir)


@pytest.fixture
def tables(profiles):
    return generate_crm.generate_crm(profiles, n_contacts=200, match_rate=0.5, seed=7)


def _unique_contacts(tables):
    return {c["contact_id"]: c for c in tables["contacts"][1]}


class TestLoadOlistCustomers:
    def test_groups_by_customer_unique_id(self, profiles):
        assert len(profiles) == N_CUSTOMERS
        assert profiles["u0000"]["orders"] == 2
        assert profiles["u0100"]["orders"] == 1

    def test_first_purchase_is_earliest_order(self, profiles):
        assert profiles["u0000"]["first_purchase"] == datetime(2017, 1, 1)


class TestGenerateCrm:
    def test_is_deterministic(self, profiles):
        a = generate_crm.generate_crm(profiles, n_contacts=50, seed=1)
        b = generate_crm.generate_crm(profiles, n_contacts=50, seed=1)
        assert a == b

    def test_match_rate(self, tables):
        contacts = _unique_contacts(tables)
        matched = [c for c in contacts.values() if c["customer_unique_id"]]
        assert len(contacts) == 200
        assert len(matched) == 100

    def test_matched_ids_exist_in_olist_and_are_unique(self, tables, profiles):
        ids = [c["customer_unique_id"] for c in _unique_contacts(tables).values()
               if c["customer_unique_id"]]
        assert len(ids) == len(set(ids))
        assert set(ids) <= set(profiles)

    def test_repeat_buyers_are_oversampled(self, profiles):
        import random

        chosen = generate_crm.select_matched_customers(profiles, 100, random.Random(0), 0.3)
        assert sum(profiles[uid]["orders"] > 1 for uid in chosen) == 30

    def test_duplicates_are_older_versions(self, tables):
        rows = tables["contacts"][1]
        n_unique = len(_unique_contacts(tables))
        latest = {c["contact_id"]: c for c in rows[:n_unique]}
        duplicates = rows[n_unique:]
        assert len(duplicates) == int(len(latest) * 0.02)
        for dup in duplicates:
            assert dup["contact_id"] in latest
            assert dup["updated_at"] <= latest[dup["contact_id"]]["updated_at"]

    def test_dates_are_consistent(self, tables):
        for c in tables["contacts"][1]:
            assert generate_crm.CRM_START <= c["created_at"] <= generate_crm.CRM_END
            assert c["created_at"] <= c["updated_at"] <= generate_crm.CRM_END

    def test_campaign_started_before_contact_creation(self, tables):
        campaigns = {c["campaign_id"]: c for c in tables["campaigns"][1]}
        for c in tables["contacts"][1]:
            if c["campaign_id"]:
                start = campaigns[c["campaign_id"]]["start_date"]
                assert start <= c["created_at"].date()
                assert (c["created_at"].date() - start).days <= 90
                assert c["lead_source"] == campaigns[c["campaign_id"]]["channel"]

    def test_campaign_theme_matches_month(self, tables):
        for c in tables["campaigns"][1]:
            assert c["campaign_name"].startswith(generate_crm.CAMPAIGN_THEMES[c["start_date"].month])

    def test_activities_reference_valid_contacts_and_owners(self, tables):
        contacts = _unique_contacts(tables)
        owners = {o["owner_id"] for o in tables["owners"][1]}
        activity_ids = [a["activity_id"] for a in tables["activities"][1]]
        assert len(activity_ids) == len(set(activity_ids))
        for a in tables["activities"][1]:
            assert a["contact_id"] in contacts
            assert a["owner_id"] in owners
            assert a["activity_at"] >= contacts[a["contact_id"]]["created_at"]


class TestWriteAndMain:
    def test_write_tables_creates_prefixed_csvs(self, tables, tmp_path):
        paths = generate_crm.write_tables(tables, tmp_path / "out")
        assert sorted(p.name for p in paths) == [
            "crm_activities.csv", "crm_campaigns.csv", "crm_contacts.csv", "crm_owners.csv",
        ]
        with open(tmp_path / "out" / "crm_contacts.csv") as f:
            header = next(csv.reader(f))
        assert header == generate_crm.CONTACT_COLUMNS

    def test_main_uploads_to_crm_volume(self, olist_dir, tmp_path):
        with patch("pipelines.generate_crm.upload_to_volume", return_value=True) as mock_upload:
            code = generate_crm.main([
                "--olist-dir", str(olist_dir), "--output-dir", str(tmp_path / "crm"),
                "--contacts", "50",
            ])
        assert code == 0
        assert mock_upload.call_args.args[1] == "/Volumes/raw/source_crm/landing"

    def test_main_skip_upload(self, olist_dir, tmp_path):
        with patch("pipelines.generate_crm.upload_to_volume") as mock_upload:
            generate_crm.main([
                "--olist-dir", str(olist_dir), "--output-dir", str(tmp_path / "crm"),
                "--contacts", "50", "--skip-upload",
            ])
        mock_upload.assert_not_called()
