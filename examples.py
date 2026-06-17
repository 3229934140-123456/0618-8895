from constraint_solver import (
    Solver, LayoutView, Strength, LayoutGroup, BreakpointLayout,
    make_centered, make_equal_spacing, make_aligned,
    make_equal_width, make_equal_height, make_padding,
    make_min_size, make_fixed_size, make_fill_container,
    make_baseline_aligned, make_proportional_width,
    make_aspect_ratio, make_distribute_proportionally
)
from constraint_solver import Variable


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


def example_layout_groups():
    print("=" * 60)
    print("示例9: 布局组 - 断点布局切换")
    print("=" * 60)

    solver = Solver()

    container = LayoutView("container")
    sidebar = LayoutView("sidebar")
    content = LayoutView("content")

    solver.add_constraints([
        container.left == 0,
        container.top == 0,
        container.right == 800,
        container.bottom == 600,
    ])

    base_constraints = [
        content.top == container.top,
        content.bottom == container.bottom,
        sidebar.top == container.top,
        sidebar.bottom == container.bottom,
        content.left == sidebar.right,
        content.right == container.right,
        sidebar.left == container.left,
        (sidebar.width >= 150).with_strength(Strength.STRONG),
        (sidebar.width <= 300).with_strength(Strength.STRONG),
    ]
    solver.add_constraints(base_constraints)

    desktop = LayoutGroup("desktop", [
        (sidebar.width == 250).with_strength(Strength.MEDIUM),
    ])
    desktop.attach(solver)

    tablet = LayoutGroup("tablet", [
        (sidebar.width == 200).with_strength(Strength.MEDIUM),
    ])

    mobile = LayoutGroup("mobile", [
        (sidebar.width == 0).with_strength(Strength.MEDIUM),
        content.left == container.left,
    ])

    solver.solve()
    print("桌面布局 (侧边栏250px):")
    print(f"  {sidebar}")
    print(f"  {content}")

    print("\n切换到平板布局 (侧边栏200px):")
    desktop.disable()
    tablet.attach(solver)
    tablet.enable()
    solver.solve()
    print(f"  {sidebar}")
    print(f"  {content}")

    print("\n切换到移动布局 (侧边栏隐藏):")
    tablet.disable()
    mobile.attach(solver)
    mobile.enable()
    solver.solve()
    print(f"  {sidebar}")
    print(f"  {content}")

    print("\n使用 BreakpointLayout 管理器:")
    solver2 = Solver()
    container2 = LayoutView("container")
    view2 = LayoutView("view")

    solver2.add_constraints([
        container2.left == 0,
        container2.top == 0,
        container2.right == 600,
        container2.bottom == 400,
    ])
    solver2.add_constraints(make_fixed_size(view2, 200, 150))

    bp = BreakpointLayout(solver2)
    bp.add_breakpoint("left", [
        (view2.left == container2.left + 20).with_strength(Strength.STRONG),
        (view2.center_y == container2.center_y).with_strength(Strength.STRONG),
    ])
    bp.add_breakpoint("center", make_centered(view2, container2, strength=Strength.STRONG))
    bp.add_breakpoint("right", [
        (view2.right == container2.right - 20).with_strength(Strength.STRONG),
        (view2.center_y == container2.center_y).with_strength(Strength.STRONG),
    ])

    for bp_name in ["left", "center", "right"]:
        bp.switch_to(bp_name)
        solver2.solve()
        print(f"  {bp_name}: view.left={view2.left.value:.0f}, view.center_x={view2.center_x.evaluate():.0f}")

    print()


