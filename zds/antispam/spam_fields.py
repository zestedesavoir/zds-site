from zds.forum.models import Comment
from zds.member.models import Profile

spam_fields = [
    {
        "scope": "PROFILE",
        "model": Profile,
        "fields": ["biography", "sign"],
        "get_instance_info": str,
    },
    {
        "scope": "FORUM",
        "model": Comment,
        "fields": ["text"],
        "get_instance_info": lambda instance: str(instance.author.username),
    },
]
