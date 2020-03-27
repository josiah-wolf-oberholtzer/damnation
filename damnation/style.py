import dataclasses
import enum
from typing import List, Optional, Union

from .utils import build_dataclass_repr, build_enum_repr


@dataclasses.dataclass
class Auto:
    def __repr__(self):
        return f"{type(self).__qualname__}()"


@dataclasses.dataclass
class Inherit:
    def __repr__(self):
        return f"{type(self).__qualname__}()"


class Display(enum.Enum):
    BLOCK = 0
    INLINE = 1
    NONE = 2

    def __repr__(self):
        return build_enum_repr(self)


class LengthUnit(enum.Enum):
    PIXELS = 0
    PERCENT = 1

    def __repr__(self):
        return build_enum_repr(self)


@dataclasses.dataclass
class Length:
    size: float
    unit: LengthUnit

    def __post_init__(self):
        if isinstance(self.size, int):
            self.size = float(self.size)
        if isinstance(self.unit, str):
            self.unit = LengthUnit[self.unit.upper()]

    def __repr__(self):
        return build_dataclass_repr(self)


class Clear(enum.Enum):
    LEFT = 0
    RIGHT = 1
    BOTH = 2

    def __repr__(self):
        return build_enum_repr(self)


class Float(enum.Enum):
    LEFT = 0
    RIGHT = 1

    def __repr__(self):
        return build_enum_repr(self)


class Overflow(enum.Enum):
    VISIBLE = 0
    HIDDEN = 1

    def __repr__(self):
        return build_enum_repr(self)


class Position(enum.Enum):
    STATIC = 0
    RELATIVE = 1
    ABSOLUTE = 2
    FIXED = 3

    def __repr__(self):
        return build_enum_repr(self)


class Color:
    pass


class NamedColor(Color, enum.Enum):
    pass


class RGBColor(Color):
    pass


@dataclasses.dataclass
class Transparent:
    def __repr__(self):
        return f"{type(self).__qualname__}()"


@dataclasses.dataclass
class Style:
    clear: Optional[Clear] = None
    display: Display = Display.BLOCK
    float: Optional[Float] = None
    overflow_x: Union[Auto, Overflow] = Auto()
    overflow_y: Union[Auto, Overflow] = Auto()
    position: Position = Position.STATIC
    white_space: None = None
    flex: None = None
    flex_wrap: None = None

    height: Union[Auto, Length] = Auto()
    max_height: Optional[Length] = None
    max_width: Optional[Length] = None
    min_height: Length = Length(0, LengthUnit.PIXELS)
    min_width: Length = Length(0, LengthUnit.PIXELS)
    width: Union[Auto, Length] = Auto()

    padding: Length = Length(0, LengthUnit.PIXELS)
    padding_bottom: Optional[Length] = None
    padding_left: Optional[Length] = None
    padding_right: Optional[Length] = None
    padding_top: Optional[Length] = None

    border_bottom_width: Optional[Length] = None
    border_left_width: Optional[Length] = None
    border_right_width: Optional[Length] = None
    border_top_width: Optional[Length] = None
    border_width: Optional[Length] = Length(0, LengthUnit.PIXELS)

    margin: Union[Auto, Length] = Length(0, LengthUnit.PIXELS)
    margin_bottom: Optional[Union[Auto, Length]] = None
    margin_left: Optional[Union[Auto, Length]] = None
    margin_right: Optional[Union[Auto, Length]] = None
    margin_top: Optional[Union[Auto, Length]] = None

    bottom: Union[Auto, Length] = Auto()
    left: Union[Auto, Length] = Auto()
    right: Union[Auto, Length] = Auto()
    top: Union[Auto, Length] = Auto()

    background_color: Union[Color, Inherit, Transparent] = Inherit()
    color: Union[Color, Inherit] = Inherit()

    def __post_init__(self):
        enumerations = {
            "clear": Clear,
            "display": Display,
            "float": Float,
            "position": Position,
            "overflow": Overflow,
        }
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if value == "auto":
                setattr(self, field_name, Auto())
            elif isinstance(value, str):
                enumeration = enumerations.get(field_name)
                if enumeration is None:
                    raise ValueError(f"Got {value!r} for {field_name}")
                setattr(self, field_name, enumeration[value.upper()])
            elif isinstance(value, (int, float)):
                setattr(self, field_name, Length(value, LengthUnit.PIXELS))

    def __repr__(self):
        return build_dataclass_repr(self)

    def get(self, key):
        key = key.replace("-", "_")
        value = getattr(self, key, None)
        if value is not None:
            return value
        if key.startswith(("margin_", "padding_")):
            return getattr(self, key.partition("_")[0], None)
        elif key.startswith("border_") and key.endswith("_width"):
            return getattr(self, "border_width", None)
        return None


@dataclasses.dataclass
class Node:
    name: str
    children: List["Node"] = dataclasses.field(default_factory=list)
    class_: List[str] = dataclasses.field(default_factory=list)
    id_: Optional[str] = None
    style: Style = dataclasses.field(default_factory=Style)
    text: Optional[str] = None

    def __repr__(self):
        return build_dataclass_repr(self)

    def get(self, key: str):
        return self.style.get(key)