def example_debug_info():
    print("=" * 60)
    print("示例10: 约束调试信息 - 查看每条约束的满足状态")
    print("=" * 60)

    solver = Solver()

    x = Variable("x")
    y = Variable("y")

    solver.add_constraint(x + y == 10)
    solver.add_constraint(x >= 3)
    solver.add_constraint(y >= 2)
    solver.add_constraint((x == 8).with_strength(Strength.STRONG))
    solver.add_constraint((y == 1).with_strength(Strength.WEAK))

    solver.solve()

    solver.print_debug_info("调试信息 - 变量约束求解")

    print(f"结果: x={x.value:.1f}, y={y.value:.1f}")
    print("说明:")
    print("  - 硬约束 x+y=10, x>=3, y>=2 全部满足")
    print("  - STRONG 软约束 x=8 满足 (y=2)")
    print("  - WEAK 软约束 y=1 违反 1.0 (被 y>=2 硬约束限制)")
    print()


def example_new_layout_intents():
    print("=" * 60)
    print("示例11: 新增布局意图 - 基线对齐、比例分配、固定比例")
    print("=" * 60)

    print("\n--- 基线对齐 ---")
    solver1 = Solver()
    label = LayoutView("label")
    input_field = LayoutView("input")
    button = LayoutView("button")

    solver1.add_constraints([
        label.left == 10,
        label.top == 100,
        input_field.left == 100,
        input_field.top == 80,
        button.left == 300,
        button.top == 90,
    ])
    solver1.add_constraints([
        (label.width == 80).with_strength(Strength.REQUIRED),
        (label.height == 30).with_strength(Strength.REQUIRED),
        (input_field.width == 180).with_strength(Strength.REQUIRED),
        (input_field.height == 50).with_strength(Strength.REQUIRED),
        (button.width == 100).with_strength(Strength.REQUIRED),
        (button.height == 40).with_strength(Strength.REQUIRED),
    ])

    solver1.add_constraint(label.set_baseline_offset(22))
    solver1.add_constraint(input_field.set_baseline_offset(38))
    solver1.add_constraint(button.set_baseline_offset(28))
    solver1.add_constraints(make_baseline_aligned([label, input_field, button]))

    solver1.solve()
    print(f"label:  top={label.top.value:.0f}, baseline={label.baseline.value:.0f}")
    print(f"input:  top={input_field.top.value:.0f}, baseline={input_field.baseline.value:.0f}")
    print(f"button: top={button.top.value:.0f}, baseline={button.baseline.value:.0f}")
    print(f"所有元素基线对齐在 y={label.baseline.value:.0f}")

    print("\n--- 按比例分配宽度 (1:2:1) ---")
    solver2 = Solver()
    container = LayoutView("container")
    col1 = LayoutView("col1")
    col2 = LayoutView("col2")
    col3 = LayoutView("col3")

    solver2.add_constraints([
        container.left == 0,
        container.top == 0,
        container.right == 600,
        container.bottom == 200,
    ])

    solver2.add_constraints(make_distribute_proportionally(
        [col1, col2, col3], container, [1, 2, 1],
        axis='x', spacing=10, padding=20
    ))
    solver2.add_constraints([
        col1.top == container.top + 20,
        col2.top == container.top + 20,
        col3.top == container.top + 20,
        col1.bottom == container.bottom - 20,
        col2.bottom == container.bottom - 20,
        col3.bottom == container.bottom - 20,
    ])

    solver2.solve()
    print(f"容器宽度: {container.width.evaluate():.0f}")
    print(f"col1: left={col1.left.value:.0f}, width={col1.width.evaluate():.0f} (ratio 1)")
    print(f"col2: left={col2.left.value:.0f}, width={col2.width.evaluate():.0f} (ratio 2)")
    print(f"col3: left={col3.left.value:.0f}, width={col3.width.evaluate():.0f} (ratio 1)")
    total = col1.width.evaluate() + col2.width.evaluate() + col3.width.evaluate() + 10*2 + 20*2
    print(f"验证: 140+280+140+2*10间距+2*20边距 = {total:.0f}")

    print("\n--- 固定宽高比 (16:9) ---")
    solver3 = Solver()
    video = LayoutView("video")
    screen = LayoutView("screen")

    solver3.add_constraints([
        screen.left == 0,
        screen.top == 0,
        screen.right == 800,
        screen.bottom == 600,
    ])
    solver3.add_constraints(make_centered(video, screen))
    solver3.add_constraints(make_aspect_ratio(video, 16 / 9))
    solver3.add_constraints(make_fill_container(video, screen, strength=Strength.WEAK))
    solver3.add_constraints([
        (video.width <= screen.width).with_strength(Strength.REQUIRED),
        (video.height <= screen.height).with_strength(Strength.REQUIRED),
    ])

    solver3.solve()
    print(f"屏幕: {screen}")
    print(f"视频: {video}")
    print(f"宽高比: {video.width.evaluate() / video.height.evaluate():.4f} (16/9 = {16/9:.4f})")

    print()


