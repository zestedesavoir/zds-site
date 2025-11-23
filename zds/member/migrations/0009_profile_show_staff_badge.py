from django.contrib.auth.models import Permission, User
from django.db import migrations, models
from django.db.models import Q

from zds.member.models import Profile


def forwards_func(apps, schema_editor):
    # Check for each user if the staff badge should be displayed
    try:
        staff_perm = Permission.objects.get(codename="change_post")
        staffs = User.objects.filter(
            Q(groups__permissions=staff_perm) | Q(user_permissions=staff_perm) | Q(is_superuser=True)
        ).distinct()
        Profile.objects.filter(user__in=staffs).update(show_staff_badge=True)
    except Permission.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0008_remove_profile_sdz_tutorial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="show_staff_badge",
            field=models.BooleanField(default=False, verbose_name="Afficher le badge staff"),
        ),
        migrations.RunPython(forwards_func),
    ]
