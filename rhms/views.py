from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.generic import View, TemplateView, DetailView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from rooms.models import Room,RoomType
from .models import Carousel, Booking, HotelDetails
from accounts.models import Staff, Guest,Designation, Department
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


def _sort_rooms_by_availability(rooms):
    def _sort_key(room):
        status = getattr(room, 'display_status', None) or getattr(room, 'status', None) or 'available'
        if isinstance(status, str):
            status = status.lower()
        else:
            status = 'available'
        serial = getattr(room, 'serial', None)
        if serial is None:
            serial = getattr(room, 'id', 0)
        return (status != 'available', serial)

    return sorted(list(rooms), key=_sort_key)

class Frontpage(View):
    template_name = 'frontpage/frontpage.html'
    
    def get(self, request, *args, **kwargs):
        rooms=Room.objects.all().prefetch_related('booking_set').order_by("serial")
        # Only show room types that have at least one room
        room_types=RoomType.objects.filter(room__isnull=False).distinct().order_by("serial")
        carousels=Carousel.objects.all().order_by("serial")[0:4]
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        # Compute display status based on booking state
        today = timezone.now().date()
        for room in rooms:
            manual_status = (room.status or '').lower()
            active_bookings = [
                b for b in room.booking_set.all()
                if b.check_in_status not in ('checked_out', 'cancelled') and not b.check_out_status
            ]
            if manual_status in ('unavailable', 'maintenance'):
                room.display_status = 'unavailable'
                room.booked_until = None
                continue
            if manual_status == 'booked':
                room.display_status = 'booked'
                pending_bookings = [b for b in active_bookings if b.check_in_status == 'pending' and b.end_day >= today]
                room.booked_until = max(b.end_day for b in pending_bookings) if pending_bookings else None
                continue
            if any(b.check_in_status == 'checked_in' for b in active_bookings):
                room.display_status = 'occupied'
                room.booked_until = None
            elif any(b.check_in_status == 'pending' and b.end_day >= today for b in active_bookings):
                room.display_status = 'booked'
                pending_bookings = [b for b in active_bookings if b.check_in_status == 'pending' and b.end_day >= today]
                room.booked_until = max(b.end_day for b in pending_bookings) if pending_bookings else None
            else:
                room.display_status = 'available'
                room.booked_until = None
        rooms = _sort_rooms_by_availability(rooms)
        print(rooms)
        context={}
        context['rooms']=rooms
        context['room_types']=room_types
        context['carousels']=carousels
        context['staffs']=staffs
        context['guests']=guests
        return render(request, self.template_name,context)

    def post(self, request, *args, **kwargs):
        # Handle check availability form submission
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests_count = request.POST.get('guests')
        rooms_count = request.POST.get('rooms')
        
        if check_in and check_out:
            # Store search parameters in session
            request.session['check_in'] = check_in
            request.session['check_out'] = check_out
            request.session['guests'] = guests_count
            request.session['rooms_count'] = rooms_count
            
            messages.success(request, f'Searching for available rooms from {check_in} to {check_out}')
            return redirect('rooms_view')
        else:
            messages.error(request, 'Please select check-in and check-out dates')
            return redirect('frontpage')


class AboutView(TemplateView):
    template_name = 'frontpage/about_us.html'


class ContactView(TemplateView):
    template_name = 'frontpage/contact_us.html'


class FindBookingView(View):
    """View to search for a booking by tracking number, email, or phone"""
    template_name = 'frontpage/find_booking.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        tracking_no = request.POST.get('tracking_no', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Tracking number is required
        if not tracking_no:
            messages.error(request, 'Tracking Number is required')
            return render(request, self.template_name)
        
        # Build query with tracking number as primary search
        query = Q(tracking_no__iexact=tracking_no)
        
        # Add optional filters if provided
        if phone:
            query &= Q(guest__phone__iexact=phone)
        if email:
            query &= Q(guest__email__iexact=email)
        
        # Search for bookings
        bookings = Booking.objects.filter(query).select_related(
            'guest', 'transaction'
        ).prefetch_related('room').order_by('-booked_on')
        
        if bookings.exists():
            context = {
                'bookings': bookings,
                'phone': phone,
                'tracking_no': tracking_no,
                'email': email
            }
            return render(request, self.template_name, context)
        else:
            messages.error(request, 'No bookings found with the provided information')
            context = {
                'phone': phone,
                'tracking_no': tracking_no,
                'email': email
            }
            return render(request, self.template_name, context)


