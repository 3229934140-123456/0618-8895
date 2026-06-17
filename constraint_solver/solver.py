from typing import Dict, List, Set, Optional, Tuple
from .variable import Variable
from .expression import Expression
from .constraint import Constraint, Relation, Strength


class _Row:
    def __init__(self, constant: float = 0.0):
        self.constant = constant
        self.terms: Dict[Variable, float] = {}

    def __repr__(self) -> str:
        parts = [f"{self.constant:.4f}"]
        for var, coeff in sorted(self.terms.items(), key=lambda x: x[0].name):
            sign = '+' if coeff >= 0 else '-'
            parts.append(f"{sign} {abs(coeff):.4f}*{var}")
        return " ".join(parts)

    def add_var(self, var: Variable, coeff: float) -> None:
        if abs(coeff) < 1e-12:
            return
        if var in self.terms:
            new_coeff = self.terms[var] + coeff
            if abs(new_coeff) < 1e-12:
                del self.terms[var]
            else:
                self.terms[var] = new_coeff
        else:
            self.terms[var] = coeff

    def add_row(self, other: "_Row", multiplier: float = 1.0) -> None:
        self.constant += other.constant * multiplier
        for var, coeff in other.terms.items():
            self.add_var(var, coeff * multiplier)

    def has_var(self, var: Variable) -> bool:
        return var in self.terms

    def coefficient_for(self, var: Variable) -> float:
        return self.terms.get(var, 0.0)


