from django import template

register = template.Library()

@register.filter('non_breaking_space')
def non_breaking_space(str):
	# Narrow non-breaking space
	str = str.replace(' ;', ' ;')
	str = str.replace(' ?', ' ?')
	str = str.replace(' !', ' !')
	str = str.replace(' %', ' %')

	# Non-breaking space
	str = str.replace('« ', '« ')
	str = str.replace(' »', ' »')
	str = str.replace(' :', ' :')

	return str