class BookingDetailsView(View):
    """View to display detailed information about a specific booking"""
    template_name = 'frontpage/booking_details.html'
    
    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        
        context = {
            'booking': booking,
            'rooms': booking.room.all(),
            'can_check_in': booking.check_in_status == 'pending' and booking.start_day <= timezone.now().date(),
            'can_check_out': booking.check_in_status == 'checked_in' and not booking.check_out_status,
        }
        
        return render(request, self.template_name, context)


class BookingReceiptView(View):
    """Downloadable booking receipt for guests"""

    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        rooms = booking.room.all()

        hotel_details = HotelDetails.objects.last()
        hotel_name = None
        logo_path = None
        watermark_path = None

        if hotel_details:
            hotel_name = hotel_details.title_en or hotel_details.title
            if hotel_details.logo and hasattr(hotel_details.logo, 'path'):
                logo_path = hotel_details.logo.path
            if hotel_details.logo_opacity and hasattr(hotel_details.logo_opacity, 'path'):
                watermark_path = hotel_details.logo_opacity.path
            elif hotel_details.logo and hasattr(hotel_details.logo, 'path'):
                watermark_path = hotel_details.logo.path

        stay_nights = 1
        if booking.start_day and booking.end_day:
            try:
                stay_nights = (booking.end_day - booking.start_day).days
            except (TypeError, ValueError):
                stay_nights = 1
        if stay_nights <= 0:
            stay_nights = 1

        def _get_room_price(room):
            try:
                raw_price = room.price if room.price not in (None, '') else None
                if raw_price is None and room.room_type:
                    raw_price = room.room_type.price
                return float(raw_price or 0)
            except (TypeError, ValueError):
                return 0

        def _get_room_nights(room_id):
            if booking.transaction and hasattr(booking.transaction, 'booking_dates_json'):
                booking_dates = booking.transaction.booking_dates_json or {}
                room_dates = booking_dates.get(str(room_id)) or booking_dates.get(room_id)
                if isinstance(room_dates, dict):
                    check_in = room_dates.get('check_in')
                    check_out = room_dates.get('check_out')
                    if check_in and check_out:
                        try:
                            from datetime import datetime as dt
                            check_in_date = dt.strptime(check_in, '%Y-%m-%d')
                            check_out_date = dt.strptime(check_out, '%Y-%m-%d')
                            nights = (check_out_date - check_in_date).days
                            return nights if nights > 0 else 1
                        except Exception:
                            pass
            return stay_nights

        total_amount = 0
        for room in rooms:
            room_price = _get_room_price(room)
            total_amount += room_price * _get_room_nights(room.id)

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        def _safe_set_alpha(alpha):
            if hasattr(pdf, 'setFillAlpha'):
                pdf.setFillAlpha(alpha)

        # Watermark
        if watermark_path:
            try:
                pdf.saveState()
                _safe_set_alpha(0.08)
                watermark = ImageReader(watermark_path)
                wm_size = 120 * mm
                pdf.drawImage(
                    watermark,
                    (width - wm_size) / 2,
                    (height - wm_size) / 2,
                    wm_size,
                    wm_size,
                    preserveAspectRatio=True,
                    mask='auto'
                )
                pdf.restoreState()
            except Exception:
                pass

        # Header
        x_left = 25 * mm
        y_top = height - 25 * mm
        if logo_path:
            try:
                logo = ImageReader(logo_path)
                pdf.drawImage(logo, x_left, y_top - 18 * mm, 30 * mm, 18 * mm, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(x_left + 35 * mm, y_top - 5 * mm, hotel_name or "Hotel")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(x_left + 35 * mm, y_top - 12 * mm, "Booking Receipt")

        pdf.setFont("Helvetica", 10)
        pdf.drawRightString(width - x_left, y_top - 5 * mm, f"Receipt ID: {booking.id}")
        pdf.drawRightString(width - x_left, y_top - 12 * mm, f"Issued: {booking.booked_on:%d %b %Y, %I:%M %p}")

        pdf.line(x_left, y_top - 20 * mm, width - x_left, y_top - 20 * mm)

        y = y_top - 30 * mm
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x_left, y, "Guest Information")
        y -= 8 * mm
        pdf.setFont("Helvetica", 10)
        pdf.drawString(x_left, y, f"Guest Name: {booking.guest.name_eng if booking.guest else 'N/A'}")
        y -= 6 * mm
        pdf.drawString(x_left, y, f"Email: {booking.guest.email if booking.guest else 'N/A'}")
        y -= 6 * mm
        pdf.drawString(x_left, y, f"Phone: {booking.guest.phone if booking.guest else 'N/A'}")
        y -= 6 * mm
        pdf.drawString(x_left, y, f"Tracking No: {booking.tracking_no or 'N/A'}")

        y -= 10 * mm
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x_left, y, "Booking Summary")
        y -= 8 * mm
        pdf.setFont("Helvetica", 10)
        pdf.drawString(x_left, y, f"Check-in Date: {booking.start_day}")
        y -= 6 * mm
        pdf.drawString(x_left, y, f"Check-out Date: {booking.end_day}")
        y -= 6 * mm
        pdf.drawString(x_left, y, f"Nights: {stay_nights}")
        y -= 6 * mm
        pdf.drawString(x_left, y, f"Guests: {booking.number_of_person or 'N/A'}")
        y -= 6 * mm
        pdf.drawString(x_left, y, f"Status: {booking.check_in_status or 'N/A'}")

        # Per-room check-in/check-out under Booking Summary
        booking_dates = {}
        if booking.transaction and hasattr(booking.transaction, 'booking_dates_json'):
            booking_dates = booking.transaction.booking_dates_json or {}
        if booking_dates:
            y -= 8 * mm
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(x_left, y, "Per-room Dates")
            y -= 6 * mm
            pdf.setFont("Helvetica", 9)
            for room in rooms:
                if y < 25 * mm:
                    pdf.showPage()
                    y = height - 25 * mm
                    pdf.setFont("Helvetica", 9)
                room_dates = booking_dates.get(str(room.id)) or booking_dates.get(room.id) or {}
                room_check_in = room_dates.get('check_in', '') if isinstance(room_dates, dict) else ''
                room_check_out = room_dates.get('check_out', '') if isinstance(room_dates, dict) else ''
                label = f"{room.name_eng or ''} ({room.room_no or ''})"
                pdf.drawString(x_left, y, f"{label}: {room_check_in} → {room_check_out}")
                y -= 5 * mm

        y -= 12 * mm
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x_left, y, "Booked Rooms")
        y -= 8 * mm
        pdf.setFont("Helvetica-Bold", 9)
        col_room = 28 * mm
        col_room_no = 18 * mm
        col_type = 28 * mm
        col_check_in = 20 * mm
        col_check_out = 20 * mm
        col_fare = 16 * mm
        col_days = 8 * mm
        col_total = 22 * mm
        x_room = x_left
        x_room_no = x_room + col_room
        x_type = x_room_no + col_room_no
        x_check_in = x_type + col_type
        x_check_out = x_check_in + col_check_in
        x_fare_right = x_check_out + col_check_out + col_fare
        x_days_right = x_fare_right + col_days
        x_total_right = x_days_right + col_total
        pdf.drawString(x_room, y, "Room")
        pdf.drawString(x_room_no, y, "Room No")
        pdf.drawString(x_type, y, "Type")
        pdf.drawString(x_check_in, y, "Check-in")
        pdf.drawString(x_check_out, y, "Check-out")
        pdf.drawRightString(x_fare_right, y, "Fare (৳)")
        pdf.drawRightString(x_days_right, y, "Days")
        pdf.drawRightString(x_total_right, y, "Total (৳)")
        y -= 4 * mm
        pdf.line(x_left, y, width - x_left, y)
        y -= 6 * mm

        pdf.setFont("Helvetica", 9)
        def _format_date_short(value):
            if not value:
                return ""
            if hasattr(value, "strftime"):
                return value.strftime("%d %b")
            try:
                from datetime import datetime as dt
                return dt.strptime(str(value), "%Y-%m-%d").strftime("%d %b")
            except Exception:
                return str(value)
        for room in rooms:
            if y < 25 * mm:
                pdf.showPage()
                y = height - 25 * mm
                pdf.setFont("Helvetica", 9)
            pdf.drawString(x_room, y, room.name_eng or '')
            pdf.drawString(x_room_no, y, room.room_no or '')
            pdf.drawString(x_type, y, room.room_type.name_eng if room.room_type else '')
            room_check_in = ""
            room_check_out = ""
            if booking.transaction and hasattr(booking.transaction, 'booking_dates_json'):
                booking_dates = booking.transaction.booking_dates_json or {}
                room_dates = booking_dates.get(str(room.id)) or booking_dates.get(room.id)
                if isinstance(room_dates, dict):
                    room_check_in = room_dates.get('check_in') or ""
                    room_check_out = room_dates.get('check_out') or ""
            pdf.drawString(x_check_in, y, _format_date_short(room_check_in))
            pdf.drawString(x_check_out, y, _format_date_short(room_check_out))
            room_price = _get_room_price(room)
            room_nights = _get_room_nights(room.id)
            room_total = room_price * room_nights
            pdf.drawRightString(x_fare_right, y, f"{room_price:.2f}")
            pdf.drawRightString(x_days_right, y, f"{room_nights}")
            pdf.drawRightString(x_total_right, y, f"{room_total:.2f}")
            y -= 6 * mm

        y -= 4 * mm
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawRightString(
            width - x_left,
            y,
            f"Total Amount (৳): {total_amount:.2f}"
        )

        y -= 10 * mm
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x_left, y, "Payment Information")
        y -= 8 * mm
        pdf.setFont("Helvetica", 10)
        payment_status = "Paid" if booking.transaction else "Unpaid"
        transaction_id = booking.transaction.tracking_no if booking.transaction else "N/A"
        amount = booking.transaction.amount if booking.transaction else "0"
        pdf.drawString(x_left, y, f"Payment Status: {payment_status}")
        y -= 6 * mm
        pdf.drawString(x_left, y, f"Transaction ID: {transaction_id}")
        y -= 6 * mm
        pdf.drawString(x_left, y, f"Amount: ৳{amount}")

        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="booking-receipt-{booking.id}.pdf"'
        return response


