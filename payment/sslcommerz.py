import string
import random
from django.conf import settings
from sslcommerz_lib import SSLCOMMERZ
from .models import PaymentGateway

gateway = PaymentGateway.objects.filter(is_active=True).first()
cradentials = {'store_id': gateway.store_id,
            'store_pass': gateway.store_pass, 'issandbox': gateway.is_sandbox}
  
def generator_trangection_id( size=10, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


    

def sslcommerz_payment_gateway(request, guest, room, amount):
    
    # gateway = PaymentGateway.objects.all().first()
    
    # cradentials = {'store_id': 'ictparkbd0live ',
    #         'store_pass': '68045F6E0BDD747715', 'issandbox': False}
    sslcommez = SSLCOMMERZ(cradentials)
    body = {}
    body['guest'] = guest
    body['total_amount'] = amount
    body['currency'] = "BDT"
    body['tran_id'] = generator_trangection_id()
    body['success_url'] ='https://' +str(request.META['HTTP_HOST'])+'/payment/success/'
    body['fail_url'] = 'https://' +str(request.META['HTTP_HOST'])+'/payment/failed/'
    body['cancel_url'] = 'https://' +str(request.META['HTTP_HOST'])+'/payment/canceled/'
    body['ipn_url'] = 'https://' +str(request.META['HTTP_HOST'])+'/payment/ipn/'
    body['emi_option'] = 0
    body['cus_name'] = guest.name
    body['cus_email'] = 'request.data["email"]'
    body['cus_phone'] = '01712539569'
    body['cus_add1'] = 'request.data["address"]'
    body['cus_city'] = 'request.data["address"]'
    body['cus_country'] = 'Bangladesh'
    body['shipping_method'] = "NO"
    body['multi_card_name'] = ""
    body['num_of_item'] = 1
    body['product_name'] = "Test"
    body['product_category'] = "Test Category"
    body['product_profile'] = "general"
    body['value_a'] = 1
    body['value_b'] =guest
    body['value_c'] = room
    body['value_d'] = amount
    
    


    response = sslcommez.createSession(body)
    print(response)   
    # return  response["GatewayPageURL"]
    return 'https://sandbox.sslcommerz.com/gwprocess/v4/gw.php?Q=pay&SESSIONKEY=' + response["sessionkey"]
    return 'https://securepay.sslcommerz.com/gwprocess/v4/api.php?Q=pay&SESSIONKEY=' + response["sessionkey"]

