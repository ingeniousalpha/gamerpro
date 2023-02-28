from typing import Dict
from dataclasses import dataclass


@dataclass
class CustomError:
    error_id: int
    code: str
    message: str


@dataclass
class CustomResponse:
    data: Dict = None
    error: Dict = None
