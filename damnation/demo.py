from .layout import LayoutBox
from .renderer import render
from .style import Node, Style

"""
        Node( "b",
            style=Style(display="block", border_width=1, height=Length(50, "percent")),
        ),
        Node("c", style=Style(display="block", border_width=1, height=1)),
"""

dummy = Node(
    name="box",
    style=Style(border_width=1, display="block", height=2, width=2, margin=2),
)

root_box = LayoutBox.layout_tree(dummy, 20, 20)

if __name__ == "__main__":
    print(render(root_box, 20, 20, default_fill="."))
