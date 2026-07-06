from django.http import HttpResponse
import datetime


def auth_twitch(request):
    now = datetime.datetime.now()
    html = '<html lang="en"><body>dfIt is now %s.</body></html>' % now
    return HttpResponse(html)


def auth_twitch_callback(request):
    now = datetime.datetime.now()
    html = '<html lang="en"><body>dfIt is now %s.</body></html>' % now
    return HttpResponse(html)
