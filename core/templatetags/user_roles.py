from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def user_role(context):
    """Get the current user's role"""
    user = context['user']
    if user.is_authenticated and hasattr(user, 'profile'):
        return user.profile.role
    return None