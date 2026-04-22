"""
Unit tests for pipelines/download_data.py

Strategy: mock KaggleApi and os.makedirs so tests run with no
credentials and without touching the filesystem or network.
"""

from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MODULE = "pipelines.download_data"


def _run(download_path="data/raw"):
    """Import and call the function under test inside every test so that
    module-level patches applied via `patch` decorators are honoured."""
    from pipelines.download_data import download_olist_dataset

    download_olist_dataset(download_path)


# ---------------------------------------------------------------------------
# Tests — happy path
# ---------------------------------------------------------------------------


class TestDownloadOlistDatasetSuccess:
    @patch(f"{MODULE}.KaggleApi")
    @patch(f"{MODULE}.os.makedirs")
    def test_creates_download_directory(self, mock_makedirs, mock_api_cls):
        mock_api_cls.return_value.authenticate.return_value = None
        mock_api_cls.return_value.dataset_download_files.return_value = None

        _run("data/raw")

        mock_makedirs.assert_called_once_with("data/raw", exist_ok=True)

    @patch(f"{MODULE}.KaggleApi")
    @patch(f"{MODULE}.os.makedirs")
    def test_authenticates_kaggle_api(self, mock_makedirs, mock_api_cls):
        mock_instance = MagicMock()
        mock_api_cls.return_value = mock_instance

        _run()

        mock_instance.authenticate.assert_called_once()

    @patch(f"{MODULE}.KaggleApi")
    @patch(f"{MODULE}.os.makedirs")
    def test_downloads_correct_dataset(self, mock_makedirs, mock_api_cls):
        mock_instance = MagicMock()
        mock_api_cls.return_value = mock_instance

        _run()

        mock_instance.dataset_download_files.assert_called_once_with(
            "olistbr/brazilian-ecommerce",
            path="data/raw",
            unzip=True,
        )

    @patch(f"{MODULE}.KaggleApi")
    @patch(f"{MODULE}.os.makedirs")
    def test_custom_download_path_is_used(self, mock_makedirs, mock_api_cls):
        mock_instance = MagicMock()
        mock_api_cls.return_value = mock_instance

        _run("custom/path")

        mock_makedirs.assert_called_once_with("custom/path", exist_ok=True)
        mock_instance.dataset_download_files.assert_called_once_with(
            "olistbr/brazilian-ecommerce",
            path="custom/path",
            unzip=True,
        )

    @patch(f"{MODULE}.KaggleApi")
    @patch(f"{MODULE}.os.makedirs")
    def test_success_prints_confirmation(self, mock_makedirs, mock_api_cls, capsys):
        mock_api_cls.return_value = MagicMock()

        _run()

        captured = capsys.readouterr()
        assert "Download e extração concluídos com sucesso" in captured.out


# ---------------------------------------------------------------------------
# Tests — error / edge cases
# ---------------------------------------------------------------------------


class TestDownloadOlistDatasetErrors:
    @patch(f"{MODULE}.KaggleApi")
    @patch(f"{MODULE}.os.makedirs")
    def test_authentication_error_is_caught(self, mock_makedirs, mock_api_cls, capsys):
        mock_api_cls.return_value.authenticate.side_effect = Exception("auth failed")

        # Should not raise — errors are handled internally
        _run()

        captured = capsys.readouterr()
        assert "Erro ao baixar o dataset" in captured.out

    @patch(f"{MODULE}.KaggleApi")
    @patch(f"{MODULE}.os.makedirs")
    def test_download_error_is_caught(self, mock_makedirs, mock_api_cls, capsys):
        mock_instance = MagicMock()
        mock_instance.dataset_download_files.side_effect = Exception("network error")
        mock_api_cls.return_value = mock_instance

        _run()

        captured = capsys.readouterr()
        assert "Erro ao baixar o dataset" in captured.out

    @patch(f"{MODULE}.KaggleApi")
    @patch(f"{MODULE}.os.makedirs")
    def test_error_message_contains_exception_detail(
        self, mock_makedirs, mock_api_cls, capsys
    ):
        mock_api_cls.return_value.authenticate.side_effect = Exception("missing key")

        _run()

        captured = capsys.readouterr()
        assert "missing key" in captured.out

    @patch(f"{MODULE}.KaggleApi")
    @patch(f"{MODULE}.os.makedirs")
    def test_makedirs_called_before_api_on_error(self, mock_makedirs, mock_api_cls):
        """Directory must be created even when the API call fails."""
        mock_api_cls.return_value.authenticate.side_effect = Exception("fail")

        _run("data/raw")

        mock_makedirs.assert_called_once_with("data/raw", exist_ok=True)
