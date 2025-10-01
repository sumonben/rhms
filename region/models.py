from django.db import models

# Create your models here.

class Division(models.Model):
    name=models.CharField(max_length=25,unique=True)
    name_en=models.CharField(max_length=25,unique=True)
    link=models.CharField(max_length=55,null=True,blank=True)
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name+'('+self.name_en+')'

class District(models.Model):
    name=models.CharField(max_length=25,unique=True)
    name_en=models.CharField(max_length=25,unique=True)
    lattitude=models.CharField(max_length=15,blank=True,null=True)
    longitude=models.CharField(max_length=15, blank=True,null=True)
    division=models.ForeignKey(Division, on_delete=models.CASCADE,blank=True,null=True)
    link=models.CharField(max_length=55,null=True,blank=True)
    class Meta:
        ordering = ['name_en']
    def __str__(self):
        return self.name+'('+self.name_en+')'

class Upazilla(models.Model):
    name=models.CharField(max_length=25)
    name_en=models.CharField(max_length=25)
    district=models.ForeignKey(District, on_delete=models.CASCADE,blank=True,null=True)
    link=models.CharField(max_length=55,null=True,blank=True)
    class Meta:
        ordering = ['name_en']
    def __str__(self):
        return self.name+'('+self.name_en+')'

class Union(models.Model):
    name=models.CharField(max_length=25)
    name_en=models.CharField(max_length=25)
    upazilla=models.ForeignKey(Upazilla, on_delete=models.CASCADE,blank=True,null=True)
    link=models.CharField(max_length=55,null=True,blank=True)

    class Meta:
        ordering = ['name_en']
    def __str__(self):
        return self.name+'('+self.name_en+')'




class Address(models.Model):
    serial=models.IntegerField(default=10)
    ward=models.CharField(max_length=50,blank=True,null=True,verbose_name="ওয়ার্ড নং ")
    village_or_street=models.CharField(max_length=50,blank=True,null=True,verbose_name=" গ্রাম/মহল্লা")
    post_office=models.CharField(max_length=50,blank=True,null=True,verbose_name="ডাকঘর ")
    division=models.ForeignKey(Division, on_delete=models.CASCADE,blank=True,null=True,verbose_name=" বিভাগ ")
    district=models.ForeignKey(District,blank=True,null=True,on_delete=models.SET_NULL,verbose_name=" জেলা ")
    upazilla=models.ForeignKey(Upazilla,blank=True,null=True,on_delete=models.SET_NULL,verbose_name="উপজেলা ")
    Others=models.CharField(max_length=500,blank=True,null=True,verbose_name="অন্য ঠিকানা ")

    class Meta:
        ordering = ['serial']
        verbose_name="ঠিকানা"
        verbose_name_plural="ঠিকানা"
    def __str__(self):
        if self.village_or_street:
            return self.village_or_street.name
        else:
            return '1'