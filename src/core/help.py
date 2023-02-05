from math import ceil


class Help:
    """
    Convenience class for building help messages programmatically

    Splits the content into 2 sections - abilities and examples.

    Abilities section contains the usage and description of each ability.
    The examples section just lists the added examples.

    The headers of both sections and the top header could be customized
    via respective constructor parameters.
    """

    def __init__(self,
                 header: str = None,
                 abilities_header: str = None,
                 examples_header: str = None):
        self._header = header
        self._abilities_header = abilities_header
        self._examples_header = examples_header
        self._abilities = []
        self._examples = []

    def add_ability(self, usage: str, description: str):
        """
        Add an entry to the abilities section

        :param usage: how to generally invoke the ability
        :param description: what the ability does
        """
        self._abilities.append((usage, description))

    def add_example(self, example: str):
        """
        Add an entry to the examples section

        :param example: arbitrary text, e.g. concrete ability usage
        """
        self._examples.append(example)

    def make_message(self) -> str:
        """
        Create a help message from the previously added abilities and examples.

        The layout of the message is the following:

        ---

        Top Header

        Abilities Header:

        - `usage1` - description1
        - `usage2` - description2
        - ...

        Examples Header:

        - example1
        - example2
        - ...

        ---

        If no ability was added - the abilities section is completely skipped
        including its header. Same with examples.

        The abilities section displays abilities sorted by length ascending.
        Also, extra spaces are added between usages and descriptions
        to align the latter and provide more clean view.

        :return: the composed message
        """
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