class Solver:
    def __init__(self):
        self._constraints: Set[Constraint] = set()
        self._external_vars: Set[Variable] = set()
        self._rows: Dict[Variable, _Row] = {}
        self._columns: Dict[Variable, Set[Variable]] = {}
        self._objective: _Row = _Row()
        self._error_vars: Dict[Constraint, Tuple[Variable, Variable]] = {}
        self._slack_vars: Dict[Constraint, Variable] = {}
        self._artificial_vars: Set[Variable] = set()
        self._artificial_var_map: Dict[Constraint, Variable] = {}
        self._var_counter = 0
        self._optimized = False
        self._infeasible = False

    def _new_var(self, prefix: str = "v") -> Variable:
        self._var_counter += 1
        var = Variable(f"{prefix}_{self._var_counter}")
        self._columns[var] = set()
        return var

    def _add_row(self, basic_var: Variable, row: _Row) -> None:
        self._substitute_basic_vars(row)
        self._rows[basic_var] = row
        for var in row.terms:
            if var not in self._columns:
                self._columns[var] = set()
            self._columns[var].add(basic_var)
        if basic_var not in self._columns:
            self._columns[basic_var] = set()

    def add_constraint(self, constraint: Constraint) -> None:
        if constraint in self._constraints:
            return
        self._constraints.add(constraint)
        self._optimized = False

        expr = constraint.expression
        for var in expr.terms:
            if var not in self._columns:
                self._columns[var] = set()
                self._external_vars.add(var)

        if constraint.is_required():
            self._add_required_constraint(constraint, expr)
        else:
            self._add_soft_constraint(constraint, expr)

    def _add_required_constraint(self, constraint: Constraint, expr: Expression) -> None:
        if constraint.is_inequality():
            self._add_le_constraint(expr, constraint)
        else:
            self._add_eq_constraint(expr, constraint)

    def _add_le_constraint(self, expr: Expression, constraint: Constraint) -> None:
        row_const = -expr.constant
        row_terms: Dict[Variable, float] = {}
        for var, coeff in expr.terms.items():
            row_terms[var] = -coeff

        if row_const >= -1e-12:
            slack = self._new_var("s")
            self._slack_vars[constraint] = slack
            row = _Row(row_const)
            for v, c in row_terms.items():
                row.add_var(v, c)
            self._add_row(slack, row)
        else:
            art = self._new_var("a")
            self._artificial_vars.add(art)
            self._artificial_var_map[constraint] = art
            surplus = self._new_var("s")
            self._slack_vars[constraint] = surplus

            row = _Row(-row_const)
            for v, c in row_terms.items():
                row.add_var(v, -c)
            row.add_var(surplus, 1.0)
            self._add_row(art, row)

    def _add_eq_constraint(self, expr: Expression, constraint: Constraint) -> None:
        row_const = -expr.constant
        row_terms: Dict[Variable, float] = {}
        for var, coeff in expr.terms.items():
            row_terms[var] = -coeff

        art = self._new_var("a")
        self._artificial_vars.add(art)
        self._artificial_var_map[constraint] = art

        if row_const >= -1e-12:
            row = _Row(row_const)
            for v, c in row_terms.items():
                row.add_var(v, c)
            self._add_row(art, row)
        else:
            row = _Row(-row_const)
            for v, c in row_terms.items():
                row.add_var(v, -c)
            self._add_row(art, row)

    def _add_soft_constraint(self, constraint: Constraint, expr: Expression) -> None:
        e_plus = self._new_var("ep")
        e_minus = self._new_var("em")
        self._error_vars[constraint] = (e_plus, e_minus)

        if constraint.is_inequality():
            self._objective.add_var(e_plus, constraint.strength)
            self._add_soft_inequality(constraint, expr, e_plus)
        else:
            self._objective.add_var(e_plus, constraint.strength)
            self._objective.add_var(e_minus, constraint.strength)
            self._add_soft_equality(expr, e_plus, e_minus)

    def _add_soft_equality(self, expr: Expression, e_plus: Variable, e_minus: Variable) -> None:
        if expr.constant >= -1e-12:
            row = _Row(expr.constant)
            for var, coeff in expr.terms.items():
                row.add_var(var, coeff)
            row.add_var(e_minus, 1.0)
            self._add_row(e_plus, row)
        else:
            row = _Row(-expr.constant)
            for var, coeff in expr.terms.items():
                row.add_var(var, -coeff)
            row.add_var(e_plus, 1.0)
            self._add_row(e_minus, row)

    def _add_soft_inequality(self, constraint: Constraint, expr: Expression, e_plus: Variable) -> None:
        slack = self._new_var("s")
        self._slack_vars[constraint] = slack

        row_const = -expr.constant
        if row_const >= -1e-12:
            row = _Row(row_const)
            for var, coeff in expr.terms.items():
                row.add_var(var, -coeff)
            row.add_var(e_plus, 1.0)
            self._add_row(slack, row)
        else:
            row = _Row(-row_const)
            for var, coeff in expr.terms.items():
                row.add_var(var, coeff)
            row.add_var(slack, 1.0)
            self._add_row(e_plus, row)

    def add_constraints(self, constraints: List[Constraint]) -> None:
        for c in constraints:
            self.add_constraint(c)

    def remove_constraint(self, constraint: Constraint) -> None:
        if constraint not in self._constraints:
            return
        self._constraints.remove(constraint)
        self._optimized = False
        self._infeasible = False

        if constraint in self._error_vars:
            e_plus, e_minus = self._error_vars[constraint]
            del self._error_vars[constraint]
            self._objective.add_var(e_plus, -constraint.strength)
            self._objective.add_var(e_minus, -constraint.strength)
            self._remove_var(e_plus)
            self._remove_var(e_minus)

        if constraint in self._slack_vars:
            slack = self._slack_vars[constraint]
            del self._slack_vars[constraint]
            self._remove_var(slack)

        if constraint in self._artificial_var_map:
            art = self._artificial_var_map[constraint]
            del self._artificial_var_map[constraint]
            if art in self._artificial_vars:
                self._remove_var(art)

    def _remove_var(self, var: Variable) -> None:
        if var in self._rows:
            row = self._rows[var]
            for v in list(row.terms.keys()):
                if v in self._columns:
                    self._columns[v].discard(var)
            del self._rows[var]
        else:
            for row_var in list(self._columns.get(var, set())):
                if row_var in self._rows:
                    self._pivot(row_var, var)
                    break
            if var in self._rows:
                row = self._rows[var]
                for v in list(row.terms.keys()):
                    if v in self._columns:
                        self._columns[v].discard(var)
                del self._rows[var]

        self._columns.pop(var, None)
        self._external_vars.discard(var)
        self._artificial_vars.discard(var)

    def remove_constraints(self, constraints: List[Constraint]) -> None:
        for c in constraints:
            self.remove_constraint(c)

    def solve(self) -> None:
        if self._optimized:
            self._extract_values()
            return

        if self._artificial_vars:
            self._phase1()

        if self._infeasible:
            self._extract_values()
            return

        self._optimize()
        self._extract_values()
        self._optimized = True

    def _phase1(self) -> None:
        old_objective = self._objective
        self._objective = _Row()
        for art in self._artificial_vars:
            self._objective.add_var(art, 1.0)

        for art in list(self._artificial_vars):
            if art in self._rows and self._objective.has_var(art):
                row = self._rows[art]
                coeff = self._objective.coefficient_for(art)
                self._objective.add_var(art, -coeff)
                self._objective.add_row(row, coeff)

        iteration = 0
        while True:
            iteration += 1
            if iteration > 1000:
                break

            entering = self._find_entering(self._objective, use_external=True)
            if entering is None:
                break

            leaving = self._find_leaving(entering)
            if leaving is None:
                break

            self._pivot(leaving, entering)

        phase1_value = self._objective.constant
        self._objective = old_objective

        if abs(phase1_value) > 1e-6:
            self._infeasible = True
            return

        for art in list(self._artificial_vars):
            if art in self._rows:
                pivoted = False
                for var, coeff in list(self._rows[art].terms.items()):
                    if var not in self._artificial_vars and abs(coeff) > 1e-8:
                        self._pivot(art, var)
                        pivoted = True
                        break
                if not pivoted:
                    row = self._rows[art]
                    for v in list(row.terms.keys()):
                        if v in self._columns:
                            self._columns[v].discard(art)
                    del self._rows[art]
                    self._columns.pop(art, None)
                    self._artificial_vars.discard(art)

    def _optimize(self) -> None:
        self._substitute_basic_vars(self._objective)

        iteration = 0
        while True:
            iteration += 1
            if iteration > 1000:
                break

            entering = self._find_entering(self._objective, use_external=True)
            if entering is None:
                break

            leaving = self._find_leaving(entering)
            if leaving is None:
                break

            self._pivot(leaving, entering)

    def _substitute_basic_vars(self, row: _Row) -> None:
        basic_vars = list(self._rows.keys())
        for basic_var in basic_vars:
            if row.has_var(basic_var):
                coeff = row.coefficient_for(basic_var)
                if abs(coeff) > 1e-12:
                    basic_row = self._rows[basic_var]
                    row.add_var(basic_var, -coeff)
                    row.add_row(basic_row, coeff)

    def _find_entering(self, objective: _Row, use_external: bool) -> Optional[Variable]:
        best_var = None
        best_coeff = 0.0

        for var, coeff in objective.terms.items():
            if not use_external and var in self._external_vars:
                continue
            if var in self._artificial_vars:
                continue
            if coeff < -1e-8:
                if coeff < best_coeff:
                    best_coeff = coeff
                    best_var = var

        return best_var

    def _find_leaving(self, entering: Variable) -> Optional[Variable]:
        min_ratio = float('inf')
        leaving = None

        for row_var, row in self._rows.items():
            coeff = row.coefficient_for(entering)
            if coeff < -1e-8:
                ratio = -row.constant / coeff
                if ratio < min_ratio - 1e-10:
                    min_ratio = ratio
                    leaving = row_var

        return leaving

    def _pivot(self, leaving: Variable, entering: Variable) -> None:
        row = self._rows.pop(leaving)

        for var in list(row.terms.keys()):
            if var in self._columns:
                self._columns[var].discard(leaving)

        pivot_coeff = row.coefficient_for(entering)
        if abs(pivot_coeff) < 1e-12:
            return

        new_row = _Row()
        new_row.constant = -row.constant / pivot_coeff
        new_row.add_var(leaving, 1.0 / pivot_coeff)

        for var, coeff in row.terms.items():
            if var is not entering:
                new_row.add_var(var, -coeff / pivot_coeff)

        self._rows[entering] = new_row
        for var in new_row.terms:
            if var not in self._columns:
                self._columns[var] = set()
            self._columns[var].add(entering)
        if entering not in self._columns:
            self._columns[entering] = set()

        for row_var in list(self._rows.keys()):
            if row_var is entering:
                continue
            r = self._rows[row_var]
            coeff = r.coefficient_for(entering)
            if abs(coeff) > 1e-12:
                for var in list(r.terms.keys()):
                    if var in self._columns:
                        self._columns[var].discard(row_var)
                r.add_var(entering, -coeff)
                r.add_row(new_row, coeff)
                for var in r.terms:
                    if var in self._columns:
                        self._columns[var].add(row_var)

        if entering in self._objective.terms:
            coeff = self._objective.coefficient_for(entering)
            if abs(coeff) > 1e-12:
                self._objective.add_var(entering, -coeff)
                self._objective.add_row(new_row, coeff)

    def _extract_values(self) -> None:
        for var in self._external_vars:
            if var in self._rows:
                var.value = self._rows[var].constant
            else:
                var.value = 0.0

    def get_value(self, var: Variable) -> float:
        if not self._optimized:
            self.solve()
        return var.value

    def constraint_satisfied(self, constraint: Constraint) -> bool:
        if not self._optimized:
            self.solve()
        value = constraint.expression.evaluate()
        if constraint.relation == Relation.LE:
            return value <= 1e-6
        elif constraint.relation == Relation.GE:
            return value >= -1e-6
        else:
            return abs(value) < 1e-6

    def get_objective_value(self) -> float:
        if not self._optimized:
            self.solve()
        return self._objective.constant

    def has_conflict(self) -> bool:
        if not self._optimized:
            self.solve()
        return self._infeasible

    def reset(self) -> None:
        self._constraints.clear()
        self._external_vars.clear()
        self._rows.clear()
        self._columns.clear()
        self._objective = _Row()
        self._error_vars.clear()
        self._slack_vars.clear()
        self._artificial_vars.clear()
        self._var_counter = 0
        self._optimized = False
        self._infeasible = False
