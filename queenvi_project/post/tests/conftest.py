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
def post_factory(db, users, image_file):
    def create(user=users[UserRole.USER], name='test', **kwargs):
        post = Post.objects.create(
            user=user,
            name=name,
            **kwargs,
        )
        Media.objects.create(
            post=post,
            file=image_file,
            file_type=ImageConstants.FORMAT,
            order=ImageConstants.FIRST_MEDIA_IDX,
        )
        return post
    return create
