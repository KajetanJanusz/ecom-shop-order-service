import uuid
from datetime import datetime, timezone

from ecom_shop_shared_lib.brokers.events.order_service.events import OrderServiceEvents
from ecom_shop_shared_lib.models import EventStatus
from ecom_shop_shared_lib.schemas.outbox import OutboxSchema
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.session import get_session
from app.exceptions import OutOfStockError
from app.models.outbox import Outbox
from app.models.order import Order, OrderItem, ProductSnapshot
from app.schemas.order import (
    CreateOrderRequestSchema,
    OrderItemSchema,
    OrderItemCreateSchema,
    OrderCreateSchema,
)
from ecom_shop_shared_lib.repositories.base import AsyncBaseRepository, ModelFields


class OrderService:
    def __init__(
        self,
        db_session: AsyncSession,
        order_repository: AsyncBaseRepository[Order],
        order_item_repository: AsyncBaseRepository[OrderItem],
        product_repository: AsyncBaseRepository[ProductSnapshot],
        outbox_repository: AsyncBaseRepository[Outbox],
    ):
        self.db_session = db_session
        self.order_repository = order_repository
        self.order_item_repository = order_item_repository
        self.product_repository = product_repository
        self.outbox_repository = outbox_repository

    async def create_order(
        self, create_order_data: CreateOrderRequestSchema, user_id: uuid.UUID
    ) -> Order:
        product = await self.product_repository.get_one(
            filter_fields=[
                ModelFields(
                    field=ProductSnapshot.id, value=create_order_data.product_id
                )
            ]
        )

        if product.stock < create_order_data.quantity:
            raise OutOfStockError

        order_create_data = OrderCreateSchema(
            owner_id=user_id, currency=create_order_data.currency
        )
        order = await self.order_repository.create(schema=order_create_data)

        order_item_create_data = OrderItemCreateSchema(
            order_id=order.id,
            product_id=product.id,
            quantity=create_order_data.quantity,
            price=product.price,
        )
        await self.order_item_repository.create(schema=order_item_create_data)

        await self.outbox_repository.create(
            schema=OutboxSchema(
                event_topic=OrderServiceEvents.ORDER_CREATED.topic,
                payload=OrderServiceEvents.ORDER_CREATED.schema(
                    id=order.id, created_at=order.created_at
                ).model_dump(),
                status=EventStatus.UNPROCESSED,
            )
        )
        return await self.order_repository.get_one(
            filter_fields=[ModelFields(field=Order.id, value=order.id)],
            joins=[Order.order_items],
        )

    async def add_order_item(
        self, order_item_data: OrderItemSchema, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> Order:
        order = await self.order_repository.get_one(
            filter_fields=[ModelFields(field=Order.id, value=order_id)]
        )
        if order.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        product = await self.product_repository.get_one(
            filter_fields=[
                ModelFields(field=ProductSnapshot.id, value=order_item_data.product_id)
            ]
        )

        is_item_in_order = await self.order_item_repository.exists(
            filter_fields=[
                ModelFields(field=OrderItem.order_id, value=order_id),
                ModelFields(
                    field=OrderItem.product_id, value=order_item_data.product_id
                ),
            ]
        )

        if is_item_in_order:
            order_item = await self.order_item_repository.get_one(
                filter_fields=[
                    ModelFields(field=OrderItem.order_id, value=order_id),
                    ModelFields(
                        field=OrderItem.product_id, value=order_item_data.product_id
                    ),
                ]
            )
            new_quantity = order_item.quantity + order_item_data.quantity

            if product.stock < new_quantity:
                raise OutOfStockError

            await self.order_item_repository.update_one(
                model=order_item,
                update_fields=[
                    ModelFields(field=OrderItem.quantity, value=new_quantity)
                ],
            )
        else:
            if product.stock < order_item_data.quantity:
                raise OutOfStockError

            order_item_create_data = OrderItemCreateSchema(
                order_id=order_id,
                product_id=product.id,
                quantity=order_item_data.quantity,
                price=product.price,
            )
            await self.order_item_repository.create(schema=order_item_create_data)

        return await self.order_repository.get_one(
            filter_fields=[ModelFields(field=Order.id, value=order_id)],
            joins=[Order.order_items],
        )

    async def remove_order_item(
        self, product_id: uuid.UUID, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> Order:
        order = await self.order_repository.get_one(
            filter_fields=[ModelFields(field=Order.id, value=order_id)]
        )
        if order.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        order_item = await self.order_item_repository.get_one(
            filter_fields=[
                ModelFields(field=OrderItem.order_id, value=order_id),
                ModelFields(field=OrderItem.product_id, value=product_id),
            ]
        )
        await self.order_item_repository.delete_one(model=order_item)
        return await self.order_repository.get_one(
            filter_fields=[ModelFields(field=Order.id, value=order_id)],
            joins=[Order.order_items],
        )

    async def pay_for_order(self, order_id: uuid.UUID, user_id: uuid.UUID) -> Order:
        order = await self.order_repository.get_one(
            filter_fields=[ModelFields(field=Order.id, value=order_id)],
            joins=[Order.order_items],
        )
        if order.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        await self.outbox_repository.create(
            schema=OutboxSchema(
                event_topic=OrderServiceEvents.ORDER_PAID.topic,
                payload=OrderServiceEvents.ORDER_PAID.schema(
                    id=order.id,
                    amount=order.total_price,
                    currency="USD",
                    paid_at=datetime.now(timezone.utc),
                ).model_dump(),
                status=EventStatus.UNPROCESSED,
            )
        )
        return order

    async def get_order(self, order_id: uuid.UUID, user_id: uuid.UUID) -> Order:
        order = await self.order_repository.get_one(
            filter_fields=[ModelFields(field=Order.id, value=order_id)],
            joins=[Order.order_items],
        )
        if order.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        return order


async def get_order_service(
    db_session: AsyncSession = Depends(get_session),
) -> OrderService:
    return OrderService(
        db_session=db_session,
        order_repository=AsyncBaseRepository(model_class=Order, db_session=db_session),
        order_item_repository=AsyncBaseRepository(
            model_class=OrderItem, db_session=db_session
        ),
        product_repository=AsyncBaseRepository(
            model_class=ProductSnapshot, db_session=db_session
        ),
        outbox_repository=AsyncBaseRepository(
            model_class=Outbox, db_session=db_session
        ),
    )
