import black


def build_dataclass_repr(self, ignored_field_names=()):
    fragments = []
    for field_name, field_spec in self.__dataclass_fields__.items():
        value = getattr(self, field_name)
        if value == field_spec.default or field_name in ignored_field_names:
            continue
        fragments.append(f"{field_name}={value!r}")
    string = "{}({})".format(type(self).__qualname__, ", ".join(fragments))
    return black.format_file_contents(string, fast=True, mode=black.FileMode()).strip()


def build_enum_repr(self):
    return "{}.{}".format(type(self).__qualname__, self.name)
