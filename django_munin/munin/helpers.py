from django.http import HttpResponse


class muninview:
    """decorator to make it simpler to write munin views"""

    def __init__(self, config=""):
        self.config = config

    def __call__(self, func):
        def rendered_func(request, *args, **kwargs):
            tuples = func(request, *args, **kwargs)
            if "autoconfig" in request.GET:
                return HttpResponse("yes")
            if "config" in request.GET:
                rows = ["{}.label {}".format(t[0].replace(" ", "_"), t[0]) for t in tuples]
                return HttpResponse("\n".join([self.config] + rows))
            if type(tuples) == type([]):
                rows = ["{} {}".format(t[0].replace(" ", "_"), str(t[1])) for t in tuples]
                return HttpResponse("\n".join(rows))
            else:
                return tuples

        return rendered_func
