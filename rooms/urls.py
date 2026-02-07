from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.Rooms.as_view(),name='rooms_view'),
    path('room_details/<int:id>/', views.RoomDetails.as_view(),name="room_details"),
    path('room_details/<int:id>/review/', views.RoomReviewSubmitView.as_view(), name='room_review'),
    path('room_type_rooms/<int:id>/', views.RoomTypeRooms.as_view(),name="room_type_rooms"),
    # path('rooms/', include('rooms.urls')),

]