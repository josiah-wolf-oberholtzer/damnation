import dataclasses
import enum
from typing import List

from .style import Auto, Display, Length, LengthUnit, Node, Position, Style
from .utils import build_dataclass_repr, build_enum_repr


def to_pixels(value, container_pixels):
    if isinstance(value, Length):
        if value.unit == LengthUnit.PIXELS:
            return value.size
        return value.size / 100.0 * container_pixels
    elif isinstance(value, (int, float)):
        return value
    elif isinstance(value, Auto):
        return 0.0
    raise ValueError(f"Cannot convert {value!r} to pixels")


class LayoutBoxType(enum.IntEnum):
    BLOCK = 0
    INLINE = 1
    ANONYMOUS = 2

    def __repr__(self):
        return build_enum_repr(self)


@dataclasses.dataclass
class EdgeSizes:
    left: float = 0.0
    right: float = 0.0
    top: float = 0.0
    bottom: float = 0.0


@dataclasses.dataclass
class Rectangle:
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    def expanded_by(
        self, edge: EdgeSizes, containing_block: "Dimensions"
    ) -> "Rectangle":
        left = to_pixels(edge.left, containing_block.content.width)
        top = to_pixels(edge.top, containing_block.content.height)
        right = to_pixels(edge.right, containing_block.content.width)
        bottom = to_pixels(edge.bottom, containing_block.content.height)
        return dataclasses.replace(
            self,
            x=self.x - left,
            y=self.y - top,
            width=to_pixels(self.width, containing_block.content.width) + left + right,
            height=to_pixels(self.height, containing_block.content.height)
            + top
            + bottom,
        )


@dataclasses.dataclass
class Dimensions:
    child_height: float = 0.0
    content: Rectangle = dataclasses.field(default_factory=Rectangle)
    padding: EdgeSizes = dataclasses.field(default_factory=EdgeSizes)
    border: EdgeSizes = dataclasses.field(default_factory=EdgeSizes)
    margin: EdgeSizes = dataclasses.field(default_factory=EdgeSizes)

    def __repr__(self):
        return build_dataclass_repr(self)

    def padding_box(self, containing_block: "Dimensions") -> Rectangle:
        "The area covered by the content area plus its padding."
        return self.content.expanded_by(self.padding, containing_block)

    def border_box(self, containing_block: "Dimensions") -> Rectangle:
        "The area covered by the content area plus padding and borders."
        return self.padding_box(containing_block).expanded_by(
            self.border, containing_block
        )

    def margin_box(self, containing_block: "Dimensions") -> Rectangle:
        "The area covered by the content area plus padding, borders, and margin."
        return self.border_box(containing_block).expanded_by(
            self.margin, containing_block
        )


