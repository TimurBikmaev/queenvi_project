from django.db import models

from post.constants import PostCommentStatus, PostCommentStatusConstants


class PostCommentStatusMixin(models.Model):
    status = models.CharField(
        'Статус',
        max_length=PostCommentStatusConstants.MAX_LENGTH,
        choices=PostCommentStatus.choices,
        default=PostCommentStatus.VISIBLE,
    )

    def make_visible(self):
        self.status = PostCommentStatus.VISIBLE
        return self

    def make_hidden(self):
        self.status = PostCommentStatus.HIDDEN
        return self

    def make_banned(self):
        self.status = PostCommentStatus.BANNED
        return self

    @property
    def is_visible(self):
        return self.status == PostCommentStatus.VISIBLE

    @property
    def is_hidden(self):
        return self.status == PostCommentStatus.HIDDEN

    @property
    def is_banned(self):
        return self.status == PostCommentStatus.BANNED

    class Meta:
        abstract = True
