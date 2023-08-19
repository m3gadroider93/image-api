# Image hosting api
An API that allows any user to upload an image in PNG or JPG format and create thumbnails based on user plans.

## Installation

`docker compose up -d`

`docker exec disco_image_hosting_web_run_1 python manage.py loaddata plans.json` - loads intial plans

`docker exec -it disco_image_hosting_web_run_1 bash`

`python manage.py createsuperuser` - create your superuser account

## Service
Service running on: http://0.0.0.0:8000

Log into admin http://0.0.0.0:8000/admin  
Create a UserPlan and assign admin to any plan to test

## Running Tests
Run tests via - `docker exec disco_image_hosting_web_run_1 python manage.py test`

## Endpoints
Fetch image list:

`api/images/` 

Create/Upload image:

`api/image/`

Update existing image/fetch expiry image:

`api/image/expiry/<int:pk>`

