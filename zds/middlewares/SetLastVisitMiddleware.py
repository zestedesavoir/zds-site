from django.contrib.auth.models import User
import datetime

class SetLastVisitMiddleware(object):
    def process_response(self, request, response):
        if request.user.is_authenticated():
            # Update last visit time after request finished processing.
            #User.objects.filter(pk=request.user.pk).update(last_visit=now())
            profile = User.objects.get(pk=request.user.pk).get_profile()
            if profile.last_visit is None:
                profile.last_visit = datetime.datetime.now()
                profile.save()
            else:
                duration = datetime.datetime.now() - profile.last_visit
                if duration.seconds > 600:
                    profile.last_visit = datetime.datetime.now()
                    profile.save()
        return response