# Create your views here.
from disco_image_api.models import Image
from disco_image_api.models import UserPlan
from rest_framework import viewsets
from rest_framework import permissions
from disco_image_api.serializers import ImageSerializer, ImageExpirySerializer
from rest_framework.response import Response


class ImageListView(viewsets.ViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        Lists all the images for the current user
        """
        queryset = Image.objects.filter(user=request.user)
        serializer = ImageSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class ImageCreateView(viewsets.ViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        """
        Create the original image link and the thumbnails if any.
        """
        serializer = ImageSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)

        latest_img = Image.objects.filter(user=self.request.user).latest("id")

        user_plan = UserPlan.objects.get(user=request.user)

        response_dict = {}
        if user_plan.plan:
            if user_plan.plan.generate_original_link:
                response_dict["original_image"] = latest_img.get_url(request)

            thumbnails = latest_img.create_thumbnail_images(
                request.user, request.data.get("height"), request.data.get("width")
            )
            for thumbnail in thumbnails:
                response_dict[
                    str(thumbnail.height) + "x" + str(thumbnail.width)
                ] = thumbnail.get_url(request)

        return Response(response_dict)


class ImageExpiryView(viewsets.ViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageExpirySerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_expiry_link_access(self, user):
        """
        Check is user is on a plan that gets them access to expiry links.
        """
        user_plan = UserPlan.objects.get(user=user)

        if user_plan and user_plan.plan.generate_expiring_link:
            return True
        return False

    def check_expiry_seconds(self, expiry_seconds):
        """
        Check if expiry seconds follow the expiry constraints.
        """
        if expiry_seconds > 30000 or expiry_seconds < 300:
            return False
        return True

    def update(self, request, pk=None):
        """
        This takes an update on a current image to put an expiry date on it.
        """
        if not self.check_expiry_link_access(request.user):
            return Response(
                {
                    "status": 400,
                    "message": "Your user plan does not permit generating expiring links.",
                }
            )

        if not self.check_expiry_seconds(int(request.data.get("expiry_seconds"))):
            return Response(
                {
                    "status": 400,
                    "message": "Expiry needs to be between 300 and 30000 in seconds.",
                }
            )

        try:
            source_image = Image.objects.get(user=request.user, id=pk)
        except Image.DoesNotExist:
            return Response({"error": "Image not found"})

        source_image.set_expiry_date(int(request.data.get("expiry_seconds")))

        return Response({"image": source_image.get_url(request)})

    def retrieve(self, request, pk=None):
        """
        This retrieves the images based on their ids and only serves them if they are not expired.
        """

        if not self.check_expiry_link_access(request.user):
            return Response(
                {
                    "status": 400,
                    "message": "Your user plan does not permit access to expiring links.",
                }
            )

        try:
            image = Image.objects.get(user=request.user, id=pk)
        except Image.DoesNotExist:
            return Response({"error": "Image not found"})

        if image.image_has_expired:
            return Response({"message": "Image has expired."})

        serializer = ImageSerializer(image, context={"request": request})
        return Response(serializer.data)
