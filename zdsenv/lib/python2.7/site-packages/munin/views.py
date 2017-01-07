from .helpers import muninview
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from datetime import datetime
from datetime import timedelta
import time
from .models import Test

@muninview(config="""graph_title Total Users
graph_vlabel users""")
def total_users(request):
    return [("users",User.objects.all().count())]

@muninview(config="""graph_title Active Users
graph_vlabel users
graph_info Number of users logged in during the last hour""")
def active_users(request):
    hour_ago = datetime.now() - timedelta(hours=1)
    return [("users",User.objects.filter(last_login__gt=hour_ago).count())]

@muninview(config="""graph_title Total Sessions
graph_vlabel sessions""")
def total_sessions(request):
    return [("sessions",Session.objects.all().count())]

@muninview(config="""graph_title Active Sessions
graph_vlabel sessions""")
def active_sessions(request):
    return [("sessions",Session.objects.filter(expire_date__gt=datetime.now()).count())]

@muninview(config="""graph_title DB performance
graph_vlabel milliseconds
graph_info performance of simple insert/select/delete operations""")
def db_performance(request):
    start = time.time()
    t = Test.objects.create(name="inserting at %f" % start)
    end = time.time()
    insert = end - start
    start = time.time()
    t2 = Test.objects.get(id=t.id)
    end = time.time()
    select = end - start
    start = time.time()
    t2.delete()
    end = time.time()
    delete = end - start
    return [("insert",1000 * insert),
            ("select",1000 * select),
            ("delete",1000 * delete)]
