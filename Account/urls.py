
from django.urls import path, re_path, include
from Account import views

urlpatterns = [
    path('login/', views.loginPage, name='loginPage'),
    path('logon/', views.logonPage, name='logonPage'),
    path('login/submit/', views.login, name='login'),
    path('logon/submit/', views.logon, name='logon'),
]
