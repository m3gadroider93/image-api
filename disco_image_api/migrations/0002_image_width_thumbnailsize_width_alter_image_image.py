# Generated by Django 4.2.4 on 2023-08-30 09:31

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("disco_image_api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="image",
            name="width",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="thumbnailsize",
            name="width",
            field=models.IntegerField(default=0, help_text="Width in px"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="image",
            name="image",
            field=models.ImageField(
                upload_to="images/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["png", "jpg"]
                    )
                ],
            ),
        ),
    ]