from django import template

register = template.Library()


CONVERT_VALUES = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


@register.filter("roman")
def roman(input_text):
    user_value = int(input_text)
    if user_value < 1 or user_value > 3500:
        raise Exception("out of range!")
    output_text = ""
    for arabeval, romantext in CONVERT_VALUES:
        (resultat, user_value) = divmod(user_value, arabeval)
        for index in range(resultat):
            output_text += romantext
    return output_text