class CheckInView(View):
    """View to handle guest check-in"""
    
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Verify booking can be checked in
        if booking.check_in_status != 'pending':
            messages.error(request, 'This booking has already been checked in or cancelled')
            return redirect('booking_details', booking_id=booking_id)
        
        if booking.start_day > timezone.now().date():
            messages.error(request, f'Check-in is not available until {booking.start_day}')
            return redirect('booking_details', booking_id=booking_id)
        
        # Perform check-in
        booking.check_in_status = 'checked_in'
        booking.check_in_time = timezone.now()
        booking.save()
        
        # Update room availability
        for room in booking.room.all():
            room.is_available = False
            room.status = 'occupied'
            room.save()
        
        messages.success(request, f'Successfully checked in! Welcome to your stay.')
        return redirect('booking_details', booking_id=booking_id)


class CheckOutView(View):
    """View to handle guest check-out"""
    
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Verify booking can be checked out
        if booking.check_in_status != 'checked_in':
            messages.error(request, 'This booking must be checked in before checking out')
            return redirect('booking_details', booking_id=booking_id)
        
        if booking.check_out_status:
            messages.error(request, 'This booking has already been checked out')
            return redirect('booking_details', booking_id=booking_id)
        
        # Perform check-out
        booking.check_in_status = 'checked_out'
        booking.check_out_status = True
        booking.check_out_time = timezone.now()
        booking.save()
        
        # Update room availability
        for room in booking.room.all():
            room.is_available = True
            room.status = 'available'
            room.save()
        
        messages.success(request, f'Successfully checked out! Thank you for your stay.')
        return redirect('booking_details', booking_id=booking_id)

