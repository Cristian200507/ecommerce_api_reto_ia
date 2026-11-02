import models


class TestProductsEndpoints:
    """Pruebas de integración para catálogo de productos y paginación."""

    def test_get_products_empty_catalog(self, client):
        """Verifica que un catálogo sin productos devuelva una lista vacía con status 200."""
        response = client.get("/products/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_products_returns_catalog(self, client, sample_products):
        """Verifica que el catálogo devuelva los productos creados."""
        response = client.get("/products/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        names = [item["name"] for item in data]
        assert "Smartphone Pro" in names
        assert "Funda Protectora" in names

    def test_default_pagination_limits_to_10_products(self, client, db_session):
        """Verifica que por defecto el límite de resultados sea de 10 productos."""
        # Crear 15 productos
        products = [
            models.Product(name=f"Producto {i}", price=10.0 + i, stock=5)
            for i in range(15)
        ]
        db_session.add_all(products)
        db_session.commit()

        response = client.get("/products/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        assert data[0]["name"] == "Producto 0"
        assert data[9]["name"] == "Producto 9"

    def test_custom_pagination_limit_and_offset(self, client, db_session):
        """Verifica el funcionamiento correcto de los parámetros personalizados limit y offset."""
        products = [
            models.Product(name=f"Item {i:02d}", price=10.0, stock=5)
            for i in range(12)
        ]
        db_session.add_all(products)
        db_session.commit()

        # Solicitar 4 elementos a partir del índice 3 (offset=3)
        response = client.get("/products/?limit=4&offset=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert data[0]["name"] == "Item 03"
        assert data[3]["name"] == "Item 06"

    def test_max_limit_allowed_is_100(self, client):
        """Verifica que solicitar exactamente el límite máximo de 100 sea válido."""
        response = client.get("/products/?limit=100")
        assert response.status_code == 200

    def test_limit_exceeding_100_returns_422(self, client):
        """Verifica que un limit mayor a 100 sea rechazado con HTTP 422."""
        response = client.get("/products/?limit=101")
        assert response.status_code == 422

    def test_limit_below_minimum_returns_422(self, client):
        """Verifica que un limit menor a 1 sea rechazado con HTTP 422."""
        response = client.get("/products/?limit=0")
        assert response.status_code == 422

        response = client.get("/products/?limit=-10")
        assert response.status_code == 422

    def test_negative_offset_returns_422(self, client):
        """Verifica que un offset negativo sea rechazado con HTTP 422."""
        response = client.get("/products/?offset=-1")
        assert response.status_code == 422
