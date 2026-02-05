"""
Quick fix script for bKash credentials
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, r'd:\Django Project\rhms\rhms\rhms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rhms.settings')
django.setup()

from payment.models import PaymentGateway

# Get or create bKash gateway
gw, created = PaymentGateway.objects.get_or_create(gateway_type='bkash')

# Configure with sandbox credentials
gw.store_id = '4f6o0cjiki2rfm34kfdadl1eqq'
gw.store_pass = '2is7hdktrekvrbljjh44ll3d9l1dtjo4pasmjvs5vl5qr3fug4b'
gw.api_url = 'sandboxTokenizedUser02:sandboxTokenizedUser02@123'
gw.is_active = True
gw.is_sandbox = True
gw.save()

if created:
    print('✓ bKash gateway created and configured successfully')
else:
    print('✓ bKash gateway updated successfully')

print('\nConfiguration:')
print(f'  App Key: {gw.store_id[:20]}...')
print(f'  App Secret: {gw.store_pass[:20]}...')
print(f'  Credentials: {gw.api_url[:30]}...')
print(f'  Active: {gw.is_active}')
print(f'  Sandbox: {gw.is_sandbox}')

print('\nRun: python manage.py check_bkash')
