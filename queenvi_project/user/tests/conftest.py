from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import pytest

from user.tests.constants import TestMediaConstants as TMC


@pytest.fixture
def image_factory():
    def create(
        resolution=TMC.DEFAULT_RESOLUTION,
        extra_size=None,
    ):
        buffer = BytesIO()

        image = Image.new('RGB', resolution)
        image.save(buffer, format='JPEG')

        if extra_size is not None:
            buffer.write(b't' * extra_size)

        buffer.seek(TMC.READ_FILE_FROM_BEGIN)

        return SimpleUploadedFile(
            name='test.jpg',
            content=buffer.read(),
            content_type='image/jpeg',
        )

    return create
