"""
bKash Payment Gateway Integration for Hotel Room Management System

This module provides functions to integrate bKash payment gateway:
1. Grant token generation
2. Payment creation
3. Payment execution
4. Payment query/verification
5. Refund (if needed)

bKash API Documentation: https://developer.bka.sh/
"""

import string
import random
import json
import requests
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from .models import PaymentGateway, Transaction
from accounts.models import Guest
from rooms.models import Room
from rhms.models import Booking
from .emails import send_booking_receipt_email


def generator_transaction_id(size=10, chars=string.ascii_uppercase + string.digits):
    """Generate a unique transaction ID"""
    return "".join(random.choice(chars) for _ in range(size))


def get_bkash_credentials():
    """Get bKash payment gateway credentials safely"""
    try:
        gateway = PaymentGateway.objects.filter(
            is_active=True,
            gateway_type='bKash'
        ).first()
        
        if gateway and gateway.store_id and gateway.store_pass:
            # Parse username and password from api_url field
            username = ''
            password = ''
            
            if gateway.api_url:
                # Expected format: username:password
                try:
                    parts = gateway.api_url.split(':', 1)
                    if len(parts) == 2:
                        username = parts[0].strip()
                        password = parts[1].strip()
                    else:
                        print(f"Warning: API URL format incorrect. Expected 'username:password', got: {gateway.api_url}")
                except Exception as e:
                    print(f"Error parsing API URL: {str(e)}")
            
            return {
                'app_key': gateway.store_id,  # App Key stored in store_id
                'app_secret': gateway.store_pass,  # App Secret stored in store_pass
                'username': username,
                'password': password,
                'base_url': 'https://tokenized.sandbox.bka.sh/v1.2.0-beta' if gateway.is_sandbox else 'https://tokenized.pay.bka.sh/v1.2.0-beta',
                'is_sandbox': gateway.is_sandbox,
                'gateway_obj': gateway
            }
    except Exception as e:
        print(f"Error fetching bKash gateway: {str(e)}")
    
    # Return sandbox credentials for testing
    return {
        'app_key': '4f6o0cjiki2rfm34kfdadl1eqq',
        'app_secret': '2is7hdktrekvrbljjh44ll3d9l1dtjo4pasmjvs5vl5qr3fug4b',
        'username': 'sandboxTokenizedUser02',
        'password': 'sandboxTokenizedUser02@123',
        'base_url': 'https://tokenized.sandbox.bka.sh/v1.2.0-beta',
        'is_sandbox': True,
        'gateway_obj': None
    }


