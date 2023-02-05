from math import ceil


class Help:
    def __init__(self, header: str = None,
                 abilities_header: str = None,
                 examples_header: str = None):
        self._header = header
        self._abilities_header = abilities_header
        self._examples_header = examples_header
        self._abilities = []
        self._examples = []

    def add_ability(self, usage: str, description: str):
        self._abilities.append((usage, description))

    def add_example(self, example: str):
        self._examples.append(example)

    def make_message(self):
        return "\n\n".join(
            section for section in [
                self._header,
                self._make_abilities_section(),
                self._make_examples_section()
            ] if section
        )

    def _make_abilities_section(self):
        if not self._abilities:
            return None

        abilities = sorted(self._abilities, key=lambda p: len(p[0]) // 4)

        listing = "\n".join(f"- `{usage:<{ceil(len(usage) / 8) * 8}}`"
                            f" - {description}"
                            for usage, description
                            in abilities)

        return f"{self._abilities_header}\n{listing}"

    def _make_examples_section(self):
        if not self._examples:
            return None

        listing = "\n".join(f"- `{e}`" for e in self._examples)
        return f"{self._examples_header}\n{listing}"
