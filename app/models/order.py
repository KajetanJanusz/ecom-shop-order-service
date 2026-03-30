import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, UUID, Integer, DECIMAL, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecom_shop_shared_lib.models.base_mixin import BaseDbModelMixin
from core.db.session import Base


class OrderCurrency(StrEnum):
    USD = "USD"
    PLN = "PLN"
    EUR = "EUR"


class Order(Base, BaseDbModelMixin):
    __tablename__ = "orders"

    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    currency: Mapped[OrderCurrency] = mapped_column(
        Enum(OrderCurrency), nullable=False, default=OrderCurrency.USD
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    @property
    def total_price(self) -> Decimal:
        return sum(
            (item.total_item_price for item in self.order_items), start=Decimal(0)
        )


class OrderItem(Base, BaseDbModelMixin):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    order: Mapped["Order"] = relationship(back_populates="order_items")

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[Decimal] = mapped_column(DECIMAL, nullable=False)

    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_order_product"),
    )

    @property
    def total_item_price(self) -> Decimal:
        return (self.quantity * self.price) or Decimal('0.00')


class ProductSnapshot(Base, BaseDbModelMixin):
    __tablename__ = "product_snapshots"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False
    )
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL, nullable=False)
