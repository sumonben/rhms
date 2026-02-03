"""
Manual Booking Creation Script
Run this to create bookings for existing VALID transactions that don't have bookings
"""

from django.utils import timezone
from datetime import datetime, timedelta
from payment.models import Transaction
from rhms.models import Booking
from accounts.models import Guest

def create_bookings_for_orphan_transactions():
    """Create bookings for VALID transactions that don't have bookings"""
    
    # Find VALID transactions without bookings
    valid_transactions = Transaction.objects.filter(status='VALID')
    
    created_count = 0
    skipped_count = 0
    
    for transaction in valid_transactions:
        # Check if booking already exists
        existing_booking = Booking.objects.filter(transaction=transaction).first()
        
        if existing_booking:
            print(f"⏭ Transaction {transaction.tran_id} already has booking {existing_booking.id}")
            skipped_count += 1
            continue
        
        # Get guest
        guest = transaction.guest
        if not guest:
            print(f"❌ Transaction {transaction.tran_id} has no guest - cannot create booking")
            continue
        
        # Get rooms
        rooms = transaction.room.all()
        if rooms.count() == 0:
            print(f"❌ Transaction {transaction.tran_id} has no rooms - cannot create booking")
            continue
        
        # Use default dates (today + 1 week)
        check_in = timezone.now().date()
        check_out = check_in + timedelta(days=7)
        
        try:
            # Create booking
            booking = Booking.objects.create(
                tracking_no=transaction.tran_id,
                guest=guest,
                number_of_person='2',  # Default
                start_day=check_in,
                end_day=check_out,
                transaction=transaction,
                check_in_status='pending'
            )
            
            # Add rooms
            for room in rooms:
                booking.room.add(room)
            
            print(f"✅ Created booking {booking.id} for transaction {transaction.tran_id}")
            print(f"   Guest: {guest.name_eng}, Rooms: {rooms.count()}, Dates: {check_in} to {check_out}")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Error creating booking for transaction {transaction.tran_id}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"Summary: Created {created_count} bookings, Skipped {skipped_count}")
    print(f"{'='*60}")

if __name__ == '__main__':
    create_bookings_for_orphan_transactions()
