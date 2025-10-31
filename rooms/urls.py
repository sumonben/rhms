from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.Rooms.as_view(),name='rooms_view'),
    path('room_details/<int:id>/', views.RoomDetails.as_view(),name="room_details"),
    # path('rooms/', include('rooms.urls')),

]