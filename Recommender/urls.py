from django.conf.urls import url
from Recommender import views

urlpatterns = [
    url(r'^chart/', views.chart, name='chart'),
    url(r'^cf/user/(?P<user_id>\w+)/$',
        views.recs_cf, name='recs_cb'),
    url(r'^mf/user/(?P<user_id>\w+)/$',
        views.recs_mf, name='recs_mf'),
    url(r'^cb/user/(?P<user_id>\w+)/$',
        views.recs_cb, name='recs_cb'),
    url(r'^hf/user/(?P<user_id>\w+)/$',
        views.recs_hf, name='recs_hf'),
    url(r'^item/user/(?P<user_id>\w+)/(?P<movie_id>\w+)/$',
        views.recs_item, name='recs_item'),
    url(r'^ar/(?P<user_id>\w+)/$',
        views.recs_using_association_rules,
        name='recs_using_association_rules')
]