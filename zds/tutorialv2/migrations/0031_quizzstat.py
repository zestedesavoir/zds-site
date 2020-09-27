# Generated by Django 2.2.16 on 2020-09-26 15:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0030_contentsuggestion'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizzStat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.TextField(verbose_name='url')),
                ('question', models.TextField(verbose_name='question')),
                ('answer', models.TextField(verbose_name='anwser')),
                ('date_answer', models.DateField(auto_now=True, verbose_name='Date of answer')),
                ('related_content', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tutorialv2.PublishableContent', verbose_name='Tutoriel lié')),
            ],
        ),
    ]
