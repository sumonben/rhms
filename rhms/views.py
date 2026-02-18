from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.urls import reverse
import json
import ollama
from django.views.generic import View, TemplateView, DetailView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from rooms.models import Room,RoomType
from .models import Carousel, Booking, HotelDetails
from accounts.models import Staff, Guest,Designation, Department
from datetime import datetime
from .receipts import generate_booking_receipt_pdf


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
        pdf_bytes = generate_booking_receipt_pdf(booking)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
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


@require_POST
def chatbot_api(request):
    """Simple AI chatbot proxy using a local Ollama server."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    message = (payload.get('message') or '').strip()
    if not message:
        return JsonResponse({'error': 'Message is required.'}, status=400)

    system_prompt = (
        "You are a helpful hotel assistant for Hotel Red Rock. "
        "Answer concisely and politely. If asked to do something you cannot, "
        "say so and offer alternatives."
    )

    history = request.session.get('chatbot_history', [])
    if not isinstance(history, list):
        history = []

    messages = [{'role': 'system', 'content': system_prompt}]
    messages.extend(history)
    messages.append({'role': 'user', 'content': message})

    try:
        client = ollama.Client(host='http://localhost:11434')
        response_data = client.chat(
            model='llama3.1:8b',
            messages=messages,
            stream=False,
        )
    except Exception:
        fallback_reply = (
            "I'm here to help with bookings, check-in/out, and room details. "
            "The AI service is currently offline. Please try again later or contact us at 01786272762."
        )
        return JsonResponse({'reply': fallback_reply})

    reply = ((response_data.get('message') or {}).get('content') or '').strip()
    if not reply:
        reply = 'Sorry, I could not generate a response. Please try again.'

    history.append({'role': 'user', 'content': message})
    history.append({'role': 'assistant', 'content': reply})
    request.session['chatbot_history'] = history[-10:]
    request.session.modified = True

    return JsonResponse({'reply': reply})


def sitemap(request):
    """Generate XML sitemap for search engines."""
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    
    urls = []
    
    urls.append({
        'location': request.build_absolute_uri(reverse('frontpage')),
        'lastmod': timezone.now().date(),
        'changefreq': 'weekly',
        'priority': '1.0'
    })
    
    urls.append({
        'location': request.build_absolute_uri(reverse('about')),
        'lastmod': timezone.now().date(),
        'changefreq': 'monthly',
        'priority': '0.8'
    })
    
    urls.append({
        'location': request.build_absolute_uri(reverse('contact')),
        'lastmod': timezone.now().date(),
        'changefreq': 'monthly',
        'priority': '0.8'
    })
    
    urls.append({
        'location': request.build_absolute_uri(reverse('rooms_view')),
        'lastmod': timezone.now().date(),
        'changefreq': 'daily',
        'priority': '0.9'
    })
    
    urls.append({
        'location': request.build_absolute_uri(reverse('find_booking')),
        'lastmod': timezone.now().date(),
        'changefreq': 'monthly',
        'priority': '0.7'
    })
    
    for room in Room.objects.all():
        urls.append({
            'location': request.build_absolute_uri(reverse('room_details', args=[room.id])),
            'lastmod': room.updated_at if hasattr(room, 'updated_at') else timezone.now().date(),
            'changefreq': 'weekly',
            'priority': '0.8'
        })
    
    sitemap_xml = render_to_string('sitemap.xml', {'urls': urls})
    return HttpResponse(sitemap_xml, content_type='application/xml')


def robots_txt(request):
    """Serve robots.txt file."""
    content = """User-agent: *
Allow: /

Sitemap: https://hotelredrock.com/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')

