from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("utils", "0004_auto_20151229_1904"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommentVote",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("positive", models.BooleanField(default=True, verbose_name=b"Est un vote positif")),
                ("comment", models.ForeignKey(to="utils.Comment", on_delete=models.CASCADE)),
                ("user", models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                "verbose_name": "Vote",
                "verbose_name_plural": "Votes",
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="commentvote",
            unique_together={("user", "comment")},
        ),
        migrations.RunSQL(
            (
                "REPLACE INTO utils_commentvote (comment_id, user_id, positive)"
                "SELECT comment_id, user_id, positive FROM ("
                "SELECT DISTINCT t1.comments_id as comment_id, t1.user_id as user_id, 1 as positive "
                "FROM utils_commentlike t1 "
                "UNION SELECT DISTINCT t2.comments_id as comment_id, t2.user_id as user_id, 0 as positive "
                "FROM utils_commentdislike t2"
                ") AS t3;"
            ),
            reverse_sql=(
                "INSERT INTO utils_commentlike (comments_id, user_id) "
                "SELECT vote.comment_id as comments_id, vote.user_id as user_id "
                "FROM utils_commentvote vote "
                "WHERE vote.positive = 1;"
                "INSERT INTO utils_commentdislike (comments_id, user_id) "
                "SELECT vote.comment_id as comments_id, vote.user_id as user_id "
                "FROM utils_commentvote vote "
                "WHERE vote.positive = 0"
            ),
        ),
        migrations.RemoveField(
            model_name="commentdislike",
            name="comments",
        ),
        migrations.RemoveField(
            model_name="commentdislike",
            name="user",
        ),
        migrations.DeleteModel(
            name="CommentDislike",
        ),
        migrations.RemoveField(
            model_name="commentlike",
            name="comments",
        ),
        migrations.RemoveField(
            model_name="commentlike",
            name="user",
        ),
        migrations.DeleteModel(
            name="CommentLike",
        ),
    ]
