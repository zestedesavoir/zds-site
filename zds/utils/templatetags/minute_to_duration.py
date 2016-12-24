from django import template
from django.utils.translation import ugettext as _
import math

# Set register
register = template.Library()


# Register filter
@register.filter("minute_to_duration")
def minute_to_duration(value, duration_format=''):

    """
    #######################################################
    #                                                     #
    #   Minutes-to-Duration Template Tag                  #
    #   Inspired by Dan Ward 2009 (http://d-w.me)         #
    #   Modified by Anto59290 for Zeste de Savoir         #
    #                                                     #
    #######################################################

    Usage: {{ VALUE|minute_to_duration[:"long"] }}

    NOTE: Please read up 'Custom template tags and filters'
          if you are unsure as to how the template tag is
          implemented in your project.
    """

    # Place seconds in to integer
    secs = int(value * 60)

    # If seconds are greater than 0
    if secs > 0:

        # Place durations of given units in to variables
        daySecs = 86400
        hourSecs = 3600
        minSecs = 60
        # To how many minutes we round up the result when input string is more than an hour
        roundPrecision = 15

        # If short string is enabled
        if duration_format != 'long':

            # Set short names
            dayUnitName = ' jour'
            hourUnitName = ' h'
            minUnitName = ' min'

            # Set short duration unit splitters
            lastDurSplitter = ' '
            nextDurSplitter = lastDurSplitter

        # If short string is not provided or any other value
        else:

            # Set long names
            dayUnitName = ' jour'
            hourUnitName = ' heure'
            minUnitName = ' minute'

            # Set long duration unit splitters
            lastDurSplitter = ' et '
            nextDurSplitter = ', '

        # Create string to hold outpout
        durationString = ''

        # Calculate number of days from seconds
        days = int(math.floor(secs / int(daySecs)))

        # Subtract days from seconds
        secs = secs - (days * int(daySecs))

        # Calculate number of hours from seconds (minus number of days)
        hours = int(math.floor(secs / int(hourSecs)))

        # Subtract hours from seconds
        secs = secs - (hours * int(hourSecs))

        # Calculate number of minutes from seconds (minus number of days and hours)
        minutes = int(math.floor(secs / int(minSecs)))

        # If duration is more than an hour we round up to avoid "5 hours and 7 minutes"
        if hours > 1:
            minutes = minutes - (minutes % roundPrecision)

        # If number of days is greater than 0
        if days > 0:

            # Add multiple days to duration string
            durationString += ' ' + str(days) + dayUnitName + (days > 1 and 's' or '')

        # Determine if next string is to be shown
        if hours > 0:

            # If there are no more units after this
            if minutes <= 0 and days != 0:

                # Set hour splitter to last
                hourSplitter = lastDurSplitter

            # If there are unit after this
            else:
                # Set hour splitter to next
                if (len(durationString) > 0 and nextDurSplitter):
                    hourSplitter = nextDurSplitter
                else:
                    hourSplitter = ''

        # If number of hours is greater than 0
        if hours > 0:

            # Add multiple days to duration string
            durationString += hourSplitter + ' ' + str(hours) + hourUnitName + (hours > 1 and 's' or '')

        # Determine if next string is to be shown
        if minutes > 0 and hours > 0:
            # Set minute splitter to last
            minSplitter = lastDurSplitter
        else:
            minSplitter = ''

        # If number of minutes is greater than 0
        if minutes > 0:

            # Add multiple days to duration string
            durationString += minSplitter + ' ' + str(minutes) + minUnitName + (minutes > 1 and 's' or '')

        # Return duration string
        return durationString.strip()

    # If seconds are not greater than 0
    else:

        # Provide 'No duration' message
        return _(u'Inconnu')
