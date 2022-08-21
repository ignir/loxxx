from time import time
from typing import TYPE_CHECKING, Any

from loxxx.callable import Callable

if TYPE_CHECKING:
    from loxxx.interpreter import Interpreter


class clock(Callable):
    def call(self, interpreter: 'Interpreter', arguments: list[Any]) -> Any:
        return time()

    @property
    def arity(self) -> int:
        return 0

    def __str__(self):
        return "<native fn>"
