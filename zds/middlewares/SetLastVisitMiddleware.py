import datetime
from zds.utils import get_current_user

class SetLastVisitMiddleware(object):

    def process_response(self, request, response):
        # Update last visit time after request finished processing.
        try :
            if request.user.is_authenticated():
                user = request.user
            else:
                user = None
        except:
            user = None

        if user is not None:
            profile = request.user.profile
            if profile.last_visit is None:
                profile.last_visit = datetime.datetime.now()
                profile.save()
            else:
                duration = datetime.datetime.now() - profile.last_visit
                if duration.seconds > 600:
                    profile.last_visit = datetime.datetime.now()
                    profile.save()
        return response
