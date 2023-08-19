from django.db import models
from django.contrib.auth.models import User
from easy_thumbnails.files import get_thumbnailer
from datetime import datetime, timedelta
from disco_image_api.validators import content_type_validator
from pytz import timezone
from disco_image_hosting.settings import TIME_ZONE

class ThumbnailSize(models.Model):
    name = models.CharField(max_length=100)
    height = models.IntegerField(help_text="Height in px")

    def __str__(self):  
          return self.name 
    
class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', validators=[content_type_validator()])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    height = models.IntegerField(null=True)
    expiry_seconds = models.IntegerField(blank=True,null=True)
    expiry_date = models.DateTimeField(blank=True,null=True)

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
    
    def create_thumbnail_images(self, user):
        thumbnail_list = []
        user_plan = UserPlan.objects.get(user=user)
        thumbnail_sizes = user_plan.plan.thumbnail_sizes.values_list('height')

        for ts in thumbnail_sizes:
            thumbnail = get_thumbnailer(self.image).get_thumbnail({"size": (ts[0],ts[0])})
            thumbnail_list.append(
                Image(
                    user=user,
                    image=str(thumbnail),
                    height=ts[0]
                )
            )
        
        thumbnails = Image.objects.bulk_create(thumbnail_list)
        
        #Delete original image if the user does not have a plan for retaining originals
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