def get_bkash_token(credentials=None):
    """
    Get authorization token from bKash
    This token is required for all subsequent API calls
    """
    if credentials is None:
        credentials = get_bkash_credentials()
    
    try:
        url = f"{credentials['base_url']}/tokenized/checkout/token/grant"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'username': credentials['username'],
            'password': credentials['password']
        }
        
        payload = {
            'app_key': credentials['app_key'],
            'app_secret': credentials['app_secret']
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200 and 'id_token' in response_data:
            print(f"✅ bKash token obtained successfully")
            return response_data['id_token']
        else:
            print(f"❌ Failed to get bKash token: {response_data}")
            return None
            
    except Exception as e:
        print(f"Error getting bKash token: {str(e)}")
        return None


def create_pending_transaction(request, guest, rooms, amount, payment_gateway='bkash'):
    """
    Create a pending transaction record before payment
    Stores all booking details for later confirmation
    """
    try:
        tran_id = generator_transaction_id()
        
        # Get booking dates from session
        check_in_str = request.session.get('check_in')
        check_out_str = request.session.get('check_out')
        guests_count = request.session.get('guests', '1')
        booking_dates = request.session.get('booking_dates', {})
        
        # Convert dates to date objects for storage
        from datetime import datetime as dt
        check_in_date = None
        check_out_date = None
        
        if check_in_str:
            try:
                check_in_date = dt.strptime(check_in_str, '%Y-%m-%d').date()
            except:
                check_in_date = timezone.now().date()
        else:
            check_in_date = timezone.now().date()
            
        if check_out_str:
            try:
                check_out_date = dt.strptime(check_out_str, '%Y-%m-%d').date()
            except:
                from datetime import timedelta
                check_out_date = check_in_date + timedelta(days=1)
        else:
            from datetime import timedelta
            check_out_date = check_in_date + timedelta(days=1)
        
        # Convert booking_dates dict to have string keys for JSON storage
        booking_dates_json = {str(k): v for k, v in booking_dates.items()} if booking_dates else {}
        
        print(f"📅 Storing booking_dates in bKash transaction: {booking_dates_json}")
        
        # Create pending transaction WITH booking data stored
        transaction = Transaction.objects.create(
            tran_id=tran_id,
            tracking_no=tran_id,
            name=guest.name if hasattr(guest, 'name') else str(guest),
            phone=guest.phone if hasattr(guest, 'phone') else '',
            email=guest.email if hasattr(guest, 'email') else '',
            guest=guest if isinstance(guest, Guest) else None,
            amount=amount,
            payment_gateway=payment_gateway,
            # STORE BOOKING DATA IN TRANSACTION
            booking_check_in=check_in_date,
            booking_check_out=check_out_date,
            booking_guests_count=int(guests_count) if guests_count else 1,
            booking_dates_json=booking_dates_json,
            status='PENDING',
            tran_date=timezone.now(),
            currency='BDT',
            store_amount=0,
            currency_rate=1.0,
        )
        
        # Add rooms to transaction
        if hasattr(rooms, '__iter__') and not isinstance(rooms, str):
            for room in rooms:
                transaction.room.add(room)
        else:
            transaction.room.add(rooms)
        
        # Store transaction details in session
        request.session['pending_tran_id'] = tran_id
        request.session['transaction_id'] = transaction.id
        request.session.modified = True
        
        print(f"Created pending bKash transaction: {tran_id} for amount: {amount}")
        return transaction
        
    except Exception as e:
        print(f"Error creating pending bKash transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def create_bkash_payment(request, transaction, token):
    """
    Create payment request in bKash
    Returns payment URL where user will be redirected
    """
    credentials = get_bkash_credentials()
    
    try:
        url = f"{credentials['base_url']}/tokenized/checkout/create"
        
        # Generate merchant invoice number
        merchant_invoice = f"INV-{transaction.tran_id}"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token,
            'X-APP-Key': credentials['app_key']
        }
        
        # Get host for callback URLs
        host = request.META.get('HTTP_HOST', 'localhost')
        protocol = 'https' if request.is_secure() else 'http'
        
        payload = {
            'mode': '0011',  # Tokenized checkout
            'payerReference': transaction.phone or '01700000000',
            'callbackURL': f"{protocol}://{host}/payment/bkash/callback/",
            'amount': str(transaction.amount),
            'currency': 'BDT',
            'intent': 'sale',
            'merchantInvoiceNumber': merchant_invoice
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        print(f"bKash create payment response: {response_data}")
        
        if response.status_code == 200 and 'paymentID' in response_data:
            # Store payment ID in transaction
            transaction.payment_id = response_data['paymentID']
            transaction.merchant_invoice_number = merchant_invoice
            transaction.save()
            
            # Return the bKash URL where user will complete payment
            bkash_url = response_data.get('bkashURL')
            print(f"✅ bKash payment created: {response_data['paymentID']}")
            return bkash_url
        else:
            print(f"❌ Failed to create bKash payment: {response_data}")
            return None
            
    except Exception as e:
        print(f"Error creating bKash payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def execute_bkash_payment(payment_id, token):
    """
    Execute/Complete the payment after user completes on bKash
    This is called from the callback
    """
    credentials = get_bkash_credentials()
    
    try:
        url = f"{credentials['base_url']}/tokenized/checkout/execute"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token,
            'X-APP-Key': credentials['app_key']
        }
        
        payload = {
            'paymentID': payment_id
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        print(f"bKash execute payment response: {response_data}")
        
        if response.status_code == 200 and response_data.get('transactionStatus') == 'Completed':
            print(f"✅ bKash payment executed successfully: {payment_id}")
            return response_data
        else:
            print(f"❌ Failed to execute bKash payment: {response_data}")
            return None
            
    except Exception as e:
        print(f"Error executing bKash payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def query_bkash_payment(payment_id, token):
    """
    Query payment status from bKash
    Used to verify payment status
    """
    credentials = get_bkash_credentials()
    
    try:
        url = f"{credentials['base_url']}/tokenized/checkout/payment/status"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token,
            'X-APP-Key': credentials['app_key']
        }
        
        payload = {
            'paymentID': payment_id
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        print(f"bKash query payment response: {response_data}")
        return response_data
        
    except Exception as e:
        print(f"Error querying bKash payment: {str(e)}")
        return None


def bkash_payment_gateway(request, guest, rooms, amount):
    """
    Initialize bKash payment gateway and create pending transaction
    Returns the payment gateway URL to redirect user to
    Returns a dict with 'error' key if there's an error, or payment URL string on success
    
    Flow:
    1. Get bKash token
    2. Create pending transaction record
    3. Create payment in bKash
    4. Return bKash payment URL for user to complete payment
    5. On success, callback will execute and confirm the payment
    """
    try:
        # Check if bKash gateway is configured
        credentials = get_bkash_credentials()
        if not credentials.get('gateway_obj'):
            print("⚠️ bKash gateway not configured, using sandbox credentials")
            return {'error': 'bKash payment gateway is not configured. Please contact administrator.'}
        
        # Get bKash token
        token = get_bkash_token()
        if not token:
            print("Failed to get bKash token")
            return {'error': 'Unable to connect to bKash. Please check gateway configuration.'}
        
        # Create pending transaction before payment
        transaction = create_pending_transaction(request, guest, rooms, amount, payment_gateway='bkash')
        if not transaction:
            print("Failed to create pending transaction")
            return {'error': 'Failed to create transaction record. Please try again.'}
        
        print(f"Initializing bKash payment for transaction: {transaction.tran_id}, Amount: {amount}")
        
        # Create payment in bKash and get payment URL
        payment_url = create_bkash_payment(request, transaction, token)
        
        if payment_url:
            # Store token in session for callback
            request.session['bkash_token'] = token
            request.session['bkash_payment_id'] = transaction.payment_id
            request.session.modified = True
            return payment_url
        else:
            print("Failed to create bKash payment")
            return {'error': 'Failed to initialize bKash payment. Please try again or use another payment method.'}
            
    except Exception as e:
        print(f"Error in bKash payment gateway: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': f'Payment gateway error: {str(e)}'}


def process_bkash_callback(request):
    """
    Process bKash payment callback
    Called after user completes payment on bKash
    Returns (transaction, booking) tuple
    """
    try:
        # Get parameters from callback
        payment_id = request.GET.get('paymentID')
        status = request.GET.get('status')
        
        print(f"bKash callback received - Payment ID: {payment_id}, Status: {status}")
        
        if not payment_id:
            print("No payment ID in callback")
            return None, None
        
        # Get token from session or regenerate
        token = request.session.get('bkash_token')
        if not token:
            token = get_bkash_token()
            if not token:
                print("Failed to get token for callback processing")
                return None, None
        
        # Find transaction by payment_id
        transaction = Transaction.objects.filter(payment_id=payment_id).first()
        if not transaction:
            print(f"Transaction not found for payment_id: {payment_id}")
            return None, None
        
        # If status is success, execute the payment
        if status == 'success':
            execution_result = execute_bkash_payment(payment_id, token)
            
            if execution_result and execution_result.get('transactionStatus') == 'Completed':
                # Update transaction with bKash response
                transaction.status = 'VALID'
                transaction.trx_id = execution_result.get('trxID')
                transaction.payment_id = execution_result.get('paymentID')
                transaction.merchant_invoice_number = execution_result.get('merchantInvoiceNumber')
                transaction.store_amount = float(execution_result.get('amount', 0))
                transaction.currency = execution_result.get('currency', 'BDT')
                transaction.tran_date = timezone.now()
                transaction.save()
                
                print(f"✅ Transaction updated with bKash confirmation: {transaction.tran_id}")
                
                # Create booking from transaction
                booking = create_booking_from_bkash_transaction(transaction, request)
                
                return transaction, booking
            else:
                # Payment execution failed
                transaction.status = 'FAILED'
                transaction.save()
                print(f"❌ Payment execution failed for: {transaction.tran_id}")
                return transaction, None
        else:
            # Payment was cancelled or failed
            transaction.status = 'CANCELLED' if status == 'cancel' else 'FAILED'
            transaction.save()
            print(f"Payment {transaction.status} for: {transaction.tran_id}")
            return transaction, None
            
    except Exception as e:
        print(f"Error processing bKash callback: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def create_booking_from_bkash_transaction(transaction, request):
    """
    Create a confirmed booking from a completed bKash transaction
    Only call this when payment is confirmed successful
    """
    try:
        if not transaction:
            print("Cannot create booking: missing transaction")
            return None
        
        # Get guest from transaction
        guest = transaction.guest
        if not guest:
            print("Cannot create booking: missing guest in transaction")
            return None
        
        # Get booking dates from transaction
        check_in = transaction.booking_check_in
        check_out = transaction.booking_check_out
        number_of_guests = transaction.booking_guests_count
        
        if not check_in or not check_out:
            print("Cannot create booking: missing dates in transaction")
            return None
        
        # Check if booking already exists for this transaction
        existing_booking = Booking.objects.filter(transaction=transaction).first()
        if existing_booking:
            print(f"Booking already exists for transaction {transaction.tran_id}: {existing_booking.id}")
            return existing_booking
        
        # Create the booking
        booking = Booking.objects.create(
            tracking_no=transaction.tran_id,
            guest=guest,
            number_of_person=str(number_of_guests),
            start_day=check_in,
            end_day=check_out,
            transaction=transaction,
            check_in_status='pending'
        )
        
        # Add rooms to booking from transaction
        room_count = 0
        for room in transaction.room.all():
            booking.room.add(room)
            room_count += 1
        
        print(f"✅ Created booking {booking.id} for bKash transaction {transaction.tran_id} with {room_count} rooms")
        send_booking_receipt_email(booking)
        return booking
        
    except Exception as e:
        print(f"Error creating booking from bKash transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def refund_bkash_payment(payment_id, trx_id, amount, reason='Customer Request'):
    """
    Refund a bKash payment
    Optional function for refund support
    """
    credentials = get_bkash_credentials()
    token = get_bkash_token(credentials)
    
    if not token:
        return None
    
    try:
        url = f"{credentials['base_url']}/tokenized/checkout/payment/refund"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token,
            'X-APP-Key': credentials['app_key']
        }
        
        payload = {
            'paymentID': payment_id,
            'trxID': trx_id,
            'amount': str(amount),
            'reason': reason,
            'sku': 'Hotel Booking Refund'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        print(f"bKash refund response: {response_data}")
        return response_data
        
    except Exception as e:
        print(f"Error refunding bKash payment: {str(e)}")
        return None
