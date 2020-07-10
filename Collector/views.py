from django.shortcuts import render
from django.http import HttpResponse
from Collector.models import Log
import datetime
from django.views.decorators.csrf import ensure_csrf_cookie
# Create your views here.


@ensure_csrf_cookie
def log(request):
    if request.method == 'POST':
        date = request.GET.get('date', datetime.datetime.now())
        user_id = request.POST['user_id']
        content_id = request.POST['content_id']
        event = request.POST['event_type']
        session_id = request.POST['session_id']

        # 保存到数据库
        l = Log(created=date, user_id=user_id, content_id=content_id, event=event, session_id=session_id)
        l.save()
        print("log user_id: {}, content_id: {}, event: {}".format(user_id,
                                                               str(content_id),
                                                               event))
    else:
        HttpResponse('log only works with POST')
    return HttpResponse('ok')
