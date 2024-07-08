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

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter

from users.views import UserLoginView, UserCreateView, UserResetPasswordView, ValidateResetTokenView, user_update_username
from profiles.views import ProfileViewSet
from verification_token.views import UserVerifyEmailView

from .views import ContactView
from videostore.views import get_video_url,get_poster_urls
from videostore.views import get_all_video_urls


def home_view(request):
    return HttpResponse("Welcome to the home page!")

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = [

    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', UserCreateView.as_view(), name='register'),

    path('contact/', ContactView.as_view(), name='contact'),

    path('api/verify-email/<uuid:token>/', UserVerifyEmailView.as_view(), name='verify_email'),

    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('api/password_reset/validate/', ValidateResetTokenView.as_view(), name='password_reset_validate'),
    path('api/password_reset/confirm/<str:uidb64>/<str:token>/', UserResetPasswordView.as_view(), name='password_reset_confirm'),
    
    path('api/update_username/', user_update_username, name='update_username'),

    # path('profiles/', ProfileViewSet.as_view(), name='profiles'),
    # path('profiles/<int:pk>/', ProfileViewSet.as_view(), name='profile_detail'),

    path('', include(router.urls)), 

    path('django-rq/', include('django_rq.urls')),
    
    path('get-video-url/', get_video_url, name='get_video_url'),
    path('get_poster_urls/', get_poster_urls, name='get_poster_urls'),
    path('get-all-video-urls/', get_all_video_urls, name='get_all_video_urls'),
  
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)