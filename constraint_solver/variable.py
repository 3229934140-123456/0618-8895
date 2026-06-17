from typing import Union


class Variable:
    def __init__(self, name: str = "", value: float = 0.0):
        self.name = name
        self.value = value
        self._hash = id(self)

    def __repr__(self) -> str:
        return f"Var({self.name}={self.value:.3f})"

    def __str__(self) -> str:
        return self.name or f"var_{id(self)}"

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Variable):
            return NotImplemented
        return self is other

    def __add__(self, other: Union["Variable", float, "Expression"]) -> "Expression":
        from .expression import Expression
        if isinstance(other, Expression):
            return Expression({self: 1.0}) + other
        elif isinstance(other, Variable):
            return Expression({self: 1.0, other: 1.0})
        else:
            return Expression({self: 1.0}, float(other))

    def __radd__(self, other: float) -> "Expression":
        from .expression import Expression
        return Expression({self: 1.0}, float(other))

    def __sub__(self, other: Union["Variable", float, "Expression"]) -> "Expression":
        from .expression import Expression
        if isinstance(other, Expression):
            return Expression({self: 1.0}) - other
        elif isinstance(other, Variable):
            return Expression({self: 1.0, other: -1.0})
        else:
            return Expression({self: 1.0}, -float(other))

    def __rsub__(self, other: float) -> "Expression":
        from .expression import Expression
        return Expression({self: -1.0}, float(other))

    def __mul__(self, other: float) -> "Expression":
        from .expression import Expression
        return Expression({self: float(other)})

    def __rmul__(self, other: float) -> "Expression":
        from .expression import Expression
        return Expression({self: float(other)})

    def __truediv__(self, other: float) -> "Expression":
        from .expression import Expression
        return Expression({self: 1.0 / float(other)})

    def __neg__(self) -> "Expression":
        from .expression import Expression
        return Expression({self: -1.0})

    def __le__(self, other: Union["Variable", float, "Expression"]) -> "Constraint":
        from .constraint import Constraint, Relation, Strength
        from .expression import Expression
        expr = Expression({self: 1.0}) - other
        return Constraint(expr, Relation.LE, Strength.REQUIRED)

    def __ge__(self, other: Union["Variable", float, "Expression"]) -> "Constraint":
        from .constraint import Constraint, Relation, Strength
        from .expression import Expression
        expr = other - Expression({self: 1.0})
        return Constraint(expr, Relation.LE, Strength.REQUIRED)

    def __eq__(self, other: Union["Variable", float, "Expression"]) -> "Constraint":
        from .constraint import Constraint, Relation, Strength
        from .expression import Expression
        if isinstance(other, (Variable, Expression, int, float)):
            expr = Expression({self: 1.0}) - other
            return Constraint(expr, Relation.EQ, Strength.REQUIRED)
        return super().__eq__(other)
