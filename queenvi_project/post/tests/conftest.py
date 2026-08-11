from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import pytest

from post.tests.constants import ImageConstants
from post.models import Media, Post
from user.constants import UserRole


@pytest.fixture
def image_file():
    image = Image.new('RGB', (ImageConstants.RESOLUTION))
    buffer = BytesIO()
    image.save(buffer, format=ImageConstants.FORMAT)
    buffer.seek(ImageConstants.READ_FILE_FROM_BEGIN)
    return SimpleUploadedFile(
        name='test.jpg',
        content=buffer.read(),
        content_type=ImageConstants.CONTENT_TYPE,
    )


@pytest.fixture
def posts(db, users, image_file):
    result = {}
    for role in UserRole:
        post = Post.objects.create(
            name=role,
            description=role,
            user=users[role]
        )
        Media.objects.create(
            file=image_file,
            file_type=ImageConstants.FORMAT,
            post=post,
            order=ImageConstants.FIRST_MEDIA_IDX
        )
        result[role] = post
    return result
