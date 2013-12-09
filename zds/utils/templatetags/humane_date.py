# coding: utf-8

# This file comes from Progmod; it was slightly modified to work properly
# on zds and translated for the sake of language consistency.
# Hats off to them!

from datetime import *
from django import template
from pytz import timezone, UnknownTimeZoneError

import zds.settings

def humane_date(date, conf={}):
    """Transforms a date into a human-readable format.

    Compares the current date to the given one:
    - 3 minutes and 25 seconds ago
    - 2 hours ago
    - yesterday at 18:00
    - three months ago

    Arguments:
    - date: a datetime instance, with or without a timezone

    - conf: a dictionary containing the parameters, if needed.
            It's a dictionary because this method is meant to be
            used as a Django filter and filters can only have one argument.
            Currently supported keys (and their respective default values) are
            as follows:

            - 'debug' (False): if True, adds debug info
            - 'precise' (False): if True, removes the precision limit (see below)
            - 'precision_limit' (3): precision limit (see below)
            - 'disable' (False): if True, displays the date in the usual format
            - 'full_after_week' (True): if True, displays the full date if
                                        it's more than a week old

    Implementation: Look at the two most important units (e.g. min/sec or day/month)
                    By default, show the second one only if the first is less than
                    the 'precision_limit' parameter. If the 'precise' parameter is True,
                    there is no precision limit.

                    One edge case is when the given date has a timezone info; if the
                    two most important units are day/hour and the date is less than two
                    days old or in the current week, display a relative date like this:
                    - yesterday at 10
                    - tomorrow at noon
                    - Tuesday at 9
                    0 and 12 are displayed as "midnight" and "noon" respectively

    """
    
    precise_limit = conf.get('precision_limit', 3)
    precise = conf.get('precise', False)
    debug = conf.get('debug', False)
    disable = conf.get('disable', False)
    full_after_week = conf.get('full_after_week', True)
    tz = date.tzinfo
    use_tz = (tz is not None)

    today = datetime.now(tz)
    diff = date - today

    def fulldate(date, today):
        if (date.year == today.year):
            return date.strftime("le %a %d %B à %H:%M:%S")
        else:
            return date.strftime("le %d/%m/%Y à %H:%M:%S")

    if disable:
        return fulldate(date, today)

    def week(date):
        """Week number"""
        year, week, weekday = date.isocalendar()
        return year, week

    secondes = ('seconde', abs(diff).seconds % 60)
    minutes = ('minute', abs(diff).seconds // 60 % 60)
    heures = ('heure', abs(diff).seconds // 60 // 60 % 24)
    jours = ('jour', abs(diff).days % 31)
    mois = ('mois', int(abs(diff).days % 365 // 30.5))
    annees = ('an', abs(diff).days // 365)

    if not debug:
        debug_msg = ' '
    else:
        debug_msg = "[debug(humane_date) today:{0} date:{1} conf:{2}] ".format \
            (today, date, conf)

    prefixe = "il y a" if date < today else "dans"

    def compte((str, n)):
        """Returns the requested unit, using plural if necessary"""
        return "{0} {1}{2}".format(n, str, 's' if n > 1 and str[-1] != 's' else '')

    def presente(unite1, unite2, prefixe=prefixe + ' '):
        """Returns one or two of the given units, depending on precision"""
        result = debug_msg + prefixe
        if (not precise and unite1[1] > precise_limit) or unite2[1] == 0:
            result += compte(unite1)
        elif unite1[1] == 0:
            result += compte(unite2)
        else:
            result += "{0} et {1}".format(compte(unite1), compte(unite2))
        return result

    daydiff = (date.date() - today.date()).days

    if abs(diff) < timedelta(seconds=1):
        return "maintenant"
    elif abs(diff) < timedelta(hours=1):
        return presente(minutes, secondes)
    elif daydiff == 0:
        return presente(heures, minutes)
    elif use_tz and (abs(daydiff) <= 2 or week(date) == week(today)):
        if abs(daydiff) <= 2:
            assert (date.day != today.day)
            jour = {-1: 'hier', -2: 'avant-hier', 1: 'demain',
                    2: 'après-demain'}[daydiff]
        elif week(date) == week(today):
            jour = {1: 'lundi', 2: 'mardi', 3: 'mercredi', 4: 'jeudi',
                    5: 'vendredi', 6: 'samedi', 7: 'dimanche'}[date.isoweekday()]
        heure = ('heure', date.hour)
        if not precise:
            heure_str = {0: 'minuit', 12: 'midi'}.get(heure[1], compte(heure))
        else:
            heure_str = presente(heure, ('minute', date.minute), prefixe='')
        return "{0}{1} à {2}".format(debug_msg, jour, heure_str)
    elif use_tz and full_after_week:
        return fulldate(date, today)
    elif abs(diff) < timedelta(days=31):
        return presente(jours, heures)
    elif abs(diff) < timedelta(days=365):
        return presente(mois, jours)
    else:
        return presente(annees, mois)


def test(tz=None):
    """humane_date tests"""
    def test_date(date, conf={}):
        pass
        #print "{0}  : {1}".format(date, humane_date(date, conf))
    #seconds

    def now(tz=None):
        return datetime.now(tz)

    test_date(now())
    test_date(now() - timedelta(seconds=2))
    test_date(now().replace(second=2))

    #minutes and seconds
    test_date(now() - timedelta(minutes=3))
    test_date(now() - timedelta(minutes=3, seconds=2))
    test_date(now().replace(minute=3, second=2))

    #hours and day limits
    def subtest(tz):
        test_date(now(tz) - timedelta(hours=1, minutes=2, seconds=5))
        test_date(
            now(tz) - timedelta(hours=3, minutes=12), {'precise': True})
        test_date(
            now(tz) - timedelta(hours=14, minutes=12), {'precise': True})
        test_date(now(tz) - timedelta(hours=23))
        test_date((now(tz) - timedelta(days=1)).replace(hour=0))
        test_date((now(tz) - timedelta(days=1)).replace(hour=12))
        test_date(now(tz) - timedelta(days=3))

    subtest(tz)

    # day, month, year
    test_date(now() - timedelta(days=45))
    test_date(now() - timedelta(days=130))
    test_date(now() - timedelta(days=365 + 20))
    test_date(now() - timedelta(days=365 + 92))
    test_date(now() - timedelta(days=5 * 365 + 25))

    #disable
    test_date(now(tz), {'disable': True})
    test_date(now(tz) - timedelta(days=1000), {'disable': True})

    #debug
    delta = timedelta(seconds=3, minutes=4, hours=5, days=6)
    test_date(now(tz) - delta, {'debug': True})


def do_humane_date(parser, token):
    content = token.split_contents()

    if not len(content) in (2, 3):
        raise template.SyntaxError, "Usage : {% humane_date variable (optional user timezone) %}"

    tz = "user_timezone"
    if len(content) == 3:
        tz = content[2]

    return HumaneDateNode(content[1], tz)


class HumaneDateNode(template.Node):
    def __init__(self, date_variable, tz_variable):
        self.date_variable = template.Variable(date_variable)
        self.tz_variable = template.Variable(tz_variable)

    def render(self, context):
        date = self.date_variable.resolve(context)
        tz = self.tz_variable.resolve(context)

        # What do we want? Convert the date from the native timezone to the user's
        # then give it to humane_date - there's a bug if localize isn't used
        # When do we want it? Now!
        date_nn = timezone(zds.settings.TIME_ZONE).localize(date)
        date_tz = date_nn.astimezone(tz)
        return humane_date(date_tz)


def set_timezone(request):
    tz = timezone(zds.settings.TIME_ZONE)
    if request.user.is_authenticated():
        try:
            tz = timezone(request.user.get_profile().timezone)
        except UnknownTimeZoneError:
            pass

    return {'user_timezone': tz}

if __name__ == '__main__':
    # 'humane_date' test
    test(None)
    # The 'pytz' library is needed for timezones
    test(timezone('Europe/Paris'))
else:
    # Registering 'humane_date' as a Django filter
    from django import template
    register = template.Library()
    register.filter('humane_date', humane_date)
    register.tag('humane_date', do_humane_date)
    humane_date.is_safe = True

