from django.db import models
from region.models import Address
class Department(models.Model):
    serial=models.IntegerField(default=0)
    name=models.CharField(max_length=254)
    name_eng=models.CharField(max_length=254)
class Designation(models.Model):
    serial=models.IntegerField(default=0)
    name=models.CharField(max_length=254)
    name_eng=models.CharField(max_length=254)
# Create your models here.
class Guest(models.Model):
    name=models.CharField(max_length=254)
    name_eng=models.CharField(max_length=254)
    email=models.EmailField(max_length=254,blank=True,null=True)
    phone=models.CharField(max_length=11,blank=True,null=True)
    nid_number=models.CharField(max_length=17,blank=True,null=True)
    image=models.ImageField(upload_to='media/Guest/%Y/%M',blank=True,null=True,verbose_name="Guest Image")
    nid_file=models.FileField(upload_to='media/nid_file/%Y/%M',blank=True,null=True,verbose_name="NID file upload")
    address=models.ForeignKey(Address,on_delete=models.SET_NULL,null=True,blank=True)
    class Meta:
        ordering = ['name_eng']
    def __str__(self):
        return self.name+'('+self.name_eng+')'
class Staff(models.Model):
    serial=models.IntegerField(default=0)
    name=models.CharField(max_length=254)
    name_eng=models.CharField(max_length=254)
    email=models.EmailField(max_length=254,blank=True,null=True)
    phone=models.CharField(max_length=11,blank=True,null=True)
    address=models.ForeignKey(Address,on_delete=models.SET_NULL,null=True,blank=True)
    designation=models.ForeignKey(Designation,on_delete=models.SET_NULL,null=True,blank=True)
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,null=True,blank=True)
    class Meta:
        ordering = ['name_eng']
    def __str__(self):
        return self.name+'('+self.name_eng+')'

# class CommentGuest(models.Model):
#     name = models.CharField(max_length=50)
#     email = models.EmailField(max_length=100)
#     content = RichTextField()
#     post = models.ForeignKey(Post, related_name='commentsguest', on_delete=models.CASCADE)
#     date_posted = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ('-date_posted',)

#     def __str__(self):
#         return 'Comment by {}-{}'.format(self.name,self.email)