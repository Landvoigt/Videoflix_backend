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

from verification_token.views import UserVerifyEmailView
from .views import ContactView

from users.views import UserLoginView, UserCreateView, UserResetPasswordView, ValidateResetTokenView, user_update_username
from profiles.views import ProfileViewSet
from videostore.views import get_poster_and_text, get_preview_video, get_full_video, create_gcs_myFilms, get_myFilms


def home_view():
    return HttpResponse("Welcome to the home page!")

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('django-rq/', include('django_rq.urls')),

    # path('full-video/', get_full_video, name='get_full_video'),
    # path('my-films/', create_gcs_myFilms, name='create_gcs_myFilms'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

api_patterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', UserCreateView.as_view(), name='register'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('update_username/', user_update_username, name='update_username'),

    path('verify_email/<uuid:token>/', UserVerifyEmailView.as_view(), name='verify_email'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('password_reset/validate/', ValidateResetTokenView.as_view(), name='password_reset_validate'),
    path('password_reset/confirm/<str:uidb64>/<str:token>/', UserResetPasswordView.as_view(), name='password_reset_confirm'),
    
    path('video/info/', get_poster_and_text, name='video_info'),
    path('video/playlist/', get_myFilms, name='get_myFilms'),
    path('video/preview/', get_preview_video, name='get_preview_video'),

    path('', include(router.urls)),
]

urlpatterns += [path('api/', include(api_patterns))]