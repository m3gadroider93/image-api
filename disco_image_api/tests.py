from django.test import TestCase
from disco_image_api.models import Image, ThumbnailSize, Plan, UserPlan
from django.contrib.auth.models import User
import os
from django.urls import reverse
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image as PILImage
import time

# Create your tests here.


class ImageTestCase(TestCase):
    def setUp(self):
        test_image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "test_images", "test.jpg"
        )
        self.user = User.objects.create_superuser(
            username="admin123", email="admin123@admin123.com", password="fooooobar"
        )

        self.user2 = User.objects.create_superuser(
            username="admin1234", email="admin1234@admin1234.com", password="fooooobar"
        )

        self.thumbnail_size_200 = ThumbnailSize.objects.create(name=200, height=200)
        self.thumbnail_size_400 = ThumbnailSize.objects.create(name=400, height=400)

        self.basic_plan = Plan.objects.create(name="Basic Plan")
        self.basic_plan.thumbnail_sizes.add(self.thumbnail_size_200)
        self.user_plan = UserPlan.objects.create(user=self.user, plan=self.basic_plan)

        self.premium_plan = Plan.objects.create(name="Premium Plan")
        self.premium_plan.thumbnail_sizes.add(self.thumbnail_size_200)
        self.premium_plan.thumbnail_sizes.add(self.thumbnail_size_400)
        self.user_plan2 = UserPlan.objects.create(
            user=self.user2, plan=self.premium_plan
        )

        self.expiry_image_1 = Image.objects.create(
            user=self.user, image=test_image_path, expiry_seconds=2000
        )
        self.expiry_image_1.set_expiry_date(2000)
        self.expiry_image_2 = Image.objects.create(user=self.user, expiry_seconds=2)
        self.expiry_image_2.set_expiry_date(2)

    def test_image_has_expired_correct(self):
        self.assertFalse(self.expiry_image_1.image_has_expired)

    def test_image_has_expired_incorrect(self):
        time.sleep(5)
        self.assertTrue(self.expiry_image_2.image_has_expired)

    def test_create_thumbnail_images_basic_plan(self):
        thumbnail = self.expiry_image_1.create_thumbnail_images(self.user)
        self.assertEqual(200, thumbnail[0].height)

    def test_create_thumbnail_images_premium_plan(self):
        thumbnails = self.expiry_image_1.create_thumbnail_images(self.user2)
        self.assertEqual(200, thumbnails[0].height)
        self.assertEqual(400, thumbnails[1].height)


class ImageAPITestCase(APITestCase):
    def setUp(self):
        self.test_image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "test_images", "test.jpg"
        )
        self.user = User.objects.create_superuser(
            username="admin123", email="admin123@admin123.com", password="fooooobar"
        )

        self.user2 = User.objects.create_superuser(
            username="admin1234", email="admin1234@admin1234.com", password="fooooobar"
        )

        self.thumbnail_size_200 = ThumbnailSize.objects.create(name=200, height=200)
        self.thumbnail_size_400 = ThumbnailSize.objects.create(name=400, height=400)

        self.basic_plan = Plan.objects.create(name="Basic Plan")
        self.basic_plan.thumbnail_sizes.add(self.thumbnail_size_200)
        self.user_plan = UserPlan.objects.create(user=self.user, plan=self.basic_plan)

        self.premium_plan = Plan.objects.create(name="Premium Plan")
        self.premium_plan.thumbnail_sizes.add(self.thumbnail_size_200)
        self.premium_plan.thumbnail_sizes.add(self.thumbnail_size_400)
        self.premium_plan.generate_original_link = True
        self.premium_plan.generate_expiring_link = True
        self.premium_plan.save()
        self.user_plan2 = UserPlan.objects.create(
            user=self.user2, plan=self.premium_plan
        )

        self.client.login(username="admin1234", password="fooooobar")

        with open(self.test_image_path, "rb") as f:
            image_data = BytesIO(f.read())

        image = PILImage.open(image_data)
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        self.test_inmem_image = InMemoryUploadedFile(
            image_file, None, "test.jpg", "image/jpeg", image_file.tell, None
        )

    def test_create_image(self):
        url = reverse("image-create")
        data = {"image": self.test_inmem_image}
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(list(response.data.keys()), ["original_image", 200, 400])
        self.assertEqual(len(response.data), 3)

    def test_list_images(self):
        url = reverse("image-create")
        data = {"image": self.test_inmem_image}
        self.client.post(url, data, format="multipart")

        url = reverse("image-list")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 3)

    def test_update_image_expire_link(self):
        url = reverse("image-create")
        data = {"image": self.test_inmem_image}
        self.client.post(url, data, format="multipart")

        data = {"expiry_seconds": 300}
        response = self.client.put("/api/image/expiry/2", data)
        self.assertEqual(len(response.data), 1)
        self.assertTrue(response.data.get("image"))

    def test_get_image_expire_link(self):
        url = reverse("image-create")
        data = {"image": self.test_inmem_image}
        self.client.post(url, data, format="multipart")

        data = {"expiry_seconds": 300}
        self.client.put("/api/image/expiry/2", data)

        response = self.client.get("/api/image/expiry/2")
        self.assertEqual(len(response.data), 2)
        self.assertTrue(response.data.get("image"))
        self.assertTrue(response.data.get("id"))
