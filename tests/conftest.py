import pytest
from database.connection import init_db

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
