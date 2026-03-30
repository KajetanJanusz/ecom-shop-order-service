from functools import lru_cache

from ecom_shop_shared_lib.brokers.clients.kafka import AsyncKafkaClient
from ecom_shop_shared_lib.brokers.clients.rabbit import AsyncRabbitClient

from core.settings import get_settings
from core.settings.base import Broker

settings = get_settings()


@lru_cache
def get_broker_client() -> AsyncKafkaClient | AsyncRabbitClient:
    broker = settings.broker
    broker_url = settings.broker_url
    group_id = settings.group_id

    if broker == Broker.KAFKA:
        return AsyncKafkaClient(
            broker_url=broker_url,
            group_id=group_id,
        )

    return AsyncRabbitClient(
        broker_url=broker_url,
    )
