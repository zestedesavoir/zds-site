# django-munin

This is a Django application to make it a bit simpler to use
[Munin](http://munin-monitoring.org/) to monitor various metrics
for your Django app.

First, it includes a munin plugin that you can symlink into
`/etc/munin/plugins/` and point at your django application and it will
gather data for munin to graph. Second, it contains a couple views
that return some very basic information about the state of your app:
database performance, number of users, number of sessions, etc. Third,
it provides a decorator to make it simple to expose your own custom
metrics to Munin.

## Installing

Install `django-munin` into your python path with the usual `pip install`
or whatever you are doing. Then add `munin` to your `INSTALLED_APPS` and
run `manage.py syncdb` (it just needs to set up one database table
that it will use for performance testing).

To access the included basic views, add the following pattern to your
`urls.py`:

    ('^munin/',include('munin.urls')),

The views available there are then going to be at:

* `munin/db_performance/`   (milliseconds to perform insert/select/delete operations)
* `munin/total_users/`      (total number of Users)
* `munin/active_users/`     (number of users logged in in the last hour)
* `munin/total_sessions/`   (total number of sessions)
* `munin/active_sessions/`  (number of sessions that are not expired)

Those were the only metrics I could think of that would be potentially
useful on just about any Django app and were likely to always be
available.

(I'm going to assume that you are already a pro at configuring
Munin. If not, go get on that. Munin is very cool)

Next, copy `plugins/django.py` into your `/usr/share/munin/plugins/`
directory.

For each metric that you want Munin to monitor, make a symlink in
`/etc/munin/plugins/` to `/usr/share/munin/plugins/django.py` with an
appropriate name. Eg, to monitor all five of the included ones (as
root, probably):

    $ ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/myapp_db_performance
    $ ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/myapp_total_users
    $ ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/myapp_active_users
    $ ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/myapp_total_sessions
    $ ln -s /usr/share/munin/plugins/django.py /etc/munin/plugins/myapp_active_sessions

You then need to configure each of them in
`/etc/munin/plugin-conf.d/munin-node`

For each, give it a stanza with `env.url` and `graph_category` set. To
continue the above, you'd add something like:

    [myapp_db_performance]
    env.url http://example.com/munin/db_performance/
    env.graph_category myapp

    [myapp_total_users]
    env.url http://example.com/munin/total_users/
    env.graph_category myapp

    [myapp_active_users]
    env.url http://example.com/munin/active_users/
    env.graph_category myapp

    [myapp_total_sessions]
    env.url http://example.com/munin/total_sessions/
    env.graph_category myapp

    [myapp_active_sessions]
    env.url http://example.com/munin/active_sessions/
    env.graph_category myapp

If your HTTP server require Basic Authentication, you can add login and password
as parameters:

    [myapp_active_sessions]
    env.url http://example.com/munin/active_sessions/
    env.graph_category myapp
	env.login mylogin
	env.password mypassword

Restart your Munin node, and it should start collecting and graphing
that data.

## Custom munin views

Those are pretty generic metrics though and the real power of this
application is that you can easily expose your own custom
metrics. Basically, anything that you can calculate in the context of
a Django view in your application, you can easily expose to Munin.

`django-munin` includes a `@muninview` decorator that lets you write a
regular django view that returns a list of `(key,value)` tuples and it
will expose those to that `django.py` munin plugin for easy graphing.

The `@muninview` decorator takes a `config` parameter, which is just a
string of munin config directives. You'll want to put stuff like
`graph_title`, `graph_vlabel`, and `graph_info` there. Possibly
`graph_category` too (if you include it there, remove it from the munin
plugin conf stanza). The view function that it wraps then just needs
to return a list of tuples.

The simplest way to get a feel for how this works is to look at how
the included views were written. So check out [munin/views.py](https://github.com/ccnmtl/django-munin/blob/master/munin/views.py).
