# Generated by Django 4.2.4 on 2023-08-30 10:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("disco_image_api", "0002_image_width_thumbnailsize_width_alter_image_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="thumbnailsize",
            name="height",
            field=models.IntegerField(blank=True, help_text="Height in px", null=True),
        ),
        migrations.AlterField(
            model_name="thumbnailsize",
            name="width",
            field=models.IntegerField(blank=True, help_text="Width in px", null=True),
        ),
    ]
