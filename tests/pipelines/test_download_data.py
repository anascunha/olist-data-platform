"""
Unit tests for pipelines/download_data.py

Strategy: mock subprocess (Kaggle CLI / Databricks CLI) so tests run with no
credentials and no network. Filesystem operations use pytest's tmp_path.
"""

import subprocess
import zipfile
from unittest.mock import patch

from pipelines import download_data

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_kaggle_download(tmp_dir, files):
    """Returns a side_effect for subprocess.run that writes the dataset zip."""

    def _side_effect(cmd, check):
        with zipfile.ZipFile(tmp_dir / "brazilian-ecommerce.zip", "w") as zf:
            for name in files:
                zf.writestr(name, "col_a,col_b\n1,2\n")

    return _side_effect


# ---------------------------------------------------------------------------
# download_dataset
# ---------------------------------------------------------------------------


class TestDownloadDataset:
    def test_calls_kaggle_cli_with_dataset(self, tmp_path):
        with patch("pipelines.download_data.subprocess.run") as mock_run:
            mock_run.side_effect = _fake_kaggle_download(tmp_path, ["olist_orders_dataset.csv"])
            download_data.download_dataset(tmp_path)

        cmd = mock_run.call_args.args[0]
        assert cmd[:3] == ["kaggle", "datasets", "download"]
        assert "olistbr/brazilian-ecommerce" in cmd

    def test_extracts_zip_and_removes_it(self, tmp_path):
        with patch("pipelines.download_data.subprocess.run") as mock_run:
            mock_run.side_effect = _fake_kaggle_download(tmp_path, ["olist_orders_dataset.csv"])
            assert download_data.download_dataset(tmp_path) is True

        assert (tmp_path / "olist_orders_dataset.csv").exists()
        assert not (tmp_path / "brazilian-ecommerce.zip").exists()

    def test_kaggle_error_returns_false(self, tmp_path, capsys):
        with patch("pipelines.download_data.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "kaggle")
            assert download_data.download_dataset(tmp_path) is False

        assert "Erro ao baixar o dataset" in capsys.readouterr().out

    def test_missing_cli_returns_false(self, tmp_path):
        with patch("pipelines.download_data.subprocess.run", side_effect=FileNotFoundError):
            assert download_data.download_dataset(tmp_path) is False

    def test_missing_zip_returns_false(self, tmp_path, capsys):
        with patch("pipelines.download_data.subprocess.run"):
            assert download_data.download_dataset(tmp_path) is False

        assert "zip não encontrado" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# stage_allowed_files (governança)
# ---------------------------------------------------------------------------


class TestStageAllowedFiles:
    def _populate(self, directory, names):
        for name in names:
            (directory / name).write_text("a,b\n1,2\n")

    def test_moves_only_allowed_tables(self, tmp_path):
        src, dst = tmp_path / "raw", tmp_path / "landing"
        src.mkdir()
        self._populate(src, ["olist_orders_dataset.csv", "olist_unknown_dataset.csv"])

        moved = download_data.stage_allowed_files(src, dst, ["orders"])

        assert moved == ["olist_orders_dataset.csv"]
        assert (dst / "olist_orders_dataset.csv").exists()
        assert (src / "olist_unknown_dataset.csv").exists()

    def test_without_rules_moves_every_csv(self, tmp_path):
        src, dst = tmp_path / "raw", tmp_path / "landing"
        src.mkdir()
        self._populate(src, ["olist_orders_dataset.csv", "readme.txt"])

        moved = download_data.stage_allowed_files(src, dst, None)

        assert moved == ["olist_orders_dataset.csv"]

    def test_rules_file_allows_all_nine_olist_tables(self):
        allowed = download_data.get_allowed_tables(download_data.load_rules())
        assert len(allowed) == 9
        assert {"orders", "customers", "order_items", "order_payments"} <= set(allowed)


# ---------------------------------------------------------------------------
# upload_to_volume
# ---------------------------------------------------------------------------


class TestUploadToVolume:
    def test_uses_databricks_cli_with_volume_path(self, tmp_path):
        with patch("pipelines.download_data.subprocess.run") as mock_run:
            ok = download_data.upload_to_volume(tmp_path, "/Volumes/raw/source_olist/landing")

        assert ok is True
        cmd = mock_run.call_args.args[0]
        assert cmd[:3] == ["databricks", "fs", "cp"]
        assert cmd[-1] == "dbfs:/Volumes/raw/source_olist/landing"

    def test_upload_error_returns_false(self, tmp_path, capsys):
        with patch(
            "pipelines.download_data.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "databricks"),
        ):
            assert download_data.upload_to_volume(tmp_path, "/Volumes/x/y/z") is False

        assert "Erro no upload" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_stops_when_download_fails(self):
        with patch("pipelines.download_data.download_dataset", return_value=False), patch(
            "pipelines.download_data.upload_to_volume"
        ) as mock_upload:
            assert download_data.main([]) == 1

        mock_upload.assert_not_called()

    def test_skip_upload_flag(self):
        with patch("pipelines.download_data.download_dataset", return_value=True), patch(
            "pipelines.download_data.stage_allowed_files", return_value=["a.csv"]
        ), patch("pipelines.download_data.shutil.rmtree"), patch(
            "pipelines.download_data.upload_to_volume"
        ) as mock_upload:
            assert download_data.main(["--skip-upload"]) == 0

        mock_upload.assert_not_called()

    def test_uploads_to_olist_volume(self):
        with patch("pipelines.download_data.download_dataset", return_value=True), patch(
            "pipelines.download_data.stage_allowed_files", return_value=["a.csv"]
        ), patch("pipelines.download_data.shutil.rmtree"), patch(
            "pipelines.download_data.upload_to_volume", return_value=True
        ) as mock_upload:
            assert download_data.main([]) == 0

        assert mock_upload.call_args.args[1] == "/Volumes/raw/source_olist/landing"
