import pytest
from sqlmodel import Field, create_engine, SQLModel
from sqlmodel_toolkit.model import Model


class User(Model):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    active: bool = True


@pytest.fixture(autouse=True)
def engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    Model.set_engine(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def user():
    return User.create(name="Alice", email="alice@example.com", active=True)


@pytest.fixture
def inactive_user():
    return User.create(name="Bob", email="bob@example.com", active=False)
