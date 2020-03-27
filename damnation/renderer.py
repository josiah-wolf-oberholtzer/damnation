import collections
from typing import List

from .layout import LayoutBox


class Border:
    LIGHT_HORIZONTAL = "\u2500"
    LIGHT_VERTICAL = "\u2502"
    LIGHT_TOP_LEFT = "\u250c"
    LIGHT_TOP_RIGHT = "\u2510"
    LIGHT_BOTTOM_LEFT = "\u2514"
    LIGHT_BOTTOM_RIGHT = "\u2518"
    LIGHT_LEFT = "\u2574"
    LIGHT_RIGHT = "\u2576"
    LIGHT_ARC_TOP_RIGHT = "\u256e"
    LIGHT_ARC_TOP_LEFT = "\u256d"
    LIGHT_ARC_BOTTOM_RIGHT = "\u256f"
    LIGHT_ARC_BOTTOM_LEFT = "\u2570"


def paint(character_array, x, y, character):
    try:
        character_array[y][x] = character
    except IndexError:
        pass


def paint_background(character_array, layout_box):
    content = layout_box.dimensions.content
    padding = layout_box.dimensions.padding
    start_x = int(content.x - padding.left)
    stop_x = int(content.x + content.width + padding.right)
    start_y = int(content.y - padding.top)
    stop_y = int(content.y + content.height + padding.bottom)
    for x in range(start_x, stop_x):
        for y in range(start_y, stop_y):
            paint(character_array, x, y, " ")


def paint_border(character_array, layout_box):
    content = layout_box.dimensions.content
    padding = layout_box.dimensions.padding
    border = layout_box.dimensions.border
    # TODO: Support multi-width borders
    start_x = int(content.x - padding.left)
    stop_x = int(content.x + content.width + padding.right)
    start_y = int(content.y - padding.top)
    stop_y = int(content.y + content.height + padding.bottom)
    if border.top:
        for x in range(start_x, stop_x):
            paint(character_array, x, start_y - 1, Border.LIGHT_HORIZONTAL)
        if border.left:
            paint(character_array, start_x - 1, start_y - 1, Border.LIGHT_ARC_TOP_LEFT)
        if border.right:
            paint(character_array, stop_x, start_y - 1, Border.LIGHT_ARC_TOP_RIGHT)
    if border.bottom:
        for x in range(start_x, stop_x):
            paint(character_array, x, stop_y, Border.LIGHT_HORIZONTAL)
        if border.left:
            paint(character_array, start_x - 1, stop_y, Border.LIGHT_ARC_BOTTOM_LEFT)
        if border.right:
            paint(character_array, stop_x, stop_y, Border.LIGHT_ARC_BOTTOM_RIGHT)
    if border.left:
        for y in range(start_y, stop_y):
            paint(character_array, start_x - 1, y, Border.LIGHT_VERTICAL)
    if border.right:
        for y in range(start_y, stop_y):
            paint(character_array, stop_x, y, Border.LIGHT_VERTICAL)


def render_one_box(layout_box: LayoutBox, character_array: List[List[str]]):
    paint_background(character_array, layout_box)
    paint_border(character_array, layout_box)


def render(
    layout_box: LayoutBox, viewport_width: int, viewport_height: int, default_fill=" "
) -> str:
    character_array = []
    for _ in range(viewport_height):
        character_array.append([default_fill] * viewport_width)
    stack = collections.deque([layout_box])
    while stack:
        current_box = stack.popleft()
        render_one_box(current_box, character_array)
        stack.extend(current_box.children)
    return "\n".join("".join(line) for line in character_array)
