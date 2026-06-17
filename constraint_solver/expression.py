from typing import Dict, Union, Set
from .variable import Variable


class Expression:
    def __init__(self, terms: Dict[Variable, float] = None, constant: float = 0.0):
        self.terms: Dict[Variable, float] = {}
        self.constant = constant
        if terms:
            for var, coeff in terms.items():
                if abs(coeff) > 1e-10:
                    self.terms[var] = coeff

    def __repr__(self) -> str:
        parts = []
        for var, coeff in self.terms.items():
            if parts:
                sign = '+' if coeff >= 0 else '-'
                parts.append(f"{sign} {abs(coeff):.3f}*{var}")
            else:
                parts.append(f"{coeff:.3f}*{var}")
        if self.constant != 0 or not parts:
            if parts:
                sign = '+' if self.constant >= 0 else '-'
                parts.append(f"{sign} {abs(self.constant):.3f}")
            else:
                parts.append(f"{self.constant:.3f}")
        return " ".join(parts)

    def __str__(self) -> str:
        return self.__repr__()

    def variables(self) -> Set[Variable]:
        return set(self.terms.keys())

    def is_constant(self) -> bool:
        return len(self.terms) == 0

    def evaluate(self) -> float:
        result = self.constant
        for var, coeff in self.terms.items():
            result += coeff * var.value
        return result

    def __add__(self, other: Union["Expression", Variable, float]) -> "Expression":
        result = Expression(self.terms.copy(), self.constant)
        if isinstance(other, Expression):
            for var, coeff in other.terms.items():
                result.terms[var] = result.terms.get(var, 0.0) + coeff
                if abs(result.terms[var]) < 1e-10:
                    del result.terms[var]
            result.constant += other.constant
        elif isinstance(other, Variable):
            result.terms[other] = result.terms.get(other, 0.0) + 1.0
            if abs(result.terms[other]) < 1e-10:
                del result.terms[other]
        else:
            result.constant += float(other)
        return result

    def __radd__(self, other: float) -> "Expression":
        return self + other

    def __sub__(self, other: Union["Expression", Variable, float]) -> "Expression":
        result = Expression(self.terms.copy(), self.constant)
        if isinstance(other, Expression):
            for var, coeff in other.terms.items():
                result.terms[var] = result.terms.get(var, 0.0) - coeff
                if abs(result.terms[var]) < 1e-10:
                    del result.terms[var]
            result.constant -= other.constant
        elif isinstance(other, Variable):
            result.terms[other] = result.terms.get(other, 0.0) - 1.0
            if abs(result.terms[other]) < 1e-10:
                del result.terms[other]
        else:
            result.constant -= float(other)
        return result

    def __rsub__(self, other: float) -> "Expression":
        return (-self) + other

    def __mul__(self, scalar: float) -> "Expression":
        s = float(scalar)
        if abs(s) < 1e-10:
            return Expression(constant=0.0)
        result = Expression(constant=self.constant * s)
        for var, coeff in self.terms.items():
            result.terms[var] = coeff * s
        return result

    def __rmul__(self, scalar: float) -> "Expression":
        return self * scalar

    def __truediv__(self, scalar: float) -> "Expression":
        return self * (1.0 / float(scalar))

    def __neg__(self) -> "Expression":
        return self * -1.0

    def __le__(self, other: Union["Expression", Variable, float]) -> "Constraint":
        from .constraint import Constraint, Relation, Strength
        expr = self - other
        return Constraint(expr, Relation.LE, Strength.REQUIRED)

    def __ge__(self, other: Union["Expression", Variable, float]) -> "Constraint":
        from .constraint import Constraint, Relation, Strength
        expr = other - self
        return Constraint(expr, Relation.LE, Strength.REQUIRED)

    def __eq__(self, other: Union["Expression", Variable, float]) -> "Constraint":
        from .constraint import Constraint, Relation, Strength
        if isinstance(other, (Expression, Variable, int, float)):
            expr = self - other
            return Constraint(expr, Relation.EQ, Strength.REQUIRED)
        return super().__eq__(other)

    def with_strength(self, strength: "Strength") -> "Constraint":
        from .constraint import Constraint, Relation
        return Constraint(self, Relation.EQ, strength)
