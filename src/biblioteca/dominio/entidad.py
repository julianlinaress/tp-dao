"""Identidad común de las entidades del dominio."""

from dataclasses import dataclass


@dataclass(kw_only=True, eq=False)
class Entidad:
    id: int | None = None

    def __eq__(self, otra: object) -> bool:
        if self is otra:
            return True
        return type(self) is type(otra) and self.id is not None and self.id == otra.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
