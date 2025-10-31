from django.db import models
from region.models import Upazilla, District
from payment.models import  Transaction
from rooms.models import  Room
from accounts.models import  Guest

class Carousel(models.Model):
    serial=models.IntegerField(default=10)
    title=models.CharField(max_length=250,unique=True)
    title_en=models.CharField(max_length=250,unique=True)
    sub_title=models.CharField(max_length=250,blank=True,null=True)
    sub_title_en=models.CharField(max_length=250,blank=True,null=True)
    description=models.CharField(max_length=1000,blank=True,null=True)
    image=models.FileField(upload_to='media/carousel',blank=True,null=True,)
    def __str__(self):
        return self.title+'('+self.title_en+')'
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
class Booking(models.Model):
        tracking_no = models.CharField(max_length=150,null=True,blank=True)
        room=models.ManyToManyField(Room, blank=True,null=True)
        guest=models.ForeignKey(Guest, on_delete=models.SET_NULL,null=True,blank=True)
        number_of_person=models.CharField(max_length=10,null=True,blank=True)
        start_day=models.DateField(auto_now=False, auto_now_add=False)
        end_day=models.DateField(auto_now=False, auto_now_add=False)
        transaction=models.ForeignKey(Transaction, on_delete=models.SET_NULL,null=True,blank=True)
        booked_on=models.DateTimeField(auto_now=True, auto_now_add=False)
        def __str__(self):
            return "Booking ID: "+str(self.id)
        @property
        def is_past_due(self):
            return date.today()>self.end_day
        def guest_details(self):
            if self.guest is not None:
                return format_html('<a href="%s" target="_blank">%s</a>' % (reverse("admin:accounts_guest_change", args=(self.guest.id,)) , escape(self.guest.name_eng)))
            else:
                return None
        guest_details.allow_tags=True
        def transaction_details(self):
            if self.transaction is not None:
                return format_html('<a href="%s" target="_blank">%s</a>' % (reverse("admin:payment_transaction_change", args=(self.transaction.id,)) , escape(self.transaction.tracking_no)))
            else:
                return None
        transaction_details.allow_tags=True