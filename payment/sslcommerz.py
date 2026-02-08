import string
import random
import json
import hashlib
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from .models import PaymentGateway, Transaction
from accounts.models import Guest
from rooms.models import Room
from rhms.models import Booking

try:
    from sslcommerz_lib import SSLCOMMERZ
    SSLCOMMERZ_AVAILABLE = True
except ImportError:
    SSLCOMMERZ_AVAILABLE = False

gateway = PaymentGateway.objects.filter(is_active=True).first()
cradentials = {'store_id': gateway.store_id,
            'store_pass': gateway.store_pass, 'issandbox': gateway.is_sandbox}
  
def generator_transaction_id(size=10, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


# Backward-compatibility for legacy typo usages
def generator_trangection_id(size=10, chars=string.ascii_uppercase + string.digits):
    return generator_transaction_id(size=size, chars=chars)


def get_payment_credentials():
    """Get payment gateway credentials safely"""
    try:
        gateway = PaymentGateway.objects.filter(is_active=True).first()
        if gateway and gateway.store_id and gateway.store_pass:
            return {
                'store_id': gateway.store_id,
                'store_pass': gateway.store_pass,
                'is_sandbox': gateway.is_sandbox,
                'gateway_obj': gateway
            }
    except Exception as e:
        print(f"Error fetching payment gateway: {str(e)}")
    
    # Return test credentials for sandbox mode
    return {
        'store_id': 'testbox',
        'store_pass': 'qwerty',
        'is_sandbox': True,
        'gateway_obj': None
    }


def create_pending_transaction(request, guest, rooms, amount):
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
        
        print(f"📅 Storing booking_dates in transaction: {booking_dates_json}")
        
        transaction_data = {
            'tran_id': tran_id,
            'tracking_no': tran_id,
            'name': guest.name if hasattr(guest, 'name') else str(guest),
            'phone': guest.phone if hasattr(guest, 'phone') else '',
            'email': guest.email if hasattr(guest, 'email') else '',
            'guest': guest if isinstance(guest, Guest) else None,
            'amount': amount,
            # STORE BOOKING DATA IN TRANSACTION
            'booking_check_in': check_in_date,
            'booking_check_out': check_out_date,
            'booking_guests_count': int(guests_count) if guests_count else 1,
            'booking_dates_json': booking_dates_json,
            'val_id': '',
            'card_type': '',
            'store_amount': 0,
            'card_no': '',
            'bank_tran_id': '',
            'status': 'PENDING',
            'tran_date': timezone.now(),
            'currency': 'BDT',
            'card_issuer': '',
            'card_brand': '',
            'card_issuer_country': '',
            'card_issuer_country_code': '',
            'currency_rate': 1.0,
            'verify_sign': '',
            'verify_sign_sha2': '',
            'risk_level': '0',
            'risk_title': '',
        }

        try:
            transaction = Transaction.objects.create(**transaction_data)
        except Exception as e:
            error_text = str(e).lower()
            if 'no such column' in error_text or 'unknown column' in error_text:
                # Fallback for databases missing booking_* fields
                for key in ['booking_check_in', 'booking_check_out', 'booking_guests_count', 'booking_dates_json']:
                    transaction_data.pop(key, None)
                transaction = Transaction.objects.create(**transaction_data)
            else:
                raise
        
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
        
        print(f"Created pending transaction: {tran_id} for amount: {amount}, Guest: {guest.name if hasattr(guest, 'name') else 'Unknown'}")
        print(f"  Booking dates STORED IN TRANSACTION: {check_in_date} to {check_out_date}, Guests: {guests_count}")
        return transaction
        
    except Exception as e:
        print(f"Error creating pending transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def create_booking_from_transaction(transaction, check_in=None, check_out=None, number_of_guests='1'):
    """
    Create a confirmed booking from a completed transaction
    Only call this when payment is confirmed successful
    """
    try:
        if not transaction:
            print("Cannot create booking: missing transaction")
            return None
        
        # Get guest from transaction or return None
        guest = transaction.guest
        if not guest:
            print("Cannot create booking: missing guest in transaction")
            return None
        
        # Parse dates properly
        from datetime import datetime as dt
        if check_in:
            if isinstance(check_in, str):
                try:
                    check_in = dt.strptime(check_in, '%Y-%m-%d').date()
                except Exception as e:
                    print(f"Error parsing check_in date: {e}")
                    check_in = timezone.now().date()
        else:
            check_in = timezone.now().date()
            
        if check_out:
            if isinstance(check_out, str):
                try:
                    check_out = dt.strptime(check_out, '%Y-%m-%d').date()
                except Exception as e:
                    print(f"Error parsing check_out date: {e}")
                    check_out = timezone.now().date()
        else:
            check_out = timezone.now().date()
        
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
        
        print(f"Created booking {booking.id} for transaction {transaction.tran_id} with {room_count} rooms")
        return booking
        
    except Exception as e:
        print(f"Error creating booking from transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def sslcommerz_payment_gateway(request, guest, rooms, amount):
    """
    Initialize SSL Commerz payment gateway and create pending transaction
    Returns the payment gateway URL to redirect user to
    
    Flow:
    1. Create pending transaction record
    2. Initialize SSL Commerz session with transaction details
    3. Return payment URL for user to complete payment
    4. On success, payment callback will create the booking
    """
    try:
        # Get gateway credentials (fallback to sandbox if not configured)
        creds = get_payment_credentials()
        store_id = creds['store_id']
        store_pass = creds['store_pass']
        is_sandbox = creds['is_sandbox']
        
        # Create pending transaction before payment
        transaction = create_pending_transaction(request, guest, rooms, amount)
        if not transaction:
            print("Failed to create pending transaction")
            return None
        
        print(f"Initializing payment for transaction: {transaction.tran_id}, Amount: {amount}")
        
        # Build payment form body
        body = {
            'total_amount': str(amount),
            'currency': 'BDT',
            'tran_id': transaction.tran_id,
            'success_url': f"{settings.SITE_URL}/payment/success/",
            'fail_url': f"{settings.SITE_URL}/payment/failed/",
            'cancel_url': f"{settings.SITE_URL}/payment/canceled/",
            'ipn_url': f"{settings.SITE_URL}/payment/ipn/",
            'emi_option': 0,
            'cus_name': getattr(guest, 'name', 'Guest'),
            'cus_email': getattr(guest, 'email', 'guest@hotel.com'),
            'cus_phone': getattr(guest, 'phone', '01700000000'),
            'cus_add1': str(getattr(guest, 'address', 'Dhaka')),
            'cus_city': 'Dhaka',
            'cus_country': 'Bangladesh',
            'cus_state': 'Dhaka',
            'shipping_method': 'NO',
            'num_of_item': 1,
            'product_name': 'Hotel Room Booking',
            'product_category': 'Hotel Services',
            'product_profile': 'general',
            # Custom data to retrieve after payment
            'value_a': request.session.get('guests', '1'),  # Number of guests
            'value_b': str(guest.id) if hasattr(guest, 'id') else '0',  # Guest ID
            'value_c': ','.join([str(r.id) for r in (rooms if hasattr(rooms, '__iter__') and not isinstance(rooms, str) else [rooms])]),  # Room IDs
            'value_d': str(amount),  # Total amount
        }
        
        # Try to initialize SSL Commerz payment session
        if SSLCOMMERZ_AVAILABLE and is_sandbox is not None:
            try:
                sslcommez = SSLCOMMERZ({
                    'store_id': store_id,
                    'store_pass': store_pass,
                    'issandbox': is_sandbox
                })
                
                response = sslcommez.createSession(body)
                print(f"SSL Commerz response: {response}")
                
                if response:
                    # Check for GatewayPageURL in response
                    if isinstance(response, dict):
                        if 'GatewayPageURL' in response:
                            return response['GatewayPageURL']
                        elif 'sessionkey' in response:
                            # Build payment URL from session key
                            sessionkey = response['sessionkey']
                            if is_sandbox:
                                return f"https://sandbox.sslcommerz.com/gwprocess/v4/gw.php?Q=pay&SESSIONKEY={sessionkey}"
                            else:
                                return f"https://securepay.sslcommerz.com/gwprocess/v4/api.php?Q=pay&SESSIONKEY={sessionkey}"
                        elif 'status' in response and response['status'] == 'FAILED':
                            print(f"SSL Commerz session creation failed: {response.get('failedreason')}")
                    elif isinstance(response, str) and 'https' in response:
                        return response
                
            except Exception as e:
                print(f"SSL Commerz error: {str(e)}")
                import traceback
                traceback.print_exc()
        # Fallback: Use SSL Commerz sandbox test server
        print("Using SSL Commerz sandbox test server")
        # This test server allows you to complete payment without a real gateway
        return 'https://sandbox.sslcommerz.com/testServer/testcart/'
        
    except Exception as e:
        print(f"Payment gateway initialization error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def process_payment_callback(data, request=None):
    """
    Process payment callback from SSL Commerz IPN
    Returns tuple of (transaction, booking)
    
    Called when:
    1. User returns from SSL Commerz payment page (success/fail/cancel)
    2. SSL Commerz sends IPN notification (webhook)
    
    If payment is VALID, creates booking automatically
    """
    try:
        tran_id = data.get('tran_id')
        status = data.get('status', 'UNKNOWN')
        
        if not tran_id:
            print("No transaction ID in callback")
            return None, None
        
        # Get existing transaction
        transaction = Transaction.objects.filter(tran_id=tran_id).first()
        
        # Check if already processed with booking
        if transaction and transaction.status == 'VALID':
            existing_booking = Booking.objects.filter(transaction=transaction).first()
            if existing_booking:
                print(f"Transaction {tran_id} already has booking {existing_booking.id}")
                return transaction, existing_booking
        
        # Create transaction if doesn't exist
        if not transaction:
            transaction = Transaction.objects.create(
                tran_id=tran_id,
                tracking_no=tran_id,
                amount=float(data.get('amount', 0)),
                name=data.get('cus_name', 'Guest'),
                email=data.get('cus_email', ''),
                phone=data.get('cus_phone', ''),
                status='PENDING',
                val_id='',
                card_type='',
                store_amount=0,
                tran_date=timezone.now(),
                currency='BDT',
                card_issuer='',
                card_brand='',
                card_issuer_country='',
                card_issuer_country_code='',
                currency_rate=1.0,
                verify_sign='',
                verify_sign_sha2='',
                risk_level='0',
                risk_title='',
            )
            print(f"Created new transaction: {tran_id}")
        
        # Update transaction with callback response
        transaction.status = status
        transaction.val_id = data.get('val_id', '')
        transaction.card_type = data.get('card_type', '')
        transaction.card_no = data.get('card_no', '')
        transaction.card_issuer = data.get('card_issuer', '')
        transaction.card_brand = data.get('card_brand', '')
        transaction.bank_tran_id = data.get('bank_tran_id', '')
        transaction.tran_date = timezone.now()
        transaction.currency = data.get('currency', 'BDT')
        transaction.card_issuer_country = data.get('card_issuer_country', '')
        transaction.card_issuer_country_code = data.get('card_issuer_country_code', '')
        transaction.currency_rate = float(data.get('currency_rate', 1.0))
        transaction.risk_level = data.get('risk_level', '0')
        transaction.risk_title = data.get('risk_title', '')
        transaction.verify_sign = data.get('verify_sign', '')
        transaction.verify_sign_sha2 = data.get('verify_sign_sha2', '')
        transaction.store_amount = float(data.get('store_amount', 0))
        
        # Get guest from custom data
        guest_id = data.get('value_b')
        guest = None
        if guest_id:
            try:
                guest = Guest.objects.get(id=int(guest_id))
                if not transaction.guest:
                    transaction.guest = guest
                print(f"Guest linked: {guest.name} (ID: {guest.id})")
            except (Guest.DoesNotExist, ValueError) as e:
                print(f"Error getting guest: {str(e)}")
        
        transaction.save()
        print(f"Transaction updated: {tran_id} - Status: {status}")
        
        # Add rooms to transaction if not already added
        if transaction.room.count() == 0:
            room_ids_str = data.get('value_c', '')
            if room_ids_str:
                try:
                    room_ids = [int(rid.strip()) for rid in room_ids_str.split(',') if rid.strip().isdigit()]
                    rooms = Room.objects.filter(id__in=room_ids)
                    for room in rooms:
                        transaction.room.add(room)
                    print(f"Added {rooms.count()} rooms to transaction")
                except Exception as e:
                    print(f"Error adding rooms: {str(e)}")
        
        # Create booking if payment is valid
        booking = None
        if status == 'VALID' or status == 'Validating':
            print(f"Payment status is {status}, attempting to create booking...")
            print(f"Request object: {request}")
            print(f"Request session keys: {list(request.session.keys()) if request else 'No request'}")
            
            # Try to get dates from session first (preferred)
            check_in = request.session.get('check_in') if request else None
            check_out = request.session.get('check_out') if request else None
            guests_count = request.session.get('guests', '1') if request else '1'
            
            print(f"Session data - check_in: '{check_in}', check_out: '{check_out}', guests: '{guests_count}'")
            
            # Fallback to transaction data if session is empty (KEY FIX!)
            if not check_in or not check_out:
                print(f"⚠ Session data missing, using dates from transaction...")
                check_in = transaction.booking_check_in
                check_out = transaction.booking_check_out
                guests_count = str(transaction.booking_guests_count) if transaction.booking_guests_count else '1'
                print(f"  Retrieved from transaction: {check_in} to {check_out}, guests: {guests_count}")
            
            # Convert string dates to date objects if needed
            from datetime import datetime as dt
            if check_in and isinstance(check_in, str):
                try:
                    check_in = dt.strptime(check_in, '%Y-%m-%d').date()
                    print(f"✓ Converted check_in to date: {check_in}")
                except Exception as e:
                    print(f"✗ Error parsing check_in date '{check_in}': {e}")
                    check_in = timezone.now().date()
                    print(f"  Using default: {check_in}")
            elif not check_in:
                print(f"⚠ No check_in available, using today: {timezone.now().date()}")
                check_in = timezone.now().date()
            
            if check_out and isinstance(check_out, str):
                try:
                    check_out = dt.strptime(check_out, '%Y-%m-%d').date()
                    print(f"✓ Converted check_out to date: {check_out}")
                except Exception as e:
                    print(f"✗ Error parsing check_out date '{check_out}': {e}")
                    check_out = timezone.now().date()
                    print(f"  Using default: {check_out}")
            elif not check_out:
                print(f"⚠ No check_out available, using today: {timezone.now().date()}")
                check_out = timezone.now().date()
            
            print(f"Final booking data:")
            print(f"  Guest: {guest} (ID: {guest.id if guest else 'None'})")
            print(f"  Check-in: {check_in} (type: {type(check_in).__name__})")
            print(f"  Check-out: {check_out} (type: {type(check_out).__name__})")
            print(f"  Guests count: {guests_count}")
            print(f"  Transaction rooms: {transaction.room.count()}")
            
            # Validate we have required data
            if not guest:
                print("❌ ERROR: No guest found for booking creation")
                print(f"   Transaction guest: {transaction.guest}")
                print(f"   Guest from value_b: {data.get('value_b')}")
            elif not check_in or not check_out:
                print(f"❌ ERROR: Missing dates - check_in: {check_in}, check_out: {check_out}")
            elif transaction.room.count() == 0:
                print("❌ ERROR: No rooms in transaction")
                print(f"   Rooms from value_c: {data.get('value_c')}")
            else:
                # Create the booking
                try:
                    print(f"🔄 Attempting to create booking...")
                    booking = Booking.objects.create(
                        tracking_no=transaction.tran_id,
                        guest=guest,
                        number_of_person=str(guests_count),
                        start_day=check_in,
                        end_day=check_out,
                        transaction=transaction,
                        check_in_status='pending'
                    )
                    print(f"✅ Booking object created with ID: {booking.id}")
                    
                    # Add rooms to booking
                    room_count = 0
                    for room in transaction.room.all():
                        booking.room.add(room)
                        room_count += 1
                        print(f"   ✓ Added room {room.id}: {room.name_eng}")
                    
                    print(f"✅✅✅ SUCCESS: Booking created - ID: {booking.id}, Tracking: {booking.tracking_no}, Rooms: {room_count}")
                    
                except Exception as e:
                    print(f"❌❌❌ ERROR creating booking: {str(e)}")
                    print(f"Exception type: {type(e).__name__}")
                    import traceback
                    traceback.print_exc()
        else:
            print(f"Payment status is {status}, not creating booking")
        
        return transaction, booking
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in process_payment_callback: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None
