import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configuración de base de datos aislada en memoria para pruebas
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import database
import models
from main import app

# Motor de prueba SQLite en memoria con StaticPool para compartir conexión entre hilos
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def db_session():
    """Crea un esquema de base de datos nuevo para cada prueba y lo destruye al finalizar."""
    models.Base.metadata.create_all(bind=engine_test)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        models.Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session):
    """Cliente de pruebas TestClient con la dependencia get_db sobreescrita hacia la BD aislada."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[database.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session):
    """Crea un usuario inicial en la base de datos de prueba."""
    user = models.User(name="Carlos Gomez", email="carlos@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_products(db_session):
    """Crea un conjunto variado de productos para probar precios, descuentos y stock."""
    p_expensive = models.Product(name="Smartphone Pro", price=800.0, stock=5)
    p_cheap = models.Product(name="Funda Protectora", price=20.0, stock=10)
    p_threshold = models.Product(name="Audífonos Bluetooth", price=100.0, stock=3)
    p_out_of_stock = models.Product(name="Accesorio Agotado", price=50.0, stock=0)
    
    db_session.add_all([p_expensive, p_cheap, p_threshold, p_out_of_stock])
    db_session.commit()
    
    for p in (p_expensive, p_cheap, p_threshold, p_out_of_stock):
        db_session.refresh(p)

    return {
        "expensive": p_expensive,
        "cheap": p_cheap,
        "threshold": p_threshold,
        "out_of_stock": p_out_of_stock,
    }
