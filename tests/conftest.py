import sys
from unittest.mock import MagicMock

# kaggle/__init__.py calls api.authenticate() at import time, which requires
# credentials. Pre-populate sys.modules with a mock so the real package is
# never imported during tests.
_kaggle_mock = MagicMock()
sys.modules.setdefault("kaggle", _kaggle_mock)
sys.modules.setdefault("kaggle.api", _kaggle_mock.api)
sys.modules.setdefault("kaggle.api.kaggle_api_extended", _kaggle_mock.api.kaggle_api_extended)
