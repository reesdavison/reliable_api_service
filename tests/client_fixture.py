# import psycopg
import pytest
from fastapi.testclient import TestClient

# from pytest_mock import MockerFixture
# from sqlalchemy import create_engine


# def create_test_sync_engine(postgresql: psycopg.Connection, echo: bool = True):
#     return create_engine(
#         f"postgresql://{postgresql.info.user}:@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}",
#         echo=echo,
#     )


@pytest.fixture(scope="function")
def client():
    from app.main import app

    return TestClient(app)


# @pytest.fixture
# def alembic_engine(postgresql: psycopg.Connection):
#     """Override this fixture to provide pytest-alembic powered tests with a database handle."""
#     return create_test_sync_engine(postgresql)
