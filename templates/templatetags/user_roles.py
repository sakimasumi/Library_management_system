from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def user_role(context):
    user = context['user']
    if not user.is_authenticated:
        return 'anonymous'
    # Try to get custom member role if exists
    member = getattr(user, 'member', None)
    if member and hasattr(member, 'role'):
        # If role is a string, return it; if it's a related object, return its name
        role = member.role
        if hasattr(role, 'role_name'):
            return role.role_name.lower()
        return str(role).lower()
    if user.is_superuser or user.is_staff:
        return 'admin'
    return 'student'