# Generated by Django 2.2.19 on 2022-04-11 09:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20220411_0912'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date']},
        ),
        migrations.AlterOrderWithRespectTo(
            name='post',
            order_with_respect_to=None,
        ),
    ]