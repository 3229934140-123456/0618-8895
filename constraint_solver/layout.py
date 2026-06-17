from typing import List, Tuple
from .variable import Variable
from .constraint import Constraint, Strength, Relation
from .expression import Expression


class LayoutView:
    def __init__(self, name: str = ""):
        self.name = name
        self.left = Variable(f"{name}.left" if name else "left")
        self.right = Variable(f"{name}.right" if name else "right")
        self.top = Variable(f"{name}.top" if name else "top")
        self.bottom = Variable(f"{name}.bottom" if name else "bottom")

    @property
    def width(self) -> Expression:
        return self.right - self.left

    @property
    def height(self) -> Expression:
        return self.bottom - self.top

    @property
    def center_x(self) -> Expression:
        return (self.left + self.right) / 2.0

    @property
    def center_y(self) -> Expression:
        return (self.top + self.bottom) / 2.0

    def __repr__(self) -> str:
        return (f"View({self.name}: left={self.left.value:.1f}, right={self.right.value:.1f}, "
                f"top={self.top.value:.1f}, bottom={self.bottom.value:.1f}, "
                f"w={self.width.evaluate():.1f}, h={self.height.evaluate():.1f})")


def make_aligned(views: List[LayoutView], attribute: str, strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) < 2:
        return constraints

    first_attr = getattr(views[0], attribute)
    for view in views[1:]:
        attr = getattr(view, attribute)
        constraints.append((first_attr == attr).with_strength(strength))

    return constraints


def make_centered(view: LayoutView, container: LayoutView, axis: str = 'both',
                  strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if axis in ('x', 'both'):
        constraints.append((view.center_x == container.center_x).with_strength(strength))
    if axis in ('y', 'both'):
        constraints.append((view.center_y == container.center_y).with_strength(strength))
    return constraints


def make_equal_spacing(views: List[LayoutView], axis: str = 'x', spacing: float = 0.0,
                       strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) < 2:
        return constraints

    if axis == 'x':
        for i in range(len(views) - 1):
            constraints.append((views[i + 1].left - views[i].right == spacing).with_strength(strength))
    else:
        for i in range(len(views) - 1):
            constraints.append((views[i + 1].top - views[i].bottom == spacing).with_strength(strength))

    return constraints


def make_equal_width(views: List[LayoutView], strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) < 2:
        return constraints

    first_width = views[0].width
    for view in views[1:]:
        constraints.append((view.width == first_width).with_strength(strength))

    return constraints


def make_equal_height(views: List[LayoutView], strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) < 2:
        return constraints

    first_height = views[0].height
    for view in views[1:]:
        constraints.append((view.height == first_height).with_strength(strength))

    return constraints


def make_padding(view: LayoutView, container: LayoutView,
                 left: float = 0, right: float = 0,
                 top: float = 0, bottom: float = 0,
                 strength: float = Strength.REQUIRED) -> List[Constraint]:
    return [
        (view.left >= container.left + left).with_strength(strength),
        (view.right <= container.right - right).with_strength(strength),
        (view.top >= container.top + top).with_strength(strength),
        (view.bottom <= container.bottom - bottom).with_strength(strength),
    ]


def make_min_size(view: LayoutView, min_width: float = 0, min_height: float = 0,
                  strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if min_width > 0:
        constraints.append((view.width >= min_width).with_strength(strength))
    if min_height > 0:
        constraints.append((view.height >= min_height).with_strength(strength))
    return constraints


def make_fixed_size(view: LayoutView, width: float, height: float,
                    strength: float = Strength.REQUIRED) -> List[Constraint]:
    return [
        (view.width == width).with_strength(strength),
        (view.height == height).with_strength(strength),
    ]


def make_fill_container(view: LayoutView, container: LayoutView,
                        strength: float = Strength.REQUIRED) -> List[Constraint]:
    return [
        (view.left == container.left).with_strength(strength),
        (view.right == container.right).with_strength(strength),
        (view.top == container.top).with_strength(strength),
        (view.bottom == container.bottom).with_strength(strength),
    ]
