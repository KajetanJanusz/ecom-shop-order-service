import asyncio
import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.exceptions import OutOfStockError
from app.schemas.order import CreateOrderRequestSchema, OrderItemSchema
from app.models.order import OrderCurrency
from tests.models import OrderFactory, OrderItemFactory, ProductSnapshotFactory


class TestOrderService:
    def test_create_order_when_stock_sufficient_creates_order(
        self,
        order_service,
        mock_order_repo,
        mock_product_repo,
        mock_order_item_repo,
        mock_outbox_repo,
    ):
        # Arrange
        product = ProductSnapshotFactory.build(stock=10, price=Decimal("25.00"))
        order = OrderFactory.build()
        mock_product_repo.get_one.return_value = product
        mock_order_repo.create.return_value = order
        mock_order_repo.get_one.return_value = order
        order_item_data = CreateOrderRequestSchema(
            product_id=product.id, quantity=2, currency=OrderCurrency.USD
        )

        # Act
        result = asyncio.run(
            order_service.create_order(
                create_order_data=order_item_data, user_id=uuid.uuid4()
            )
        )

        # Assert
        assert result == order
        mock_order_repo.create.assert_called_once()
        mock_order_item_repo.create.assert_called_once()
        mock_outbox_repo.create.assert_called_once()

    def test_create_order_when_stock_insufficient_raises(
        self, order_service, mock_product_repo
    ):
        # Arrange
        product = ProductSnapshotFactory.build(stock=1)
        mock_product_repo.get_one.return_value = product
        order_item_data = CreateOrderRequestSchema(
            product_id=product.id, quantity=5, currency=OrderCurrency.USD
        )

        # Act / Assert
        with pytest.raises(OutOfStockError):
            asyncio.run(
                order_service.create_order(
                    create_order_data=order_item_data, user_id=uuid.uuid4()
                )
            )

    def test_add_order_item_when_item_new_creates_item(
        self, order_service, mock_order_repo, mock_product_repo, mock_order_item_repo
    ):
        # Arrange
        user_id = uuid.uuid4()
        order_id = uuid.uuid4()
        product = ProductSnapshotFactory.build(stock=10)
        order = OrderFactory.build(owner_id=user_id)
        mock_product_repo.get_one.return_value = product
        mock_order_item_repo.exists.return_value = False
        mock_order_repo.get_one.return_value = order
        order_item_data = OrderItemSchema(product_id=product.id, quantity=3)

        # Act
        result = asyncio.run(
            order_service.add_order_item(
                order_item_data=order_item_data, order_id=order_id, user_id=user_id
            )
        )

        # Assert
        assert result == order
        mock_order_item_repo.create.assert_called_once()
        mock_order_item_repo.update_one.assert_not_called()

    def test_add_order_item_when_item_exists_updates_quantity(
        self, order_service, mock_order_repo, mock_product_repo, mock_order_item_repo
    ):
        # Arrange
        user_id = uuid.uuid4()
        order_id = uuid.uuid4()
        product = ProductSnapshotFactory.build(stock=20)
        existing_item = OrderItemFactory.build(order_id=order_id, quantity=3)
        order = OrderFactory.build(owner_id=user_id)
        mock_product_repo.get_one.return_value = product
        mock_order_item_repo.exists.return_value = True
        mock_order_item_repo.get_one.return_value = existing_item
        mock_order_item_repo.update_one.return_value = existing_item
        mock_order_repo.get_one.return_value = order
        order_item_data = OrderItemSchema(product_id=product.id, quantity=5)

        # Act
        result = asyncio.run(
            order_service.add_order_item(
                order_item_data=order_item_data, order_id=order_id, user_id=user_id
            )
        )

        # Assert
        assert result == order
        mock_order_item_repo.update_one.assert_called_once()
        mock_order_item_repo.create.assert_not_called()

    def test_add_order_item_when_existing_plus_new_exceeds_stock_raises(
        self, order_service, mock_order_repo, mock_product_repo, mock_order_item_repo
    ):
        # Arrange
        user_id = uuid.uuid4()
        product = ProductSnapshotFactory.build(stock=5)
        existing_item = OrderItemFactory.build(quantity=3)
        order = OrderFactory.build(owner_id=user_id)
        mock_product_repo.get_one.return_value = product
        mock_order_item_repo.exists.return_value = True
        mock_order_item_repo.get_one.return_value = existing_item
        mock_order_repo.get_one.return_value = order
        order_item_data = OrderItemSchema(
            product_id=product.id, quantity=4
        )  # 3 + 4 = 7 > 5

        # Act / Assert
        with pytest.raises(OutOfStockError):
            asyncio.run(
                order_service.add_order_item(
                    order_item_data=order_item_data,
                    order_id=uuid.uuid4(),
                    user_id=user_id,
                )
            )

    def test_add_order_item_when_wrong_user_raises_403(
        self, order_service, mock_order_repo, mock_product_repo, mock_order_item_repo
    ):
        # Arrange
        order = OrderFactory.build()  # random owner_id
        mock_order_repo.get_one.return_value = order
        order_item_data = OrderItemSchema(product_id=uuid.uuid4(), quantity=1)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                order_service.add_order_item(
                    order_item_data=order_item_data,
                    order_id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                )
            )

        assert exc_info.value.status_code == 403

    def test_remove_order_item_deletes_item_and_returns_order(
        self, order_service, mock_order_repo, mock_order_item_repo
    ):
        # Arrange
        user_id = uuid.uuid4()
        order_id = uuid.uuid4()
        product_id = uuid.uuid4()
        order_item = OrderItemFactory.build(order_id=order_id, product_id=product_id)
        order = OrderFactory.build(owner_id=user_id)
        mock_order_item_repo.get_one.return_value = order_item
        mock_order_repo.get_one.return_value = order

        # Act
        result = asyncio.run(
            order_service.remove_order_item(
                product_id=product_id, order_id=order_id, user_id=user_id
            )
        )

        # Assert
        assert result == order
        mock_order_item_repo.delete_one.assert_called_once_with(model=order_item)

    def test_remove_order_item_when_wrong_user_raises_403(
        self, order_service, mock_order_repo, mock_order_item_repo
    ):
        # Arrange
        order = OrderFactory.build()  # random owner_id
        mock_order_repo.get_one.return_value = order

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                order_service.remove_order_item(
                    product_id=uuid.uuid4(), order_id=uuid.uuid4(), user_id=uuid.uuid4()
                )
            )

        assert exc_info.value.status_code == 403

    def test_pay_order_emits_outbox_event_and_returns_order(
        self, order_service, mock_order_repo, mock_outbox_repo
    ):
        # Arrange
        user_id = uuid.uuid4()
        order_id = uuid.uuid4()
        item = OrderItemFactory.build(quantity=2, price=Decimal("15.00"))
        order = OrderFactory.build(id=order_id, owner_id=user_id)
        order.order_items = [item]
        mock_order_repo.get_one.return_value = order

        # Act
        result = asyncio.run(
            order_service.pay_for_order(order_id=order_id, user_id=user_id)
        )

        # Assert
        assert result == order
        mock_outbox_repo.create.assert_called_once()

    def test_pay_order_when_wrong_user_raises_403(self, order_service, mock_order_repo):
        # Arrange
        item = OrderItemFactory.build(quantity=1, price=Decimal("10.00"))
        order = OrderFactory.build()  # random owner_id
        order.order_items = [item]
        mock_order_repo.get_one.return_value = order

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                order_service.pay_for_order(order_id=uuid.uuid4(), user_id=uuid.uuid4())
            )

        assert exc_info.value.status_code == 403

    def test_get_order_returns_order_with_items(self, order_service, mock_order_repo):
        # Arrange
        user_id = uuid.uuid4()
        order_id = uuid.uuid4()
        order = OrderFactory.build(id=order_id, owner_id=user_id)
        mock_order_repo.get_one.return_value = order

        # Act
        result = asyncio.run(
            order_service.get_order(order_id=order_id, user_id=user_id)
        )

        # Assert
        assert result == order
        mock_order_repo.get_one.assert_called_once()

    def test_get_order_when_wrong_user_raises_403(self, order_service, mock_order_repo):
        # Arrange
        order = OrderFactory.build()  # random owner_id
        mock_order_repo.get_one.return_value = order

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                order_service.get_order(order_id=uuid.uuid4(), user_id=uuid.uuid4())
            )

        assert exc_info.value.status_code == 403
