import datetime
import uuid
from decimal import Decimal

from factory import LazyFunction
from factory.alchemy import SQLAlchemyModelFactory

from app.models.order import Order, OrderItem, ProductSnapshot, OrderCurrency


class OrderFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Order
        sqlalchemy_session = None

    id = LazyFunction(uuid.uuid4)
    owner_id = LazyFunction(uuid.uuid4)
    currency = OrderCurrency.USD
    created_at = LazyFunction(datetime.datetime.now)
    updated_at = LazyFunction(datetime.datetime.now)


class OrderItemFactory(SQLAlchemyModelFactory):
    class Meta:
        model = OrderItem
        sqlalchemy_session = None

    id = LazyFunction(uuid.uuid4)
    order_id = LazyFunction(uuid.uuid4)
    product_id = LazyFunction(uuid.uuid4)
    quantity = 1
    price = Decimal("10.00")
    created_at = LazyFunction(datetime.datetime.now)
    updated_at = LazyFunction(datetime.datetime.now)


class ProductSnapshotFactory(SQLAlchemyModelFactory):
    class Meta:
        model = ProductSnapshot
        sqlalchemy_session = None

    id = LazyFunction(uuid.uuid4)
    product_id = LazyFunction(uuid.uuid4)
    stock = 100
    price = Decimal("10.00")
    created_at = LazyFunction(datetime.datetime.now)
    updated_at = LazyFunction(datetime.datetime.now)
