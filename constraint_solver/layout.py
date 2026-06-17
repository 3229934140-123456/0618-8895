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
        self.baseline = Variable(f"{name}.baseline" if name else "baseline")

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

    def set_baseline_offset(self, offset_from_top: float, strength: float = Strength.REQUIRED) -> Constraint:
        return (self.baseline == self.top + offset_from_top).with_strength(strength)

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


def make_baseline_aligned(views: List[LayoutView], strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) < 2:
        return constraints

    first_baseline = views[0].baseline
    for view in views[1:]:
        constraints.append((view.baseline == first_baseline).with_strength(strength))

    return constraints


def make_proportional_width(views: List[LayoutView], ratios: List[float],
                          strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) != len(ratios) or len(views) < 2:
        return constraints

    for i in range(1, len(views)):
        constraints.append((views[i].width * ratios[0] == views[0].width * ratios[i]).with_strength(strength))

    return constraints


def make_proportional_height(views: List[LayoutView], ratios: List[float],
                             strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) != len(ratios) or len(views) < 2:
        return constraints

    for i in range(1, len(views)):
        constraints.append((views[i].height * ratios[0] == views[0].height * ratios[i]).with_strength(strength))

    return constraints


def make_aspect_ratio(view: LayoutView, ratio: float,
                       strength: float = Strength.REQUIRED) -> List[Constraint]:
    return [
        (view.width == view.height * ratio).with_strength(strength),
    ]


def make_distribute_proportionally(views: List[LayoutView], container: LayoutView,
                                ratios: List[float], axis: str = 'x',
                                spacing: float = 0.0,
                                padding: float = 0.0,
                                strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) != len(ratios) or len(views) < 2:
        return constraints

    total_ratio = sum(ratios)
    if total_ratio <= 0:
        return constraints

    if axis == 'x':
        total_space = container.right - container.left - 2 * padding - (len(views) - 1) * spacing
        cumulative = padding
        for i, (view, ratio) in enumerate(zip(views, ratios)):
            if i == 0:
                constraints.append((view.left == container.left + padding).with_strength(strength))
            else:
                constraints.append((view.left == views[i - 1].right + spacing).with_strength(strength))
            constraints.append((view.width * total_ratio == total_space * ratio).with_strength(strength))
        constraints.append((views[-1].right == container.right - padding).with_strength(strength))
    else:
        total_space = container.bottom - container.top - 2 * padding - (len(views) - 1) * spacing
        cumulative = padding
        for i, (view, ratio) in enumerate(zip(views, ratios)):
            if i == 0:
                constraints.append((view.top == container.top + padding).with_strength(strength))
            else:
                constraints.append((view.top == views[i - 1].bottom + spacing).with_strength(strength))
            constraints.append((view.height * total_ratio == total_space * ratio).with_strength(strength))
        constraints.append((views[-1].bottom == container.bottom - padding).with_strength(strength))

    return constraints


def make_trailing_aligned(views: List[LayoutView], strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) < 2:
        return constraints
    first_right = views[0].right
    for view in views[1:]:
        constraints.append((view.right == first_right).with_strength(strength))
    return constraints


def make_bottom_aligned(views: List[LayoutView], strength: float = Strength.REQUIRED) -> List[Constraint]:
    constraints = []
    if len(views) < 2:
        return constraints
    first_bottom = views[0].bottom
    for view in views[1:]:
        constraints.append((view.bottom == first_bottom).with_strength(strength))
    return constraints
