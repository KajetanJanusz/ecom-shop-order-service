import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.models.order import OrderCurrency


class OrderItemSchema(BaseModel):
    product_id: uuid.UUID
    quantity: int


class CreateOrderRequestSchema(OrderItemSchema):
    currency: OrderCurrency


class OrderItemCreateSchema(OrderItemSchema):
    order_id: uuid.UUID
    price: Decimal


class OrderItemDetailsSchema(OrderItemCreateSchema):
    pass


class OrderCreateSchema(BaseModel):
    owner_id: uuid.UUID
    currency: OrderCurrency


class OrderDetailsSchema(BaseModel):
    id: uuid.UUID
    currency: OrderCurrency
    order_items: list[OrderItemDetailsSchema]

    model_config = {"from_attributes": True}


class RemoveOrderItemSchema(BaseModel):
    product_id: uuid.UUID


class PaymentSchema(BaseModel):
    order_id: str
    payment_link: str