@dataclasses.dataclass
class LayoutBox:
    box_type: LayoutBoxType
    node: Node = None
    dimensions: Dimensions = dataclasses.field(default_factory=Dimensions)
    parent: "LayoutBox" = None
    children: List["LayoutBox"] = dataclasses.field(default_factory=list)

    def __repr__(self):
        return build_dataclass_repr(self, ["node", "parent"])

    def find_ancestral_style(self, key):
        parent = self.parent
        while parent is not None:
            value = parent.node.get(key)
            if value is not None and value != Style.__dataclass_fields__[key].default:
                return value
            parent = parent.parent

    def find_ancestral_height(self):
        parent = self.parent
        while parent is not None:
            height = parent.dimensions.content.height
            if height:
                return height
            parent = parent.parent

    def find_ancestral_width(self):
        parent = self.parent
        while parent is not None:
            width = parent.dimensions.content.width
            if width:
                return width
            parent = parent.parent

    def find_positioned_ancestor(self):
        parent = self.parent
        while parent is not None:
            position = parent.node.get("position")
            if position != Position.FIXED:
                return parent
            parent = parent.parent

    @classmethod
    def layout_tree(
        cls, node: Node, viewport_width: int, viewport_height: int
    ) -> "LayoutBox":
        def build_tree(node: Node, parent: "LayoutBox") -> "LayoutBox":
            display = node.get("display")
            if display is None or display == Display.NONE:
                return None
            elif display == Display.BLOCK:
                box_type = LayoutBoxType.BLOCK
            elif display == Display.INLINE:
                box_type = LayoutBoxType.INLINE
            root = cls(box_type=box_type, node=node, parent=parent)
            for child in node.children:
                if child.get("display") == Display.BLOCK:
                    root.children.append(build_tree(child, root))
                elif child.get("display") == Display.INLINE:
                    root.get_inline_container().children.append(build_tree(child, root))
                elif child.get("display") == Display.NONE:
                    continue
            return root

        # TODO: Save the initial containing block height, for calculating percent heights.
        #       The layout algorithm expects the container height to start at 0.
        viewport_box = LayoutBox(
            box_type=LayoutBoxType.BLOCK,
            node=Node(
                "viewport", style=Style(width=viewport_width, height=viewport_height)
            ),
            dimensions=Dimensions(
                content=Rectangle(width=viewport_width, height=viewport_height),
            ),
        )
        root_box = build_tree(node, parent=viewport_box)
        root_box.layout(viewport_box.dimensions)
        viewport_box.children.append(root_box)
        return root_box

    def get_inline_container(self):
        if self.box_type in (LayoutBoxType.INLINE, LayoutBoxType.ANONYMOUS):
            return self
        if len(self.children) and self.children[-1].box_type == LayoutBoxType.ANONYMOUS:
            return self.children[-1]
        anonymous_box = type(self)(LayoutBoxType.ANONYMOUS, parent=self)
        self.children.append(anonymous_box)
        return self.children[-1]

    def layout(self, containing_block: Dimensions):
        "Lay out a box and its descendants."
        if self.box_type == LayoutBoxType.BLOCK:
            self.layout_block(containing_block)
        if self.box_type == LayoutBoxType.INLINE:
            self.layout_inline(containing_block)

    def layout_block(self, containing_block: Dimensions):
        # Child width can depend on parent width, so we need to calculate
        # this box's width before laying out its children.
        self.calculate_block_width(containing_block)
        # Determine where the box is located within its container.
        self.calculate_block_position(containing_block)
        # Recursively lay out the children of this box.
        self.layout_block_children()
        # Parent height can depend on child height, so `calculate_height`
        # must be called *after* the children are laid out.
        self.calculate_block_height(containing_block)

    def layout_inline(self, containing_block: Dimensions):
        pass

    def calculate_block_height(self, containing_block: Dimensions):
        style = self.node
        height = style.get("height")
        container_height = self.find_ancestral_height()
        if isinstance(height, Length):
            self.dimensions.content.height = to_pixels(height, container_height)
        else:
            self.dimensions.content.height = self.dimensions.child_height

    def calculate_block_width(self, containing_block: Dimensions):
        container_width = self.find_ancestral_width()
        width = self.node.get("width")
        margin_left = self.node.get("margin-left")
        margin_right = self.node.get("margin-right")
        border_left = self.node.get("border-left-width")
        border_right = self.node.get("border-right-width")
        padding_left = self.node.get("padding-left")
        padding_right = self.node.get("padding-right")
        total = sum(
            to_pixels(length, container_width)
            for length in [
                margin_left,
                margin_right,
                border_left,
                border_right,
                padding_left,
                padding_right,
                width,
            ]
        )
        underflow = container_width - total
        if isinstance(width, Auto):
            if isinstance(margin_left, Auto):
                margin_left = 0.0
            if isinstance(margin_right, Auto):
                margin_right = 0.0
            if underflow >= 0.0:
                width = underflow
            else:
                width = 0.0
                margin_right = to_pixels(margin_right, container_width) + underflow
        else:
            margin_left_is_auto = isinstance(margin_left, Auto)
            margin_right_is_auto = isinstance(margin_right, Auto)
            if margin_left_is_auto and margin_right_is_auto:
                margin_left = underflow / 2
                margin_right = underflow / 2
            elif margin_left_is_auto and not margin_right_is_auto:
                margin_left = underflow
            elif not margin_left_is_auto and margin_right_is_auto:
                margin_right = underflow
            else:
                margin_right = to_pixels(margin_right, container_width) + underflow
        self.dimensions.content.width = to_pixels(width, container_width)
        self.dimensions.padding.left = to_pixels(padding_left, container_width)
        self.dimensions.padding.right = to_pixels(padding_right, container_width)
        self.dimensions.border.left = to_pixels(border_left, container_width)
        self.dimensions.border.right = to_pixels(border_right, container_width)
        self.dimensions.margin.left = to_pixels(margin_left, container_width)
        self.dimensions.margin.right = to_pixels(margin_right, container_width)
        return total

    def calculate_block_position(self, containing_block: Dimensions):
        container_height = self.find_ancestral_height()
        # container_width = self.find_ancestral_width()

        # TODO: Implement margin merging
        # TODO: Implement absolute / relative / fixed positioning

        x_base, y_base = 0, 0
        if self.node.get("position") == Position.ABSOLUTE:
            positioned_block = self.find_positioned_ancestor()
            if positioned_block is not None:
                x_base = positioned_block.dimensions.content.x
                y_base = positioned_block.dimensions.content.y
        else:
            x_base = containing_block.content.x
            y_base = containing_block.content.y

        self.dimensions.margin.top = to_pixels(
            self.node.get("margin-top"), container_height
        )
        self.dimensions.margin.bottom = to_pixels(
            self.node.get("margin-bottom"), container_height
        )
        self.dimensions.border.top = to_pixels(
            self.node.get("border-top-width"), container_height
        )
        self.dimensions.border.bottom = to_pixels(
            self.node.get("border-bottom-width"), container_height
        )
        self.dimensions.padding.top = to_pixels(
            self.node.get("padding-top"), container_height
        )
        self.dimensions.padding.bottom = to_pixels(
            self.node.get("padding-bottom"), container_height
        )

        self.dimensions.content.x = (
            x_base
            + self.dimensions.margin.left
            + self.dimensions.border.left
            + self.dimensions.padding.left
        )
        self.dimensions.content.y = (
            containing_block.child_height
            + y_base
            + self.dimensions.margin.top
            + self.dimensions.border.top
            + self.dimensions.padding.top
        )

    def layout_block_children(self):
        for child in self.children:
            child.layout(self.dimensions)
            if child.node.get("position") == Position.ABSOLUTE:
                continue
            self.dimensions.child_height += child.dimensions.margin_box(
                self.dimensions
            ).height
