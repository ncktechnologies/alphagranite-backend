from pydantic.generics import GenericModel
from typing import TypeVar, Generic, Optional


T = TypeVar("T")


class SuccessResponse(GenericModel, Generic[T]):
    """Generic success wrapper used across the API.

    Fields:
    - success: always True for successful responses
    - message: a human readable message
    - data: the payload (can be None)
    """

    success: bool = True
    message: str
    data: Optional[T] = None
