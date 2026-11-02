import pytest
import models


class TestOrdersEndpoints:
    """Pruebas de integración para el procesamiento de pedidos, descuentos y control de inventario."""

    def test_order_success_with_10_percent_discount(self, client, sample_user, sample_products, db_session):
        """Verifica que productos con precio > 100 reciban el 10% de descuento y descuenten stock."""
        p_expensive = sample_products["expensive"]  # Precio: 800.0, Stock: 5
        initial_stock = p_expensive.stock

        payload = {
            "user_id": sample_user.id,
            "product_ids": [p_expensive.id],
        }
        response = client.post("/orders/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "order_id" in data
        # 800.0 * 0.9 = 720.0
        assert data["total"] == pytest.approx(720.0)

        # Verificar decremento de stock en base de datos
        db_session.expire_all()
        prod_updated = db_session.query(models.Product).filter(models.Product.id == p_expensive.id).first()
        assert prod_updated.stock == initial_stock - 1

    def test_order_success_without_discount_for_products_under_100(self, client, sample_user, sample_products, db_session):
        """Verifica que productos con precio <= 100 no reciban descuento."""
        p_cheap = sample_products["cheap"]  # Precio: 20.0, Stock: 10
        p_threshold = sample_products["threshold"]  # Precio: 100.0, Stock: 3

        payload = {
            "user_id": sample_user.id,
            "product_ids": [p_cheap.id, p_threshold.id],
        }
        response = client.post("/orders/", json=payload)

        assert response.status_code == 200
        data = response.json()
        # 20.0 + 100.0 = 120.0
        assert data["total"] == pytest.approx(120.0)

        db_session.expire_all()
        cheap_updated = db_session.query(models.Product).filter(models.Product.id == p_cheap.id).first()
        threshold_updated = db_session.query(models.Product).filter(models.Product.id == p_threshold.id).first()
        assert cheap_updated.stock == 9
        assert threshold_updated.stock == 2

    def test_order_repeated_product_units(self, client, sample_user, sample_products, db_session):
        """Verifica que repetir IDs en product_ids descuente stock acumulado correctamente."""
        p_cheap = sample_products["cheap"]  # Precio: 20.0, Stock: 10

        payload = {
            "user_id": sample_user.id,
            "product_ids": [p_cheap.id, p_cheap.id, p_cheap.id],
        }
        response = client.post("/orders/", json=payload)

        assert response.status_code == 200
        assert response.json()["total"] == pytest.approx(60.0)

        db_session.expire_all()
        prod_updated = db_session.query(models.Product).filter(models.Product.id == p_cheap.id).first()
        assert prod_updated.stock == 7

    def test_order_user_not_found_returns_404(self, client, sample_products):
        """Verifica que ordenar con un user_id inexistente retorne HTTP 404."""
        payload = {
            "user_id": 999999,
            "product_ids": [sample_products["cheap"].id],
        }
        response = client.post("/orders/", json=payload)

        assert response.status_code == 404
        assert response.json()["detail"] == "Usuario no encontrado"

    def test_order_product_not_found_returns_400(self, client, sample_user):
        """Verifica que solicitar un producto que no existe retorne HTTP 400 con su ID."""
        payload = {
            "user_id": sample_user.id,
            "product_ids": [88888],
        }
        response = client.post("/orders/", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "Producto 88888 no existe"

    def test_order_insufficient_stock_zero_returns_400(self, client, sample_user, sample_products):
        """Verifica que solicitar un producto con stock 0 retorne HTTP 400 de stock insuficiente."""
        p_out = sample_products["out_of_stock"]  # Stock: 0

        payload = {
            "user_id": sample_user.id,
            "product_ids": [p_out.id],
        }
        response = client.post("/orders/", json=payload)

        assert response.status_code == 400
        assert "Stock insuficiente" in response.json()["detail"]

    def test_order_insufficient_stock_exceeding_available_units(self, client, sample_user, db_session):
        """Verifica que pedir más unidades del stock disponible aborte la transacción con HTTP 400."""
        # Producto con stock de solo 1 unidad
        limited_prod = models.Product(name="Última Unidad", price=50.0, stock=1)
        db_session.add(limited_prod)
        db_session.commit()
        db_session.refresh(limited_prod)

        # Solicitar 2 unidades
        payload = {
            "user_id": sample_user.id,
            "product_ids": [limited_prod.id, limited_prod.id],
        }
        response = client.post("/orders/", json=payload)

        assert response.status_code == 400
        assert "Stock insuficiente" in response.json()["detail"]

        # Verificar que el stock original permanezca intacto (sin persistir decrementos parciales)
        db_session.expire_all()
        prod_check = db_session.query(models.Product).filter(models.Product.id == limited_prod.id).first()
        assert prod_check.stock == 1

    def test_order_empty_product_ids_creates_order_with_total_zero(self, client, sample_user):
        """Verifica el comportamiento cuando la lista de product_ids está vacía."""
        payload = {
            "user_id": sample_user.id,
            "product_ids": [],
        }
        response = client.post("/orders/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["total"] == 0
