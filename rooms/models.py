from django.db import models
from ckeditor.fields import RichTextField
from accounts.models import Comment
# Create your models here.
class BedType(models.Model):
    serial=models.IntegerField(default=0)
    name=models.CharField(max_length=100,unique=True)
    name_eng=models.CharField(max_length=100,unique=True)
    description=models.CharField(max_length=500,blank=True,null=True)
    occupancy=models.CharField(max_length=100,blank=True,null=True)
    def __str__(self):
        return self.name+'('+self.name_eng+')'
class RoomType(models.Model):
    serial=models.IntegerField(default=0)
    name=models.CharField(max_length=100,unique=True)
    name_eng=models.CharField(max_length=100,unique=True)
    description=RichTextField(blank=True,null=True)
    occupancy=models.CharField(max_length=100,blank=True,null=True)
    bed_type=models.ManyToManyField(BedType,blank=True,null=True)
    price=models.CharField(max_length=10,blank=True,null=True)
    services=models.CharField(max_length=500,blank=True,null=True)
    comment=models.ManyToManyField(Comment,blank=True,null=True)
    main_image=models.FileField(upload_to='media/room_type_images',blank=True,null=True,)
    second_image=models.FileField(upload_to='media/room_type_images',blank=True,null=True,)
    def __str__(self):
        return self.name+'('+self.name_eng+')'
class Room(models.Model):
    serial=models.IntegerField(default=0)
    name=models.CharField(max_length=100,unique=True)
    name_eng=models.CharField(max_length=100,unique=True)
    room_no=models.CharField(max_length=100,unique=True)
    room_type=models.ForeignKey(RoomType,blank=True,null=True,on_delete=models.SET_NULL)
    bed_type=models.ForeignKey(BedType,blank=True,null=True,on_delete=models.SET_NULL)
    status=models.CharField(max_length=100,blank=True,null=True)
    price=models.CharField(max_length=10,blank=True,null=True)
    person_occupancy=models.CharField(max_length=10,blank=True,null=True)
    number_of_beds=models.CharField(max_length=10,blank=True,null=True)
    size=models.CharField(max_length=10,blank=True,null=True)
    services=models.CharField(max_length=500,blank=True,null=True)
    description=RichTextField(blank=True,null=True)
    comment=models.ManyToManyField(Comment,blank=True,null=True)
    main_image=models.FileField(upload_to='media/room_images',blank=True,null=True,)
    second_image=models.FileField(upload_to='media/room_images',blank=True,null=True,)
    is_available=models.BooleanField(default=False)
    class Meta:
        ordering = ['serial']
    def __str__(self):
        return self.name+'('+self.name_eng+')'


class RoomReview(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.room.name_eng} - {self.rating}★ by {self.name}"
    
