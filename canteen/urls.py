from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from canteenapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.home,name='home'),
    path('userlogin/',views.index,name='index'),
    path('sendverificationcode/',views.sendverificationcode,name='sendverificationcode'),
    path('loginverification/',views.loginverification,name='loginverification'),
    path('signupverification/',views.signupverification,name='signupverification'),
    path('loginverifymail/',views.loginverifymail,name='loginverifymail'),
    path('adminlogin/',views.adminlogin,name='adminlogin'),
    path('admindashboard/',views.admindashboard,name='admindashboard'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('accounts/', include('allauth.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
