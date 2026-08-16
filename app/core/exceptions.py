from typing import Any, Optional
from fastapi import HTTPException, status


class OtoichiException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.code = code
        self.message = message
        self.details = details


class BadRequestException(OtoichiException):
    def __init__(self, code: str = "BAD_REQUEST", message: str = "Bad request", details: Optional[Any] = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, code=code, message=message, details=details)


class UnauthorizedException(OtoichiException):
    def __init__(self, code: str = "UNAUTHORIZED", message: str = "Authentication required", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=code,
            message=message,
            details=details,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(OtoichiException):
    def __init__(self, code: str = "FORBIDDEN", message: str = "Access forbidden", details: Optional[Any] = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, code=code, message=message, details=details)


class NotFoundException(OtoichiException):
    def __init__(self, code: str = "NOT_FOUND", message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, code=code, message=message, details=details)


class ConflictException(OtoichiException):
    def __init__(self, code: str = "CONFLICT", message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, code=code, message=message, details=details)


class InsufficientStockException(OtoichiException):
    def __init__(self, message: str = "Requested quantity exceeds available stock", details: Optional[Any] = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, code="INSUFFICIENT_STOCK", message=message, details=details)


class InvalidCouponException(OtoichiException):
    def __init__(self, message: str = "Coupon is invalid or cannot be applied", details: Optional[Any] = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, code="INVALID_COUPON", message=message, details=details)


class PaymentFailedException(OtoichiException):
    def __init__(self, message: str = "Payment processing failed", details: Optional[Any] = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, code="PAYMENT_FAILED", message=message, details=details)
