#this allows the urls that can be accessed in this particular app
from django.urls import path  

#from current directory use the views file
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('recorded/', views.recorded , name="recorded"),
    # path('check_transcript/', views.check_transcript, name='check_transcript'),
    
]