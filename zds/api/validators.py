class Validator:
    """
    Super class must be extend by classes which wants validate a model field.
    """

    def throw_error(self, key=None, message=None):
        raise NotImplementedError("`throw_error()` must be implemented.")
