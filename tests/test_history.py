import models


class TestUserOrdersHistory:
    """Pruebas de integración para la consulta del historial de pedidos de un usuario."""

    def test_get_orders_user_not_found_returns_404(self, client):
        """Verifica que consultar el historial de un usuario inexistente retorne HTTP 404."""
        response = client.get("/users/999999/orders")
        assert response.status_code == 404
        assert response.json()["detail"] == "Usuario no encontrado"

    def test_get_orders_user_without_orders_returns_empty_list(self, client, sample_user):
        """Verifica que un usuario existente sin pedidos retorne una lista vacía con HTTP 200."""
        response = client.get(f"/users/{sample_user.id}/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_orders_returns_user_order_history(self, client, sample_user, sample_products):
        """Verifica que se listen los pedidos del usuario con ID, total y productos."""
        p_cheap = sample_products["cheap"]

        # Crear un pedido a través del endpoint de órdenes
        order_payload = {
            "user_id": sample_user.id,
            "product_ids": [p_cheap.id],
        }
        order_response = client.post("/orders/", json=order_payload)
        assert order_response.status_code == 200
        order_id = order_response.json()["order_id"]

        # Consultar historial del usuario
        response = client.get(f"/users/{sample_user.id}/orders")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["order_id"] == order_id
        assert data[0]["total"] == 20.0
        assert "products" in data[0]
        assert isinstance(data[0]["products"], list)

    def test_get_orders_isolation_between_multiple_users(self, client, sample_products, db_session):
        """Verifica que cada usuario consulte únicamente sus propios pedidos."""
        # Crear dos usuarios
        user_a = models.User(name="Usuario A", email="user_a@example.com")
        user_b = models.User(name="Usuario B", email="user_b@example.com")
        db_session.add_all([user_a, user_b])
        db_session.commit()
        db_session.refresh(user_a)
        db_session.refresh(user_b)

        p = sample_products["cheap"]

        # 1 pedido para usuario A
        client.post("/orders/", json={"user_id": user_a.id, "product_ids": [p.id]})

        # 2 pedidos para usuario B
        client.post("/orders/", json={"user_id": user_b.id, "product_ids": [p.id]})
        client.post("/orders/", json={"user_id": user_b.id, "product_ids": [p.id]})

        # Validar historial usuario A
        res_a = client.get(f"/users/{user_a.id}/orders")
        assert res_a.status_code == 200
        assert len(res_a.json()) == 1

        # Validar historial usuario B
        res_b = client.get(f"/users/{user_b.id}/orders")
        assert res_b.status_code == 200
        assert len(res_b.json()) == 2
