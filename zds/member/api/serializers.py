from django.contrib.auth.models import User
from dry_rest_permissions.generics import DRYPermissionsField
from rest_framework import serializers

from zds.member.commons import ProfileCreate
from zds.member.models import Profile
from zds.member.validators import validate_not_empty, validate_zds_email, validate_zds_username


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializers of a user object. This serializer is necessary because
    we have a bug between User/Profile. Sometimes, models uses a
    foreign key to User, so we must use this serialize. Sometimes,
    models uses a foreign key to Profile, so we must use Profile
    serializers.
    """

    avatar_url = serializers.CharField(source="profile.get_absolute_avatar_url")
    html_url = serializers.CharField(source="get_absolute_url")

    class Meta:
        model = User
        fields = ("id", "username", "html_url", "is_active", "date_joined", "avatar_url")


class ProfileListSerializer(serializers.ModelSerializer):
    """
    Serializers of a profile object.
    """

    id = serializers.ReadOnlyField(source="user.id")
    username = serializers.CharField(source="user.username")
    html_url = serializers.CharField(source="user.get_absolute_url")
    is_active = serializers.BooleanField(source="user.is_active")
    date_joined = serializers.DateTimeField(source="user.date_joined")
    avatar_url = serializers.CharField(source="get_absolute_avatar_url")
    permissions = DRYPermissionsField(additional_actions=["ban"])

    class Meta:
        model = Profile
        fields = ("id", "username", "html_url", "is_active", "date_joined", "last_visit", "avatar_url", "permissions")


class ProfileCreateSerializer(serializers.ModelSerializer, ProfileCreate):
    """
    Serializers of a user object to create one.
    """

    id = serializers.ReadOnlyField(source="user.id")
    username = serializers.CharField(source="user.username", validators=[validate_not_empty, validate_zds_username])
    email = serializers.EmailField(source="user.email", validators=[validate_not_empty, validate_zds_email])
    password = serializers.CharField(source="user.password")
    permissions = DRYPermissionsField(additional_actions=["ban"])

    class Meta:
        model = Profile
        fields = ("id", "username", "email", "password", "permissions")
        write_only_fields = "password"

    def create(self, validated_data):
        profile = self.create_profile(validated_data.get("user"))
        self.save_profile(profile)
        return profile

    def throw_error(self, key=None, message=None):
        raise serializers.ValidationError(message)


class ProfileDetailSerializer(serializers.ModelSerializer):
    """
    Serializers of a profile object.
    """

    id = serializers.ReadOnlyField(source="user.id")
    username = serializers.CharField(source="user.username")
    html_url = serializers.CharField(source="user.get_absolute_url")
    email = serializers.EmailField(source="user.email")
    is_active = serializers.BooleanField(source="user.is_active")
    date_joined = serializers.DateTimeField(source="user.date_joined")
    avatar_url = serializers.CharField(source="get_absolute_avatar_url")
    permissions = DRYPermissionsField(additional_actions=["ban"])

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "html_url",
            "email",
            "is_active",
            "date_joined",
            "site",
            "avatar_url",
            "biography",
            "sign",
            "show_email",
            "show_sign",
            "hide_forum_activity",
            "is_hover_enabled",
            "allow_temp_visual_changes",
            "email_for_answer",
            "last_visit",
            "permissions",
        )

    def __init__(self, *args, **kwargs):
        """
        Create the serializer with or without email field, depending on the show_email argument.
        """
        show_email = kwargs.pop("show_email", False)
        is_authenticated = kwargs.pop("is_authenticated", False)

        super().__init__(*args, **kwargs)

        if not show_email or not is_authenticated:
            # Drop email field.
            self.fields.pop("email")


class ProfileValidatorSerializer(serializers.ModelSerializer):
    """
    Serializers of a profile object used to update a member.
    """

    id = serializers.ReadOnlyField(source="user.id")
    username = serializers.CharField(
        source="user.username", required=False, allow_blank=True, validators=[validate_not_empty, validate_zds_username]
    )
    email = serializers.EmailField(
        source="user.email", required=False, allow_blank=True, validators=[validate_not_empty, validate_zds_email]
    )
    is_active = serializers.BooleanField(source="user.is_active", required=False)
    date_joined = serializers.DateTimeField(source="user.date_joined", required=False)
    permissions = DRYPermissionsField(additional_actions=["ban"])
    show_sign = serializers.BooleanField(allow_null=True, required=False)
    hide_forum_activity = serializers.BooleanField(allow_null=True, required=False)
    is_hover_enabled = serializers.BooleanField(allow_null=True, required=False)
    email_for_answer = serializers.BooleanField(allow_null=True, required=False)

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "email",
            "is_active",
            "date_joined",
            "site",
            "avatar_url",
            "biography",
            "sign",
            "show_email",
            "show_sign",
            "hide_forum_activity",
            "is_hover_enabled",
            "email_for_answer",
            "last_visit",
            "permissions",
        )
        read_only_fields = (
            "is_active",
            "date_joined",
            "last_visit",
            "permissions",
        )

    def update(self, instance, validated_data):
        """
        Update and return an existing `Profile` instance, given the validated data.
        """
        if validated_data.get("user") is not None:
            instance.user.username = validated_data.get("user").get("username", instance.user.username)
            instance.user.email = validated_data.get("user").get("email", instance.user.email)
        instance.site = validated_data.get("site", instance.site) or instance.site
        instance.avatar_url = validated_data.get("avatar_url", instance.avatar_url) or instance.avatar_url
        instance.biography = validated_data.get("biography", instance.biography) or instance.biography
        instance.sign = validated_data.get("sign", instance.sign) or instance.sign

        if validated_data.get("show_email", instance.show_email) != instance.show_email:
            instance.show_email = validated_data.get("show_email", instance.show_email)
        if validated_data.get("show_sign", instance.show_sign) != instance.show_sign:
            instance.show_sign = validated_data.get("show_sign", instance.show_sign)
        if validated_data.get("hide_forum_activity", instance.hide_forum_activity) != instance.hide_forum_activity:
            instance.hide_forum_activity = validated_data.get("hide_forum_activity", instance.hide_forum_activity)
        if validated_data.get("is_hover_enabled", instance.is_hover_enabled) != instance.is_hover_enabled:
            instance.is_hover_enabled = validated_data.get("is_hover_enabled", instance.is_hover_enabled)
        if validated_data.get("email_for_answer", instance.email_for_answer) != instance.email_for_answer:
            instance.email_for_answer = validated_data.get("email_for_answer", instance.email_for_answer)
        instance.user.save()
        instance.save()
        return instance

    def throw_error(self, key=None, message=None):
        raise serializers.ValidationError(message)


class ProfileSanctionSerializer(serializers.ModelSerializer):
    """
    Serializers of a profile object to set the user in reading only access.
    """

    id = serializers.ReadOnlyField(source="user.id")
    username = serializers.ReadOnlyField(source="user.username")
    email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = Profile
        fields = ("id", "username", "email", "can_write", "end_ban_write", "can_read", "end_ban_read")
        read_only_fields = ("can_write", "end_ban_write", "can_read", "end_ban_read")
