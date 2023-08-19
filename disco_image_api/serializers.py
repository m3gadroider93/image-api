from rest_framework import serializers
from disco_image_api.models import Image

class ImageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Image
        fields = ['id','image']

class ImageExpirySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Image
        fields = ["expiry_seconds"]
