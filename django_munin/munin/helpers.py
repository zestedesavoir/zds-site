from django.http import HttpResponse


class muninview:
    """decorator to make it simpler to write munin views"""

    def __init__(self, config=""):
        self.config = config

    def __call__(self, func):
        def rendered_func(request, *args, **kwargs):
            view_output_tuples = func(request, *args, **kwargs)
            assert type(view_output_tuples) == type([])

            if "autoconfig" in request.GET:
                return HttpResponse("yes")

            if "config" in request.GET:
                default_labels = []
                for row_name, _ in view_output_tuples:
                    assert " " not in row_name
                    if f"{row_name}.label " not in self.config:
                        default_labels.append(f"{row_name}.label {row_name}")

                return HttpResponse("\n".join([self.config] + default_labels))

            rows = []
            for row_name, row_value in view_output_tuples:
                assert " " not in row_name
                rows.append(f"{row_name} {row_value}")

            return HttpResponse("\n".join(rows))

        return rendered_func
