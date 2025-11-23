from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0004_topic_update_index_date"),
    ]

    database_operations = [migrations.AlterModelTable("TopicFollowed", "notification_topicfollowed")]

    state_operations = [migrations.DeleteModel("TopicFollowed")]

    operations = [
        migrations.SeparateDatabaseAndState(database_operations=database_operations, state_operations=state_operations)
    ]
