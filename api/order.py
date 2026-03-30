import uuid
from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends

from app.dependencies.auth import get_current_user, UserInfo
from app.schemas.order import (
    OrderItemSchema,
    OrderDetailsSchema,
    CreateOrderRequestSchema,
)
from app.services.order import OrderService, get_order_service

user_router = APIRouter(prefix="/orders", tags=["orders"])


@user_router.post(
    "/create",
    tags=["order"],
    summary="Create new order for user",
    response_model=OrderDetailsSchema,
)
async def create_order(
    order_data: CreateOrderRequestSchema,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    user_info: Annotated[UserInfo, Depends(get_current_user)],
) -> OrderDetailsSchema:
    order = await order_service.create_order(
        create_order_data=order_data,
        user_id=uuid.UUID(user_info.user_id),
    )
    return OrderDetailsSchema.model_validate(order)


@user_router.post(
    "/add-item/{order_id}",
    tags=["order"],
    summary="Add product to order",
    response_model=OrderDetailsSchema,
)
async def add_item_to_order(
    order_data: OrderItemSchema,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    user_info: Annotated[UserInfo, Depends(get_current_user)],
    order_id: uuid.UUID,
) -> OrderDetailsSchema:
    order = await order_service.add_order_item(
        order_item_data=order_data,
        order_id=order_id,
        user_id=uuid.UUID(user_info.user_id),
    )
    return OrderDetailsSchema.model_validate(order)


@user_router.delete(
    "/remove-item/{order_id}/{product_id}",
    tags=["order"],
    summary="Remove item from order",
    response_model=OrderDetailsSchema,
)
async def remove_item_from_order(
    order_service: Annotated[OrderService, Depends(get_order_service)],
    user_info: Annotated[UserInfo, Depends(get_current_user)],
    order_id: uuid.UUID,
    product_id: uuid.UUID,
) -> OrderDetailsSchema:
    order = await order_service.remove_order_item(
        product_id=product_id,
        order_id=order_id,
        user_id=uuid.UUID(user_info.user_id),
    )
    return OrderDetailsSchema.model_validate(order)


@user_router.post(
    "/pay/{order_id}",
    tags=["order"],
    summary="Pay for order",
    response_model=OrderDetailsSchema,
)
async def pay_for_order(
    order_service: Annotated[OrderService, Depends(get_order_service)],
    user_info: Annotated[UserInfo, Depends(get_current_user)],
    order_id: uuid.UUID,
) -> OrderDetailsSchema:
    order = await order_service.pay_for_order(
        order_id=order_id, user_id=uuid.UUID(user_info.user_id)
    )
    return OrderDetailsSchema.model_validate(order)


@user_router.get(
    "/details/{order_id}",
    tags=["order"],
    summary="Get order details",
    response_model=OrderDetailsSchema,
)
async def get_order_details(
    order_service: Annotated[OrderService, Depends(get_order_service)],
    user_info: Annotated[UserInfo, Depends(get_current_user)],
    order_id: uuid.UUID,
) -> OrderDetailsSchema:
    order = await order_service.get_order(
        order_id=order_id, user_id=uuid.UUID(user_info.user_id)
    )
    return OrderDetailsSchema.model_validate(order)
