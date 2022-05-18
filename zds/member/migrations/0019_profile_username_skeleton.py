# Generated by Django 2.1.11 on 2020-01-07 16:07

from django.db import migrations, models


def init_skeleton(apps, schema_editor):
    Profile = apps.get_model("member", "Profile")
    profiles = Profile.objects.all()
    for profile in profiles:
        profile.username_skeleton = Profile.find_username_skeleton(profile.user.username)
        profile.save()


def remove_skeleton(apps, schema_editor):
    Profile = apps.get_model("member", "Profile")
    profiles = Profile.objects.all()
    for profile in profiles:
        profile.username_skeleton = None
        profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0018_auto_20190114_1301"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="username_skeleton",
            field=models.CharField(
                blank=True, db_index=True, max_length=150, null=True, verbose_name="Squelette du username"
            ),
        ),
        migrations.RunPython(init_skeleton, remove_skeleton),
    ]
