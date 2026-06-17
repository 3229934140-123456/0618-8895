from constraint_solver import (
    Solver, LayoutView, Strength,
    make_centered, make_equal_spacing, make_aligned,
    make_equal_width, make_equal_height, make_padding,
    make_min_size, make_fixed_size
)


def example_basic_constraints():
    print("=" * 60)
    print("示例1: 基本线性约束 - 简单的等式和不等式")
    print("=" * 60)

    solver = Solver()

    from constraint_solver import Variable
    x = Variable("x")
    y = Variable("y")

    solver.add_constraint(x + y == 10)
    solver.add_constraint(x >= 3)
    solver.add_constraint(y >= 2)

    solver.add_constraint((x == 5).with_strength(Strength.WEAK))

    solver.solve()

    print(f"x = {x.value:.3f}")
    print(f"y = {y.value:.3f}")
    print(f"x + y = {x.value + y.value:.3f}")
    print()


def example_centered_view():
    print("=" * 60)
    print("示例2: 居中布局 - 子视图在容器中居中")
    print("=" * 60)

    solver = Solver()

    container = LayoutView("container")
    subview = LayoutView("subview")

    solver.add_constraints([
        container.left == 0,
        container.top == 0,
        container.right == 400,
        container.bottom == 300,
    ])

    solver.add_constraints(make_fixed_size(subview, 100, 80))
    solver.add_constraints(make_centered(subview, container))

    solver.solve()

    print(f"容器: {container}")
    print(f"子视图: {subview}")
    print(f"子视图中心: ({subview.center_x.evaluate():.1f}, {subview.center_y.evaluate():.1f})")
    print(f"容器中心: ({container.center_x.evaluate():.1f}, {container.center_y.evaluate():.1f})")
    print()


def example_equal_spacing():
    print("=" * 60)
    print("示例3: 等间距排列 - 三个视图水平等间距分布")
    print("=" * 60)

    solver = Solver()

    container = LayoutView("container")
    view1 = LayoutView("view1")
    view2 = LayoutView("view2")
    view3 = LayoutView("view3")

    solver.add_constraints([
        container.left == 0,
        container.top == 0,
        container.right == 600,
        container.bottom == 200,
    ])

    solver.add_constraints(make_equal_width([view1, view2, view3]))
    solver.add_constraints(make_equal_height([view1, view2, view3]))
    solver.add_constraints(make_equal_spacing([view1, view2, view3], axis='x', spacing=20))

    solver.add_constraints(make_aligned([view1, view2, view3], 'top'))
    solver.add_constraints([
        view1.height == 100,
        view1.top == 50,
    ])

    solver.add_constraint(view1.left == container.left + 20)
    solver.add_constraint(view3.right == container.right - 20)

    solver.solve()

    print(f"容器: {container}")
    print(f"view1: {view1}")
    print(f"view2: {view2}")
    print(f"view3: {view3}")
    print(f"间距1-2: {view2.left.value - view1.right.value:.1f}")
    print(f"间距2-3: {view3.left.value - view2.right.value:.1f}")
    print()


def example_soft_hard_constraints():
    print("=" * 60)
    print("示例4: 软硬约束优先级 - 硬约束必须满足，软约束尽量满足")
    print("=" * 60)

    solver = Solver()

    container = LayoutView("container")
    view = LayoutView("view")

    solver.add_constraints([
        container.left == 0,
        container.top == 0,
        container.right == 300,
        container.bottom == 200,
    ])

    solver.add_constraints(make_padding(view, container, left=10, right=10, top=10, bottom=10))

    solver.add_constraint((view.width == 400).with_strength(Strength.STRONG))
    solver.add_constraint((view.width == 50).with_strength(Strength.WEAK))
    solver.add_constraint((view.height == 80).with_strength(Strength.MEDIUM))

    solver.solve()

    print(f"容器宽度: {container.width.evaluate():.1f}")
    print(f"视图宽度: {view.width.evaluate():.1f}")
    print(f"视图高度: {view.height.evaluate():.1f}")
    print(f"左内边距: {view.left.value - container.left.value:.1f}")
    print(f"右内边距: {container.right.value - view.right.value:.1f}")
    print()
    print("说明: 硬约束(内边距)必须满足，所以宽度最大只能是280")
    print("     STRONG优先级想要400宽，但被硬约束限制在280")
    print("     WEAK优先级想要50宽，被STRONG优先级覆盖")
    print()


