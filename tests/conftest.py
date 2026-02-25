"""Test configuration — set required environment variables before imports."""

import os

os.environ.setdefault("API_SECRET_KEY", "test_secret_key_for_testing")
