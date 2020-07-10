import re

from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from Account.models import User
from Movies import views


# Create your views here.
@ensure_csrf_cookie
def login(request):
    message = ''
    request.session['message'] = message
    request.session['path'] = '/account/login/'
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        remember = request.POST.get('remember', None)
        if username and password:
            username = username.strip()
            password = password.strip()
            email = re.match('\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14}', username)
            if email is None:
                request.session['username'] = username
                message = '邮箱格式不正确!'
                request.session['message'] = message
                return HttpResponseRedirect(request.session['login_from'])
            try:
                user = User.objects.filter(username=username).first()
                if user.password == password:
                    request.session['message'] = ''
                    if remember == "on":
                        request.session['username'] = username
                        request.session['password'] = password
                    return redirect(views.index)
                else:
                    message = '用户名或密码不正确!'
            except:
                message = '此用户还未注册!'

        # 登录失败回退到登录页面
        request.session['login_from'] = request.META.get('HTTP_REFERER', '/')
        if remember == "on":
            request.session['username'] = username
            request.session['password'] = password

        request.session['message'] = message
        return HttpResponseRedirect(request.session['login_from'])
    return render(request, 'Account/login.html')


def loginPage(request):
    context = {}
    if 'path' in request.session:
        path = request.session['path']
        if path != request.path:
            request.session['message'] = ''
    return render(request, 'Account/login.html', context)


def logonPage(request):
    context = {}
    if 'path' in request.session:
        path = request.session['path']
        if path != request.path:
            request.session['message'] = ''
    return render(request, 'Account/logon.html', context)


@ensure_csrf_cookie
def logon(request):
    message = ''
    request.session['path'] = '/account/logon/'
    request.session['message'] = message
    if request.method == 'POST':
        username = request.POST.get('email', None)
        password = request.POST.get('password', None)
        re_password = request.POST.get('re_password', None)
        if username and password and re_password:
            username = username.strip()
            password = password.strip()
            re_password = re_password.strip()
            request.session['login_from'] = request.META.get('HTTP_REFERER', '/')
            email = re.match('\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14}', username)
            if email is None:
                request.session['username'] = username
                message = '邮箱格式不正确!'
                request.session['message'] = message
                return HttpResponseRedirect(request.session['login_from'])

            request.session['username'] = username
            request.session['password'] = password
            if password != re_password:
                message = '两次密码输入不一致'
                request.session['message'] = message
                # 登录失败回退到登录页面
                return HttpResponseRedirect(request.session['login_from'])
            else:
                some_user_name = User.objects.filter(username=username)
                if some_user_name:
                    message = '用户名已存在'
                    request.session['message'] = message
                    return HttpResponseRedirect(request.session['login_from'])
                else:
                    user = User(username=username, password=password)
                    user.save()
                    request.session["user_id"] = user.id
                    request.session['message'] = ''
                    return redirect(views.index)

    return render(request, 'Account/logon.html')
