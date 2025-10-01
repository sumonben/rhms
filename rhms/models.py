from django.db import models
from region.models import Upazilla, District
class HotelDetails(models.Model):
    serial=models.IntegerField(default=10)
    title=models.CharField(max_length=100,unique=True)
    title_en=models.CharField(max_length=100,unique=True)
    slogan=models.CharField(max_length=100,unique=True)
    slogan_en=models.CharField(max_length=100,unique=True)
    license_no=models.CharField(max_length=25,unique=True)
    upazilla=models.ForeignKey(Upazilla, on_delete=models.CASCADE,blank=True,null=True)
    district=models.ForeignKey(District, on_delete=models.CASCADE,blank=True,null=True)
    logo=models.FileField(upload_to='media/logo',blank=True,null=True,)
    logo_en=models.FileField(upload_to='media/logo',blank=True,null=True,)
    logo_opacity=models.FileField(upload_to='media/logo',blank=True,null=True,)
    logo_opacity_en=models.FileField(upload_to='media/logo',blank=True,null=True,)
    monogram=models.FileField(upload_to='media/logo',blank=True,null=True)
    monogram_en=models.FileField(upload_to='media/logo',blank=True,null=True)
    link=models.URLField(max_length=200, blank=True, null=True)
    class Meta:
        ordering = ['title_en']
        verbose_name="প্রতিষ্ঠানের বিবরণ"
        verbose_name_plural="প্রতিষ্ঠানের বিবরণ"

    def __str__(self):
        return self.title+'('+self.title_en+')'