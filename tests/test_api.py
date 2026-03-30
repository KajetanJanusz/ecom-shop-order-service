import uuid
from types import SimpleNamespace

from app.models.order import OrderCurrency


def _mock_order():
    return SimpleNamespace(id=uuid.uuid4(), currency=OrderCurrency.USD, order_items=[])


class TestOrderApi:
    def test_create_order_when_valid_returns_200(self, client, mock_order_service):
        # Arrange
        mock_order_service.create_order.return_value = _mock_order()
        payload = {"product_id": str(uuid.uuid4()), "quantity": 2, "currency": "USD"}

        # Act
        response = client.post("/orders/create", json=payload)

        # Assert
        assert response.status_code == 200

    def test_add_item_when_valid_returns_200(self, client, mock_order_service):
        # Arrange
        mock_order_service.add_order_item.return_value = _mock_order()
        order_id = uuid.uuid4()
        payload = {"product_id": str(uuid.uuid4()), "quantity": 1}

        # Act
        response = client.post(f"/orders/add-item/{order_id}", json=payload)

        # Assert
        assert response.status_code == 200

    def test_remove_item_when_valid_returns_200(self, client, mock_order_service):
        # Arrange
        mock_order_service.remove_order_item.return_value = _mock_order()
        order_id = uuid.uuid4()
        product_id = uuid.uuid4()

        # Act
        response = client.delete(f"/orders/remove-item/{order_id}/{product_id}")

        # Assert
        assert response.status_code == 200

    def test_pay_order_when_valid_returns_200(self, client, mock_order_service):
        # Arrange
        mock_order_service.pay_for_order.return_value = _mock_order()
        order_id = uuid.uuid4()

        # Act
        response = client.post(f"/orders/pay/{order_id}")

        # Assert
        assert response.status_code == 200

    def test_get_order_when_valid_returns_200(self, client, mock_order_service):
        # Arrange
        mock_order_service.get_order.return_value = _mock_order()
        order_id = uuid.uuid4()

        # Act
        response = client.get(f"/orders/details/{order_id}")

        # Assert
        assert response.status_code == 200
