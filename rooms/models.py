from django.db import models

# Create your models here.
class RoomType(models.Model):
    serial=models.IntegerField(default=0)
    name=models.CharField(max_length=100,unique=True)
    name_eng=models.CharField(max_length=100,unique=True)
    description=models.CharField(max_length=500,blank=True,null=True)
    occupancy=models.CharField(max_length=10,blank=True,null=True)
class Room(models.Model):
    serial=models.IntegerField(default=0)
    name=models.CharField(max_length=100,unique=True)
    name_eng=models.CharField(max_length=100,unique=True)
    room_no=models.CharField(max_length=100,unique=True)
    room_type=models.ForeignKey(RoomType,blank=True,null=True,on_delete=models.CASCADE)
    status=models.CharField(max_length=100,blank=True,null=True)
    price=models.CharField(max_length=10,blank=True,null=True)
    person_occupancy=models.CharField(max_length=10,blank=True,null=True)
    main_image=models.FileField(upload_to='media/room_images',blank=True,null=True,)
    second_image=models.FileField(upload_to='media/room_images',blank=True,null=True,)
