from datetime import timedelta
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
import pytest

from core.constants import TestConstants
from post.constants import ReportConstants, ReportReason, ReportStatus
from post.models import Report
from post.tests.constants import TestReportConstants as TRC
from user.constants import UserRole


User = get_user_model()


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_report_list_correct(
    api_client, users, new_user, report_factory, role
):
    new_user_2 = User.objects.create(
        username='new_user_2',
        role=UserRole.USER,
        twitch_id='new_user_2',
    )

    report_factory(user=new_user)

    report = report_factory(reason=ReportReason.OTHER, other='test')
    report.created_at = timezone.now() - timedelta(days=TRC.DELTA_TWO_DAYS)
    report.save(update_fields=['created_at'])

    report_factory(user=new_user_2, status=ReportStatus.APPROVED)

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('reports-list'))

    if role in (None, UserRole.USER):
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним и обычный юзер не могут смотреть репорты'
        )
        return

    assert len(response.data) == TRC.TWO_REPORTS, (
        'Без фильтров расмотренные репорты не должны возвращаться'
    )

    assert (
        response.data[TRC.FIRST_REPORT_IDX]['created_at']
        > response.data[TRC.SECOND_REPORT_IDX]['created_at']
    ), 'По умолчанию репорты должны быть отсортированы от новых к старым'

    for report in response.data:
        if report['reason'] != ReportReason.OTHER:
            assert 'other' not in report, (
                'Пустые строки репорта не должны возвращаться в ответе'
            )
            continue

        report_fields = ['reason', 'status', 'post', 'user', 'other']
        assert set(report_fields) <= report.keys(), (
            'В репорте c причиной "other" отсутствуют поля '
            f'{set(report_fields) - report.keys()}'
        )


@pytest.mark.parametrize(
    'value',
    [ReportStatus.APPROVED, ReportStatus.REJECTED],
)
def test_report_list_filter_category(new_user, moder, report_factory, value):
    report_factory(status=ReportStatus.APPROVED)
    report_factory(new_user, status=ReportStatus.REJECTED)

    response = moder.get(reverse('reports-list'), {'status': value})

    assert len(response.data) == TRC.ONE_REPORT, (
        'Фильтр "status" не работает'
    )

    assert response.data[TRC.FIRST_REPORT_IDX]['status'] == value.value, (
        'Фильтр "status" вернул репорт с неверным значением фильтра'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_report_create_correct(
    api_client, users, new_user, post_factory, role,
):
    post = post_factory(user=new_user)

    valid_report_data = {
        'post': post.id,
        'reason': ReportReason.OTHER.value,
        'other': 'test'
    }

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('posts-report', args=[post.public_id]),
        valid_report_data,
        format='json',
    )

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может репортить'
        )
        return
    elif role in (UserRole.MODER, UserRole.STREAMER):
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Модер и стример не могут репортить'
        )
        return

    assert response.status_code == HTTPStatus.CREATED

    assert (
        response.data['message']
        == ReportConstants.MSG_CREATED.format(public_id=post.public_id)
    ), (
        'При создании репорта юзеро должно '
        'возвращаться сообщение об успешном создании'
    )

    report = Report.objects.get(post=post.id)

    assert report.user == users[role], (
        'При создании репорта его автором стал юзер, который не делал запроса'
    )

    assert report.reason == valid_report_data['reason'], (
        'При создании репорта неверно был определен "reason"'
    )

    assert report.other == valid_report_data['other'], (
        'При создании репорта неверно был определен "other"'
    )

    assert report.status == ReportStatus.NOT_VIEWED, (
        'По умолчанию при создании статус репорта должен быть "not_viewed"'
    )


def test_report_create_requeried_field(auth, new_user, post_factory):
    post = post_factory(user=new_user)

    response = auth.post(
        reverse('posts-report', args=[post.public_id]),
        {'post': post.id},
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя создать репорт без "reason"'
    )


def test_report_create_reason_other(auth, new_user, post_factory):
    post = post_factory(user=new_user)

    response = auth.post(
        reverse('posts-report', args=[post.public_id]),
        {
            'post': post.id,
            'reason': ReportReason.OTHER.value
        },
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя создать репорт с причиной "other" без сообщения'
    )


