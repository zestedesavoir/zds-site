from django.contrib.auth.models import AnonymousUser
from dry_rest_permissions.generics import DRYPermissions
from rest_framework.serializers import ChoiceField, IntegerField, ModelSerializer, SerializerMethodField

from zds.member.api.serializers import UserListSerializer
from zds.utils.models import Comment, Tag


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "title")
        permissions_classes = DRYPermissions


class LikesSerializer(ModelSerializer):
    count = IntegerField(source="like", read_only=True)
    users = UserListSerializer(source="get_likers", many=True, read_only=True)

    class Meta:
        model = Comment
        fields = ("count", "users")


class DislikesSerializer(ModelSerializer):
    count = IntegerField(source="dislike", read_only=True)
    users = UserListSerializer(source="get_dislikers", many=True, read_only=True)

    class Meta:
        model = Comment
        fields = ("count", "users")


class KarmaSerializer(ModelSerializer):
    like = LikesSerializer(source="*", read_only=True)
    dislike = DislikesSerializer(source="*", read_only=True)
    user = SerializerMethodField()
    vote = ChoiceField(choices=["like", "dislike", "neutral"], write_only=True)

    class Meta:
        model = Comment
        fields = ("like", "dislike", "user", "vote")

    def get_user(self, obj):
        request = self.context.get("request", None)
        if request is not None:
            user = request.user
        else:
            user = AnonymousUser()

        return obj.get_user_vote(user)

    def update(self, instance, validated_data):
        request = self.context.get("request", None)
        if request is not None:
            instance.set_user_vote(request.user, validated_data["vote"])
            instance.save()

        return instance


class PotentialSpamSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ("is_potential_spam",)
