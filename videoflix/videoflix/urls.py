"""
URL configuration for videoflix project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path, include
from django.http import HttpResponse

from users.views import UserLoginView, UserCreateView, UserResetPasswordView, user_update_username
from django.conf import settings
from django.conf.urls.static import static

def home_view(request):
    return HttpResponse("Welcome to the home page!")

urlpatterns = [

    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    
    path('login/', UserLoginView.as_view(), name='login'),
    path('registry/', UserCreateView.as_view(), name='registry'),

    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('api/password_reset/confirm/<str:uidb64>/<str:token>/', UserResetPasswordView.as_view(), name='password_reset_confirm'),
    
    path('api/update_username/', user_update_username, name='update_username'),

    path('django-rq/', include('django_rq.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)