from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("utils", "0024_alter_hatrequest_is_granted")]

    database_operations = [migrations.AlterModelTable("HelpWriting", "tutorialv2_helpwriting")]

    state_operations = [migrations.DeleteModel("HelpWriting")]

    operations = [
        migrations.SeparateDatabaseAndState(database_operations=database_operations, state_operations=state_operations)
    ]
