import models


class TestUsersEndpoints:
    """Pruebas de integración para los endpoints de usuarios."""

    def test_create_user_success(self, client, db_session):
        """Verifica la creación exitosa de un usuario y su persistencia en base de datos."""
        payload = {"name": "Ana Lopez", "email": "ana@example.com"}
        response = client.post("/users/", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["email"] == payload["email"]
        assert "id" in data
        assert isinstance(data["id"], int)

        # Verificación directa en base de datos
        db_user = db_session.query(models.User).filter(models.User.email == payload["email"]).first()
        assert db_user is not None
        assert db_user.name == "Ana Lopez"

    def test_create_user_duplicate_email_returns_409(self, client, sample_user):
        """Verifica que intentar registrar un email existente devuelva error HTTP 409."""
        payload = {"name": "Otro Nombre", "email": sample_user.email}
        response = client.post("/users/", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert data["detail"] == "El correo electrónico ya se encuentra registrado"

    def test_create_user_missing_required_fields_returns_422(self, client):
        """Verifica que cargas útiles incompletas devuelvan error de validación 422."""
        # Sin email
        response = client.post("/users/", json={"name": "Sin Correo"})
        assert response.status_code == 422

        # Sin nombre
        response = client.post("/users/", json={"email": "sinnombre@example.com"})
        assert response.status_code == 422

        # Objeto vacío
        response = client.post("/users/", json={})
        assert response.status_code == 422
