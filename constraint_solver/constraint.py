from enum import Enum
from typing import Union
from .expression import Expression
from .variable import Variable


class Relation(Enum):
    LE = "<="
    GE = ">="
    EQ = "=="


class Strength:
    REQUIRED = 1e9
    STRONG = 1e6
    MEDIUM = 1e3
    WEAK = 1.0

    @staticmethod
    def is_required(strength: float) -> bool:
        return strength >= Strength.REQUIRED - 1e-6

    @staticmethod
    def name(strength: float) -> str:
        if strength >= Strength.REQUIRED - 1e-6:
            return "REQUIRED"
        elif strength >= Strength.STRONG - 1e-6:
            return "STRONG"
        elif strength >= Strength.MEDIUM - 1e-6:
            return "MEDIUM"
        else:
            return "WEAK"


class Constraint:
    def __init__(self, expression: Expression, relation: Relation, strength: float = Strength.REQUIRED):
        if isinstance(expression, (int, float)):
            expression = Expression(constant=float(expression))
        elif isinstance(expression, Variable):
            expression = Expression({expression: 1.0})

        self.expression = expression
        self.relation = relation
        self.strength = strength
        self._hash = id(self)

        if relation == Relation.GE:
            self.expression = -expression
            self.relation = Relation.LE

    def __repr__(self) -> str:
        rel_str = self.relation.value
        strength_name = Strength.name(self.strength)
        return f"Constraint({self.expression} {rel_str} 0, strength={strength_name})"

    def __str__(self) -> str:
        return self.__repr__()

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Constraint):
            return NotImplemented
        return self is other

    def is_required(self) -> bool:
        return Strength.is_required(self.strength)

    def is_inequality(self) -> bool:
        return self.relation == Relation.LE

    def with_strength(self, strength: float) -> "Constraint":
        return Constraint(self.expression, self.relation, strength)
