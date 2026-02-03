from django.db import models
from accounts.models import Guest
from rooms.models import Room
# Create your models here.
class PaymentGateway(models.Model):
    gateway_name = models.CharField(max_length=500, blank=True, null=True)
    store_id = models.CharField(max_length=500, blank=True, null=True)
    store_pass = models.CharField(max_length=500, blank=True, null=True)
    is_sandbox = models.BooleanField( default=False)
    is_active=models.BooleanField(default=False)
    class Meta:
        verbose_name = "Payment Gateway"
        verbose_name_plural = "Payment Gateway"


class Transaction(models.Model):
    tracking_no = models.CharField(max_length=150,null=True,blank=True)
    name = models.CharField(max_length=500,null=True,blank=True)
    phone=models.CharField(max_length=11,blank=True,null=True,)
    email=models.EmailField(max_length=50,blank=True,null=True)
    nid=models.CharField(max_length=17,blank=True,null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tran_id = models.CharField(max_length=15,unique=True)
    guest=models.ForeignKey(Guest,blank=True,null=True,on_delete=models.SET_NULL)
    room=models.ManyToManyField(Room,blank=True,null=True)
    
    # Booking data fields (to survive session loss during payment redirect)
    booking_check_in = models.DateField(null=True, blank=True, help_text="Check-in date for booking")
    booking_check_out = models.DateField(null=True, blank=True, help_text="Check-out date for booking")
    booking_guests_count = models.IntegerField(default=1, help_text="Number of guests")
    booking_dates_json = models.JSONField(null=True, blank=True, help_text="Per-room booking dates as JSON")
    
    val_id = models.CharField(max_length=75)
    card_type = models.CharField(max_length=150)
    store_amount = models.DecimalField(max_digits=10, decimal_places=2)
    card_no = models.CharField(max_length=55, null=True)
    bank_tran_id = models.CharField(max_length=155, null=True)
    status = models.CharField(max_length=55)
    tran_date = models.DateTimeField()
    currency = models.CharField(max_length=10)
    card_issuer = models.CharField(max_length=255)
    card_brand = models.CharField(max_length=15)
    card_issuer_country = models.CharField(max_length=55)
    card_issuer_country_code = models.CharField(max_length=55)
    currency_rate = models.DecimalField(max_digits=10, decimal_places=2)
    verify_sign = models.CharField(max_length=155)
    verify_sign_sha2 = models.CharField(max_length=255)
    risk_level = models.CharField(max_length=15)
    risk_title = models.CharField(max_length=25)
    created_at = models.DateTimeField(auto_now_add=True, null=True)


    def __str__(self):
        return self.tran_id
