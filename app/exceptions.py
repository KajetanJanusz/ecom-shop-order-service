from http import HTTPStatus


class BaseHttpException(Exception):
    code = HTTPStatus.BAD_GATEWAY
    error_code = HTTPStatus.BAD_GATEWAY
    message = HTTPStatus.BAD_GATEWAY.description


class OutOfStockError(BaseHttpException):
    code = HTTPStatus.CONFLICT
    error_code = HTTPStatus.CONFLICT
    message = "Product is out of stock"


class OrderNotFoundError(BaseHttpException):
    code = HTTPStatus.NOT_FOUND
    error_code = HTTPStatus.NOT_FOUND
    message = "Order not found"