def example_responsive_resize():
    print("=" * 60)
    print("示例12: 响应式布局 - 窗口缩放时自动重算")
    print("=" * 60)

    solver = Solver()

    window = LayoutView("window")
    title_bar = LayoutView("title_bar")
    sidebar = LayoutView("sidebar")
    content = LayoutView("content")
    status_bar = LayoutView("status_bar")

    solver.add_constraints([
        window.left == 0,
        window.top == 0,
    ])

    solver.add_constraints([
        title_bar.left == window.left,
        title_bar.right == window.right,
        title_bar.top == window.top,
        title_bar.height == 40,
    ])

    solver.add_constraints([
        status_bar.left == window.left,
        status_bar.right == window.right,
        status_bar.bottom == window.bottom,
        status_bar.height == 30,
    ])

    solver.add_constraints([
        sidebar.top == title_bar.bottom,
        sidebar.bottom == status_bar.top,
        sidebar.left == window.left,
        content.top == title_bar.bottom,
        content.bottom == status_bar.top,
        content.right == window.right,
        content.left == sidebar.right,
    ])

    solver.add_constraints([
        (sidebar.width >= 150).with_strength(Strength.STRONG),
        (sidebar.width <= 350).with_strength(Strength.STRONG),
    ])

    solver.add_constraint((sidebar.width == 250).with_strength(Strength.MEDIUM))

    solver.add_constraints([
        (content.width >= 300).with_strength(Strength.REQUIRED),
    ])

    win_width_constraint = None
    win_height_constraint = None

    def resize_window(width, height, desc):
        nonlocal win_width_constraint, win_height_constraint

        if win_width_constraint is not None:
            solver.remove_constraint(win_width_constraint)
        if win_height_constraint is not None:
            solver.remove_constraint(win_height_constraint)

        win_width_constraint = window.right == width
        win_height_constraint = window.bottom == height
        solver.add_constraint(win_width_constraint)
        solver.add_constraint(win_height_constraint)
        solver.solve()

        print(f"\n{desc} ({width}x{height}):")
        print(f"  标题栏: {title_bar}")
        print(f"  侧边栏: {sidebar}")
        print(f"  内容区: {content}")
        print(f"  状态栏: {status_bar}")
        print(f"  内容区占比: {content.width.evaluate()/window.width.evaluate()*100:.0f}%")

        if solver.has_conflict():
            print(f"  ⚠️  警告: 存在约束冲突！")

    resize_window(800, 600, "默认尺寸")
    resize_window(1200, 800, "放大尺寸")
    resize_window(600, 400, "缩小尺寸")
    resize_window(400, 300, "最小尺寸 (内容区挤压侧边栏)")

    print("\n布局关系保持:")
    print("  ✓ 标题栏始终在顶部，高度40px")
    print("  ✓ 状态栏始终在底部，高度30px")
    print("  ✓ 侧边栏靠左，宽度 150-350px 之间")
    print("  ✓ 内容区填充剩余空间")
    print("  ✓ 标题栏/侧边栏/内容区/状态栏边缘始终对齐")
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
    example_layout_groups()
    example_debug_info()
    example_new_layout_intents()
    example_responsive_resize()
