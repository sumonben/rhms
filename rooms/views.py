from django.shortcuts import render
from django.views.generic import View, TemplateView, DetailView
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from rooms.models import Room, RoomType, RoomReview
from accounts.models import Staff, Guest,Designation, Department
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import json


def _set_display_status_for_rooms(rooms):
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

class Rooms(View):
    template_name = 'rooms/rooms.html'
    
    def get(self, request, *args, **kwargs):
        rooms=Room.objects.all().prefetch_related('booking_set').order_by("serial")
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        context={}
        
        # Check if there's availability search data in session
        check_in = request.session.get('check_in')
        check_out = request.session.get('check_out')
        guests_count = request.session.get('guests')
        rooms_count = request.session.get('rooms_count')
        
        if check_in and check_out:
            context['check_in'] = check_in
            context['check_out'] = check_out
            context['guests'] = guests_count
            context['rooms_count'] = rooms_count
            context['search_active'] = True
            # Clear session data after using it
            request.session.pop('check_in', None)
            request.session.pop('check_out', None)
            request.session.pop('guests', None)
            request.session.pop('rooms_count', None)
        
        _set_display_status_for_rooms(rooms)
        rooms = _sort_rooms_by_availability(rooms)
        context['rooms']=rooms
        context['staffs']=staffs
        context['guests']=guests
        return render(request, self.template_name,context)

    def post(self, request, *args, **kwargs):
        pass
class RoomTypeRooms(View):
    template_name = 'rooms/rooms.html'
    
    def get(self, request, *args, **kwargs):
        room_type=RoomType.objects.filter(id=int(kwargs['id'])).first()
        rooms=Room.objects.filter(room_type=room_type).prefetch_related('booking_set')
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        context={}
        _set_display_status_for_rooms(rooms)
        rooms = _sort_rooms_by_availability(rooms)
        context['room_type']=room_type
        context['rooms']=rooms
        context['staffs']=staffs
        context['guests']=guests
        return render(request, self.template_name,context)

    def post(self, request, *args, **kwargs):
        room_type=RoomType.objects.filter(id=int(kwargs['id'])).first()
        rooms=Room.objects.filter(room_type=room_type).prefetch_related('booking_set')
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        context={}
        _set_display_status_for_rooms(rooms)
        rooms = _sort_rooms_by_availability(rooms)
        context['room_type']=room_type
        context['rooms']=rooms
        context['staffs']=staffs
        context['guests']=guests
        return render(request, self.template_name,context)


class RoomDetails(View):
    template_name = 'rooms/room_details.html'
    
    def get(self, request, *args, **kwargs):
        rooms=Room.objects.filter(id=int(kwargs['id'])).prefetch_related('booking_set').first()
        
        # Get rooms with the same price (excluding current room)
        same_priced_rooms = []
        if rooms and rooms.price:
            same_priced_rooms = Room.objects.filter(price=rooms.price).exclude(id=rooms.id).order_by('serial')[:6]
            print(f"Room {rooms.id} price: {rooms.price}, Similar rooms found: {same_priced_rooms.count()}")
        
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        room_reviews = []
        average_rating = None
        average_rating_int = None
        if rooms:
            room_reviews = RoomReview.objects.filter(room=rooms, is_approved=True).order_by('-created_at')
            if room_reviews:
                average_value = sum(r.rating for r in room_reviews) / len(room_reviews)
                average_rating = round(average_value, 1)
                average_rating_int = int(round(average_value, 0))
        context={}
        if rooms:
            _set_display_status_for_rooms([rooms])
        context['room']=rooms
        context['same_priced_rooms']=same_priced_rooms
        context['staffs']=staffs
        context['guests']=guests
        context['room_reviews'] = room_reviews
        context['average_rating'] = average_rating
        context['average_rating_int'] = average_rating_int
        context['recaptcha_site_key'] = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
        return render(request, self.template_name,context)

    def post(self, request, *args, **kwargs):
        from django.shortcuts import redirect
        # Handle check availability form submission
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests_count = request.POST.get('guests')
        rooms_count = request.POST.get('rooms')
        
        if check_in and check_out:
            # Store in session and redirect to cart
            request.session['check_in'] = check_in
            request.session['check_out'] = check_out
            request.session['guests'] = guests_count
            request.session['rooms_count'] = rooms_count
            request.session['selected_room_id'] = kwargs['id']
            
            messages.success(request, f'Room available from {check_in} to {check_out}. You can proceed to add to cart.')
            return redirect('room_details', id=kwargs['id'])
        else:
            messages.error(request, 'Please select check-in and check-out dates')
            return redirect('room_details', id=kwargs['id'])


class RoomReviewSubmitView(View):
    def post(self, request, id, *args, **kwargs):
        from django.shortcuts import redirect

        room = Room.objects.filter(id=id).first()
        if not room:
            messages.error(request, 'Room not found.')
            return redirect('rooms_view')

        name = (request.POST.get('name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        rating = request.POST.get('rating')
        comment = (request.POST.get('comment') or '').strip()
        recaptcha_token = request.POST.get('g-recaptcha-response')

        if not name or not email or not rating or not comment:
            messages.error(request, 'Please fill in all review fields.')
            return redirect('room_details', id=id)

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            messages.error(request, 'Invalid rating.')
            return redirect('room_details', id=id)

        if rating < 1 or rating > 5:
            messages.error(request, 'Rating must be between 1 and 5.')
            return redirect('room_details', id=id)

        secret = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
        site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
        if not secret or not site_key:
            messages.error(request, 'reCAPTCHA is not configured. Please contact support.')
            return redirect('room_details', id=id)

        if not recaptcha_token:
            messages.error(request, 'Please complete the reCAPTCHA.')
            return redirect('room_details', id=id)

        data = urlencode({
            'secret': secret,
            'response': recaptcha_token,
            'remoteip': request.META.get('REMOTE_ADDR', '')
        }).encode('utf-8')

        try:
            req = Request('https://www.google.com/recaptcha/api/siteverify', data=data)
            with urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
        except Exception:
            messages.error(request, 'reCAPTCHA verification failed. Please try again.')
            return redirect('room_details', id=id)

        if not result.get('success'):
            messages.error(request, 'reCAPTCHA verification failed. Please try again.')
            return redirect('room_details', id=id)

        RoomReview.objects.create(
            room=room,
            name=name,
            email=email,
            rating=rating,
            comment=comment,
        )

        messages.success(request, 'Thank you! Your review has been submitted.')
        return redirect('room_details', id=id)

