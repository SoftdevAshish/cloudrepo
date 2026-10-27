import os

os.environ["DATABASE_URL"] = "sqlite://"  # tests run without Postgres

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def override_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def test_crud_flow():
    r = client.post("/items", json={"name": "pen", "price": 1.5})
    assert r.status_code == 201
    item_id = r.json()["id"]

    assert client.get(f"/items/{item_id}").json()["name"] == "pen"
    assert len(client.get("/items").json()) == 1

    r = client.patch(f"/items/{item_id}", json={"price": 2})
    assert r.json()["price"] == 2 and r.json()["name"] == "pen"

    assert client.delete(f"/items/{item_id}").status_code == 204
    assert client.get(f"/items/{item_id}").status_code == 404


def test_validation():
    assert client.post("/items", json={"name": ""}).status_code == 422
