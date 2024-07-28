
from django.contrib import admin
from django.urls import path
from .views import login_view, send_email_view

urlpatterns = [
    path('adminpanel/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('send-email/', send_email_view, name='send_email'),
    
]
