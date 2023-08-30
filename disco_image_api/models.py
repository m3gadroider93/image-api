from django.db import models
from django.contrib.auth.models import User
from easy_thumbnails.files import get_thumbnailer
from datetime import datetime, timedelta
from disco_image_api.validators import content_type_validator
from pytz import timezone
from disco_image_hosting.settings import TIME_ZONE
from django.core.files.images import get_image_dimensions


class ThumbnailSize(models.Model):
    name = models.CharField(max_length=100)
    height = models.IntegerField(help_text="Height in px", blank=True, null=True)
    width = models.IntegerField(help_text="Width in px", blank=True, null=True)

    def __str__(self):
        return self.name


class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to="images/", validators=[content_type_validator()]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    height = models.IntegerField(null=True)
    width = models.IntegerField(null=True)
    expiry_seconds = models.IntegerField(blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.image.url

    def set_expiry_date(self, expiry_seconds):
        tz = timezone(TIME_ZONE)
        date_now = tz.localize(datetime.now())

        self.expiry_seconds = expiry_seconds
        self.expiry_date = date_now + timedelta(seconds=expiry_seconds)
        self.save()

    @property
    def image_has_expired(self):
        tz = timezone(TIME_ZONE)
        date_now = tz.localize(datetime.now())

        if not self.expiry_date:
            return False

        if date_now.timestamp() > self.expiry_date.timestamp():
            return True
        return False

    def get_url(self, request):
        return request.get_host() + self.image.url

    def create_thumbnail_images(self, user, height, width):
        thumbnail_list = []
        user_plan = UserPlan.objects.get(user=user)
        # thumbnail_sizes = user_plan.plan.thumbnail_sizes.values_list('height')
        thumbnail_sizes = user_plan.plan.thumbnail_sizes.all().values()

        latest_img = Image.objects.filter(user=user).latest("id")
        og_width, og_height = get_image_dimensions(latest_img.image)
        ratio = og_width / og_height

        for ts in thumbnail_sizes:
            size = {"size": (0, 0)}
            if ts.get("height") and ts.get("width"):
                size = {"size": (ts["height"], ts["width"])}
            elif ts.get("height") and not ts.get("width"):
                size = {"size": (ts["height"], ts["height"] * ratio)}
            elif ts.get("width") and not ts.get("height"):
                size = {"size": (ts.get("width") / ratio, ts["width"])}

            thumbnail = get_thumbnailer(self.image).get_thumbnail(size)
            thumbnail_list.append(
                Image(
                    user=user,
                    image=str(thumbnail),
                    height=size["size"][0],
                    width=size["size"][1],
                )
            )
        if height or width:
            if height and width:
                size = {"size": (int(height), int(width))}
            elif height and not width:
                size = {"size": (int(height), int(height) * ratio)}
            elif width and not height:
                size = {"size": (int(width) / ratio, int(width))}

            thumbnail = get_thumbnailer(self.image).get_thumbnail(size)
            thumbnail_list.append(
                Image(
                    user=user,
                    image=str(thumbnail),
                    height=size["size"][0],
                    width=size["size"][1],
                )
            )

        thumbnails = Image.objects.bulk_create(thumbnail_list)

        # Delete original image if the user does not have a plan for retaining originals
        if not user_plan.plan.generate_original_link:
            self.delete()

        return thumbnails


class Plan(models.Model):
    name = models.CharField(max_length=100)
    thumbnail_sizes = models.ManyToManyField(ThumbnailSize)
    generate_original_link = models.BooleanField(default=False)
    generate_expiring_link = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class UserPlan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
