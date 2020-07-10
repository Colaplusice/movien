"""Recs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from Movies import views

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^$', views.index, name='index'),
    re_path(r'^collect/', include('Collector.urls')),
    re_path(r'^movies/', include(('Movies.urls', 'Movies'), namespace='movies')),
    re_path(r'^rec/', include('Recommender.urls')),
    re_path(r'^account/', include(('Account.urls', 'Account'), namespace='account')),
    re_path(r'^static/(?P<path>.*)', serve, {'document_root': '/home/pi/djangosite/static'})

]
