import string
import random
from django.conf import settings
from sslcommerz_lib import SSLCOMMERZ
from .models import PaymentGateway

# Get gateway settings safely
gateway = PaymentGateway.objects.filter(is_active=True).first()

if gateway:
    cradentials = {'store_id': gateway.store_id,
                'store_pass': gateway.store_pass, 'issandbox': gateway.is_sandbox}
else:
    # Default credentials for development
    cradentials = {'store_id': 'test',
                'store_pass': 'test', 'issandbox': True}
  
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
    
    # Store transaction ID in session for later use
    request.session['pending_tran_id'] = body['tran_id']
    
    body['success_url'] ='http://' +str(request.META['HTTP_HOST'])+'/payment/success/'
    body['fail_url'] = 'http://' +str(request.META['HTTP_HOST'])+'/payment/failed/'
    body['cancel_url'] = 'http://' +str(request.META['HTTP_HOST'])+'/payment/canceled/'
    body['ipn_url'] = 'http://' +str(request.META['HTTP_HOST'])+'/payment/ipn/'
    body['emi_option'] = 0
    body['cus_name'] = guest.name if hasattr(guest, 'name') else str(guest)
    body['cus_email'] = guest.email if hasattr(guest, 'email') else 'guest@hotel.com'
    body['cus_phone'] = guest.phone if hasattr(guest, 'phone') else '01712539569'
    body['cus_add1'] = str(guest.address) if hasattr(guest, 'address') else 'Dhaka, Bangladesh'
    body['cus_city'] = 'Dhaka'
    body['cus_country'] = 'Bangladesh'
    body['shipping_method'] = "NO"
    body['multi_card_name'] = ""
    body['num_of_item'] = room.count() if hasattr(room, 'count') else 1
    body['product_name'] = "Hotel Room Booking"
    body['product_category'] = "Hotel Services"
    body['product_profile'] = "general"
    
    # Pass data through value fields
    body['value_a'] = request.session.get('guests', '1')  # Number of guests
    body['value_b'] = str(guest.id) if hasattr(guest, 'id') else '0'  # Guest ID
    
    # Store room IDs as comma-separated string
    if hasattr(room, '__iter__'):
        room_ids = ','.join([str(r.id) for r in room])
    else:
        room_ids = str(room.id)
    body['value_c'] = room_ids  # Room IDs
    body['value_d'] = str(amount)  # Amount
    
    
    try:
        response = sslcommez.createSession(body)
        print("Payment gateway response:", response)
    except Exception as e:
        print("Payment gateway error:", str(e))
        response = None
    
    # Return the payment gateway URL
    if response:
        if "GatewayPageURL" in response:
            return response["GatewayPageURL"]
        elif "sessionkey" in response:
            # Fallback for different response format
            sandbox = cradentials.get('issandbox', True)
            if sandbox:
                return 'https://sandbox.sslcommerz.com/gwprocess/v4/gw.php?Q=pay&SESSIONKEY=' + response["sessionkey"]
            else:
                return 'https://securepay.sslcommerz.com/gwprocess/v4/api.php?Q=pay&SESSIONKEY=' + response["sessionkey"]
        else:
            # Response exists but doesn't have expected format
            print("Unexpected payment gateway response format:", response)
    
    # If payment gateway fails, return test payment page
    print("Payment gateway not configured properly. Using test mode.")
    # Return a test payment URL (you should configure PaymentGateway in admin first)
    return 'https://sandbox.sslcommerz.com/testServer/testcart/'


