from django.core.validators import FileExtensionValidator


def content_type_validator():
    return FileExtensionValidator(allowed_extensions=["png", "jpg"])