def test_report_create_cannot_the_same_post(auth, report_factory):
    report = report_factory()

    response = auth.post(
        reverse('posts-report', args=[report.post.public_id]),
        {'reason': ReportReason.ILLEGAL},
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя создать репорт на один и тот же пост дважды'
    )


def test_report_create_incorrect_reason(auth, new_user, post_factory):
    post = post_factory(user=new_user)

    response = auth.post(
        reverse('posts-report', args=[post.public_id]),
        {
            'post': post.id,
            'reason': 'test'
        },
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя создать репорт с причиной не из {ReportReason.values}'
    )


def test_report_create_incorrect_other(auth, new_user, post_factory):
    post = post_factory(user=new_user)

    response = auth.post(
        reverse('posts-report', args=[post.public_id]),
        {
            'post': post.id,
            'reason': ReportReason.OTHER,
            'other': True
        },
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя создать репорт с причиной "other" и сообщением не str'
    )


def test_report_create_by_banned(api_client, users, new_user, post_factory):
    post = post_factory(user=new_user)

    users[UserRole.USER].is_banned = True
    users[UserRole.USER].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[UserRole.USER])
    response = api_client.post(
        reverse('reports-list'),
        {
            'post': post.id,
            'reason': ReportReason.SPAM
        },
        format='json'
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может репортить'
    )


@pytest.mark.parametrize(
    'field, value',
    [
        ('post', 'test'),
        ('user', 'test'),
        ('reason', ReportReason.ILLEGAL),
        ('status', ReportStatus.APPROVED),
        ('status', ReportStatus.REJECTED),
    ],
)
@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_STAFF
)
def test_report_patch_correct(
    api_client, users, role, report_factory, field, value
):
    report = report_factory()
    old_field = getattr(report, field)

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('reports-detail', args=[report.public_id]),
        {field: value},
        format='json'
    )

    assert response.status_code == HTTPStatus.OK

    report.refresh_from_db()

    if field != 'status':
        assert getattr(report, field) == old_field, (
            f'Нельзя менять {field} репорта'
        )
        return

    assert report.moder == users[role], (
        'При обновлении репорта в "moder" должен быть присвоен текущий юзер'
    )

    assert getattr(report, field) == value, 'Статус репорта можно менять'


def test_report_patch_is_not_viewed_to_is_not_viewed(
    api_client, users, report_factory
):
    report = report_factory()

    api_client.force_authenticate(user=users[UserRole.MODER])
    response = api_client.patch(
        reverse('reports-detail', args=[report.public_id]),
        {'status': ReportStatus.NOT_VIEWED.value},
        format='json'
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя нерасмотренный репорт снова сделать нерасмотренным'
    )


@pytest.mark.parametrize(
    'value',
    [ReportStatus.APPROVED, ReportStatus.REJECTED],
)
def test_report_patch_status_to_is_not_viewed(
    api_client, users, report_factory, value
):
    report = report_factory()
    report.status = value
    report.save(update_fields=['status'])

    url = reverse('reports-detail', args=[report.public_id])

    api_client.force_authenticate(user=users[UserRole.MODER])
    response = api_client.patch(
        f'{url}?status={value}',
        {'status': ReportStatus.NOT_VIEWED.value},
        format='json'
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя расмотренный репорт снова сделать нерасмотренным'
    )


def test_report_patch_by_banned(api_client, users, report_factory):
    report = report_factory()

    users[UserRole.MODER].is_banned = True
    users[UserRole.MODER].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[UserRole.MODER])
    response = api_client.patch(
        reverse('reports-detail', args=[report.public_id]),
        {'status': ReportStatus.APPROVED},
        format='json'
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный модер не может менять статус репорта'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_STAFF,
)
def test_report_retrieve_not_allowed(api_client, users, report_factory, role):
    report = report_factory()

    api_client.force_authenticate(user=users[role])
    response = api_client.get(
        reverse('reports-detail', args=[report.public_id]),
    )

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
        'Retrieve для репорта недоступен'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_STAFF,
)
def test_report_delete_not_allowed(api_client, users, report_factory, role):
    report = report_factory()

    api_client.force_authenticate(user=users[role])
    response = api_client.delete(
        reverse('reports-detail', args=[report.public_id]),
    )

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
        'Метод delete для репорта недоступен'
    )
