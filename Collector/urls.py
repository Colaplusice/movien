from django.conf.urls import url
from Collector import views

urlpatterns = [
    url(r'^log/$', views.log, name='log'),
]