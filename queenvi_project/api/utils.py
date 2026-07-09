from http import HTTPStatus

from rest_framework.response import Response


def date_to_json(value, status=HTTPStatus.BAD_REQUEST, key='error'):
    return Response({key: value}, status=status)
