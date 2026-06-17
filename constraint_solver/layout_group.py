from typing import List, Set, Optional, Dict, Union
from .constraint import Constraint
from .solver import Solver


class LayoutGroup:
    def __init__(self, name: str = "", constraints: Optional[List[Constraint]] = None):
        self.name = name
        self._constraints: List[Constraint] = list(constraints) if constraints else []
        self._enabled: bool = True
        self._solver: Optional[Solver] = None

    def add(self, constraint: Union[Constraint, List[Constraint]]) -> "LayoutGroup":
        if isinstance(constraint, list):
            for c in constraint:
                self._constraints.append(c)
                if self._enabled and self._solver is not None:
                    self._solver.add_constraint(c)
        else:
            self._constraints.append(constraint)
            if self._enabled and self._solver is not None:
                self._solver.add_constraint(constraint)
        return self

    def remove(self, constraint: Constraint) -> "LayoutGroup":
        if constraint in self._constraints:
            self._constraints.remove(constraint)
            if self._enabled and self._solver is not None:
                self._solver.remove_constraint(constraint)
        return self

    def enable(self) -> None:
        if self._enabled or self._solver is None:
            return
        self._enabled = True
        for c in self._constraints:
            self._solver.add_constraint(c)

    def disable(self) -> None:
        if not self._enabled or self._solver is None:
            return
        self._enabled = False
        for c in self._constraints:
            self._solver.remove_constraint(c)

    def toggle(self) -> None:
        if self._enabled:
            self.disable()
        else:
            self.enable()

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def constraints(self) -> List[Constraint]:
        return list(self._constraints)

    def attach(self, solver: Solver) -> None:
        self._solver = solver
        if self._enabled:
            for c in self._constraints:
                solver.add_constraint(c)

    def detach(self) -> None:
        if self._solver is not None and self._enabled:
            for c in self._constraints:
                self._solver.remove_constraint(c)
        self._solver = None

    def __repr__(self) -> str:
        status = "enabled" if self._enabled else "disabled"
        return f"LayoutGroup('{self.name}', {len(self._constraints)} constraints, {status})"


class BreakpointLayout:
    def __init__(self, solver: Solver):
        self._solver = solver
        self._groups: Dict[str, LayoutGroup] = {}
        self._active_group: Optional[str] = None

    def add_breakpoint(self, name: str, constraints: List[Constraint]) -> LayoutGroup:
        group = LayoutGroup(name, constraints)
        self._groups[name] = group
        return group

    def switch_to(self, name: str) -> None:
        if name not in self._groups:
            raise KeyError(f"Breakpoint '{name}' not found")

        if self._active_group is not None and self._active_group != name:
            self._groups[self._active_group].disable()

        if self._active_group != name:
            self._groups[name].attach(self._solver)
            self._groups[name].enable()
            self._active_group = name

    def get(self, name: str) -> Optional[LayoutGroup]:
        return self._groups.get(name)

    @property
    def active(self) -> Optional[str]:
        return self._active_group

    def __repr__(self) -> str:
        return f"BreakpointLayout(active={self._active_group}, breakpoints={list(self._groups.keys())})"
