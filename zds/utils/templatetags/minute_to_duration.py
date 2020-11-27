from django import template
from django.utils.translation import ugettext as ngettext

register = template.Library()

def minute_to_duration(value):
    """
    Display a human-readable reading-time (or any other duration)
    from a duration in minutes, with a granularity of 15 minutes.
    """
    if value <= 0:
        return ''
    # Rounds value to avoid "1 hour, 2 minutes".
    if 55 <= value <= 65:
        value = 60
    elif value > 65:
        value = value - (value % 15)

    min_in_hour = 60
    hours_in_day = 24
    min_in_day = min_in_hour * hours_in_day

    if value < min_in_hour:
        if value == 1:
            return '1 minute'
        if value != 1:
            return f'{value} minutes'

    if value < min_in_day and value % min_in_hour == 0:
        value /= min_in_hour
        return ngettext('%(count)d heure', '%(count)d heures', value) % {'count': value}

    if value < min_in_day and value % min_in_hour != 0:
        hours = value // min_in_hour
        minutes = value % min_in_hour
        return (ngettext('%(hours)d heure et %(minutes)d minutes', '%(hours)d heures et %(minutes)d minutes', hours) % 
        {'hours': hours, 'minutes': minutes})

    if value >= min_in_day:
        value //= min_in_hour
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        return f'{value} heures'
=======
        return f"{value} heures"
>>>>>>> Modifie les test suite aux modifications du template
=======
        return f"{value} heures"
=======
        return f'{value} heures'
>>>>>>> Retire les imports inutiles + code plus propre
>>>>>>> Retire les imports inutiles + code plus propre
=======
        return f'{value} heures'
>>>>>>> Diminue la longueur de ligne + corrige erreur d'import
