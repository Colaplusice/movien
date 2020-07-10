from django.urls import path, re_path
from Movies import views

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^movie/(?P<movie_id>\d+)/$', views.detail, name='detail'),
    re_path(r'^search/$', views.search_for_movie, name='search_for_movie'),
]
