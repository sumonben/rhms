"""
Django management command to check bKash payment gateway configuration
Usage: python manage.py check_bkash
"""

from django.core.management.base import BaseCommand
from payment.models import PaymentGateway
from payment.bkash import get_bkash_token


class Command(BaseCommand):
    help = 'Check bKash payment gateway configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('bKash Payment Gateway Configuration Check'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write('')
        
        # Check if bKash gateway exists
        try:
            gateway = PaymentGateway.objects.filter(gateway_type='bkash').first()
            
            if not gateway:
                self.stdout.write(self.style.ERROR('❌ No bKash gateway configured'))
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('To configure bKash:'))
                self.stdout.write('1. Go to Django Admin: http://localhost:8000/admin/payment/paymentgateway/')
                self.stdout.write('2. Add new Payment Gateway')
                self.stdout.write('3. Fill in:')
                self.stdout.write('   - Gateway Type: bkash')
                self.stdout.write('   - Is Active: ✓')
                self.stdout.write('   - Store ID: Your bKash App Key')
                self.stdout.write('   - Store Password: Your bKash App Secret')
                self.stdout.write('   - API URL: username:password (e.g., sandboxTokenizedUser02:sandboxTokenizedUser02@123)')
                self.stdout.write('   - Is Sandbox: ✓ (for testing)')
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('Get credentials from: https://developer.bka.sh/'))
                return
            
            # Display current configuration
            self.stdout.write(self.style.SUCCESS('✓ bKash gateway found'))
            self.stdout.write('')
            self.stdout.write(f'Gateway ID: {gateway.id}')
            self.stdout.write(f'Is Active: {"✓" if gateway.is_active else "✗"}')
            self.stdout.write(f'Environment: {"Sandbox" if gateway.is_sandbox else "Production"}')
            self.stdout.write(f'App Key: {gateway.store_id[:10]}...' if gateway.store_id else 'App Key: Not set')
            self.stdout.write(f'App Secret: {gateway.store_pass[:10]}...' if gateway.store_pass else 'App Secret: Not set')
            self.stdout.write(f'Credentials: {"Set" if gateway.api_url else "Not set"}')
            self.stdout.write('')
            
            # Check if gateway is active
            if not gateway.is_active:
                self.stdout.write(self.style.ERROR('❌ Gateway is not active'))
                self.stdout.write(self.style.WARNING('Enable it in Django Admin'))
                return
            
            # Check if credentials are set
            if not gateway.store_id or not gateway.store_pass or not gateway.api_url:
                self.stdout.write(self.style.ERROR('❌ Credentials incomplete'))
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('Missing:'))
                if not gateway.store_id:
                    self.stdout.write('  - Store ID (App Key)')
                if not gateway.store_pass:
                    self.stdout.write('  - Store Password (App Secret)')
                if not gateway.api_url:
                    self.stdout.write('  - API URL (username:password)')
                return
            
            self.stdout.write(self.style.SUCCESS('✓ All credentials configured'))
            self.stdout.write('')
            
            # Test token generation
            self.stdout.write('Testing token generation...')
            token = get_bkash_token()
            
            if token:
                self.stdout.write(self.style.SUCCESS('✓ Token generated successfully'))
                self.stdout.write(f'Token: {token[:20]}...')
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=' * 60))
                self.stdout.write(self.style.SUCCESS('bKash gateway is properly configured and working!'))
                self.stdout.write(self.style.SUCCESS('=' * 60))
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to generate token'))
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('Possible issues:'))
                self.stdout.write('  - Incorrect App Key or App Secret')
                self.stdout.write('  - Incorrect username/password format')
                self.stdout.write('  - Network connectivity issues')
                self.stdout.write('  - bKash API service down')
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('For sandbox testing, use:'))
                self.stdout.write('  App Key: 4f6o0cjiki2rfm34kfdadl1eqq')
                self.stdout.write('  App Secret: 2is7hdktrekvrbljjh44ll3d9l1dtjo4pasmjvs5vl5qr3fug4b')
                self.stdout.write('  API URL: sandboxTokenizedUser02:sandboxTokenizedUser02@123')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error checking configuration: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
