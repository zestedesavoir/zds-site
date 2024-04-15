class SearchFilter:
    """Class to generate filters for Typesense queries.

    See https://typesense.org/docs/26.0/api/search.html#filter-parameters
    """

    def __init__(self):
        self.filter = ""

    def __str__(self):
        return self.filter

    def _add_filter(self, f):
        if self.filter != "":
            self.filter += " && "
        self.filter += f"({f})"

    def add_exact_filter(self, field: str, values: list):
        """
        Filter documents such as field has one of the values.

        :param field: Name of the field to apply the filter on.
        :type field: str
        :param values: A list of values the field can have.
        :type values: list
        """
        self._add_filter(f"{field}:=[" + ",".join(map(str, values)) + "]")

    def add_bool_filter(self, field: str, value: bool):
        self._add_filter(f"{field}:{str(value).lower()}")

    def add_not_numerical_filter(self, field: str, values: list[int]):
        """
        Filter documents such as field has *not* one of the values.

        :param field: Name of the field to filter.
        :type field: str
        :param values: A list of integer values the field cannot have.
        :type values: list[int]
        """
        self._add_filter(f"{field}:!=[" + ",".join(map(str, values)) + "]")