def example_incremental():
    print("=" * 60)
    print("示例5: 增量添加/移除约束")
    print("=" * 60)

    solver = Solver()

    container = LayoutView("container")
    view = LayoutView("view")

    solver.add_constraints([
        container.left == 0,
        container.top == 0,
        container.right == 400,
        container.bottom == 300,
    ])

    solver.add_constraints(make_fixed_size(view, 100, 80))
    solver.add_constraints(make_centered(view, container, strength=Strength.MEDIUM))

    solver.solve()
    print("初始状态（MEDIUM强度居中）:")
    print(f"  视图: {view}")

    left_align = (view.left == container.left + 20).with_strength(Strength.STRONG)
    solver.add_constraint(left_align)
    solver.solve()
    print("\n添加强度为STRONG的左对齐约束后:")
    print(f"  视图: {view}")
    print("  (STRONG优先级高于MEDIUM，所以视图左对齐)")

    solver.remove_constraint(left_align)
    solver.solve()
    print("\n移除左对齐约束后（恢复居中）:")
    print(f"  视图: {view}")
    print()


def example_conflict_detection():
    print("=" * 60)
    print("示例6: 约束冲突检测")
    print("=" * 60)

    solver = Solver()

    from constraint_solver import Variable
    x = Variable("x")

    solver.add_constraint(x == 10)
    solver.add_constraint(x == 20)

    try:
        solver.solve()
        has_conflict = solver.has_conflict()
        print(f"是否存在冲突: {has_conflict}")
        print(f"x = {x.value:.3f}")
        if has_conflict:
            print("检测到硬约束冲突！两个等式约束无法同时满足。")
    except Exception as e:
        print(f"求解异常: {e}")
    print()


def example_complex_layout():
    print("=" * 60)
    print("示例7: 复杂布局 - 容器+标题栏+内容区+侧边栏")
    print("=" * 60)

    solver = Solver()

    window = LayoutView("window")
    title_bar = LayoutView("title_bar")
    content = LayoutView("content")
    sidebar = LayoutView("sidebar")
    main_content = LayoutView("main_content")

    solver.add_constraints([
        window.left == 0,
        window.top == 0,
        window.right == 800,
        window.bottom == 600,
    ])

    solver.add_constraints([
        title_bar.left == window.left,
        title_bar.right == window.right,
        title_bar.top == window.top,
        title_bar.height == 40,
    ])

    solver.add_constraints([
        content.left == window.left,
        content.right == window.right,
        content.top == title_bar.bottom,
        content.bottom == window.bottom,
    ])

    solver.add_constraints([
        sidebar.left == content.left,
        sidebar.top == content.top,
        sidebar.bottom == content.bottom,
        sidebar.width == 200,
    ])

    solver.add_constraints([
        main_content.left == sidebar.right,
        main_content.right == content.right,
        main_content.top == content.top,
        main_content.bottom == content.bottom,
    ])

    solver.solve()

    print(f"窗口: {window}")
    print(f"标题栏: {title_bar}")
    print(f"内容区: {content}")
    print(f"侧边栏: {sidebar}")
    print(f"主内容区: {main_content}")
    print()


def example_min_max_constraints():
    print("=" * 60)
    print("示例8: 最小/最大尺寸约束")
    print("=" * 60)

    solver = Solver()

    container = LayoutView("container")
    view = LayoutView("view")

    solver.add_constraints([
        container.left == 0,
        container.top == 0,
        container.right == 500,
        container.bottom == 400,
    ])

    solver.add_constraints(make_min_size(view, 100, 80))

    solver.add_constraint(view.left == container.left + 50)
    solver.add_constraint(view.top == container.top + 50)
    solver.add_constraint((view.right == container.right - 50).with_strength(Strength.WEAK))
    solver.add_constraint((view.bottom == container.bottom - 50).with_strength(Strength.WEAK))
    solver.add_constraint((view.width == 300).with_strength(Strength.STRONG))
    solver.add_constraint((view.height == 200).with_strength(Strength.STRONG))

    solver.solve()

    print(f"容器: {container}")
    print(f"视图: {view}")
    print(f"宽度(最小100, 期望300): {view.width.evaluate():.1f}")
    print(f"高度(最小80, 期望200): {view.height.evaluate():.1f}")
    print()


if __name__ == "__main__":
    example_basic_constraints()
    example_centered_view()
    example_equal_spacing()
    example_soft_hard_constraints()
    example_incremental()
    example_conflict_detection()
    example_complex_layout()
    example_min_max_constraints()
