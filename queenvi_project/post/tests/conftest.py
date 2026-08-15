from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from post.constants import ReportReason, ReportStatus
from post.tests.constants import TestMediaConstants as TMC
from post.models import Comment, Media, Post, Report
from user.constants import UserRole


@pytest.fixture
def file_factory(name='test.jpg', content=b'test', content_type='image/jpeg'):
    def create(name=name, content=content, content_type=content_type):
        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type=content_type,
        )

    return create


@pytest.fixture
def post_factory(db, users, file_factory):
    def create(user=users[UserRole.USER], name='test', **kwargs):
        post = Post.objects.create(
            user=user,
            name=name,
            ** kwargs,
        )
        Media.objects.create(
            post=post,
            file=file_factory(),
            file_type=TMC.FORMAT,
            order=TMC.FIRST_MEDIA_IDX,
        )
        return post
    return create


@pytest.fixture
def post_many_files(users, file_factory):
    post = Post.objects.create(
        user=users[UserRole.USER],
        name='test',
        description='12345678910',
    )

    Media.objects.bulk_create([
        Media(
            post=post,
            file=file_factory(name=f'{idx}'),
            file_type=TMC.FORMAT,
            order=idx,
        )
        for idx in (
            TMC.THIRD_MEDIA_IDX, TMC.SECOND_MEDIA_IDX, TMC.FIRST_MEDIA_IDX
        )
    ])

    return post


@pytest.fixture
def report_factory(db, users, post_factory):
    def create(
            user=users[UserRole.USER],
            reason=ReportReason.SPAM,
            other='',
            status=ReportStatus.NOT_VIEWED,
    ):
        return Report.objects.create(
            user=user,
            post=post_factory(),
            reason=reason,
            status=status,
            other=other,
        )
    return create


@pytest.fixture
def comment_factory(db, users, post_factory):
    def create(user=users[UserRole.USER], post=post_factory(), text='test'):
        return Comment.objects.create(
            user=user,
            post=post,
            text=text
        )
    return create
