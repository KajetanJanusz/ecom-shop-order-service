import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import user_router
from app.dependencies.auth import get_current_user, UserInfo
from app.services.order import OrderService, get_order_service


@pytest.fixture
def mock_order_repo():
    return AsyncMock()


@pytest.fixture
def mock_order_item_repo():
    return AsyncMock()


@pytest.fixture
def mock_product_repo():
    return AsyncMock()


@pytest.fixture
def mock_outbox_repo():
    return AsyncMock()


@pytest.fixture
def order_service(
    mock_order_repo, mock_order_item_repo, mock_product_repo, mock_outbox_repo
):
    service = object.__new__(OrderService)
    service.db_session = MagicMock()
    service.order_repository = mock_order_repo
    service.order_item_repository = mock_order_item_repo
    service.product_repository = mock_product_repo
    service.outbox_repository = mock_outbox_repo
    return service


@pytest.fixture
def mock_user_info():
    return UserInfo(user_id=str(uuid.uuid4()), admin=False)


@pytest.fixture
def mock_order_service():
    return AsyncMock()


@pytest.fixture
def client(mock_order_service, mock_user_info):
    test_app = FastAPI()
    test_app.include_router(user_router)
    test_app.dependency_overrides[get_order_service] = lambda: mock_order_service
    test_app.dependency_overrides[get_current_user] = lambda: mock_user_info
    yield TestClient(test_app, raise_server_exceptions=False)
