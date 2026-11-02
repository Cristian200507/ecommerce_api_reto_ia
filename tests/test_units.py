import pytest
from main import apply_discount


class TestDiscountUnit:
    """Pruebas unitarias para la función independiente de cálculo de descuentos."""

    def test_discount_applied_when_price_strictly_greater_than_100(self):
        """Verifica que un precio mayor a 100 reciba el 10% de descuento."""
        assert apply_discount(200.0) == pytest.approx(180.0)
        assert apply_discount(150.0) == pytest.approx(135.0)

    def test_no_discount_when_price_is_exactly_100(self):
        """Verifica que el umbral límite de 100 no reciba descuento."""
        assert apply_discount(100.0) == 100.0

    def test_no_discount_when_price_is_less_than_100(self):
        """Verifica que precios menores a 100 conserven su valor íntegro."""
        assert apply_discount(99.99) == 99.99
        assert apply_discount(50.0) == 50.0
        assert apply_discount(0.0) == 0.0

    def test_database_get_db_yields_session(self):
        """Verifica que el generador get_db provea y cierre una sesión de base de datos."""
        import database
        gen = database.get_db()
        session = next(gen)
        assert session is not None
        try:
            next(gen)
        except StopIteration:
            pass
