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