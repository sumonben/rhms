from django.shortcuts import render
from django.views.generic import View, TemplateView, DetailView
from django.contrib import messages
from django.utils import timezone
from rooms.models import Room,RoomType
from accounts.models import Staff, Guest,Designation, Department


def _set_display_status_for_rooms(rooms):
    today = timezone.now().date()
    for room in rooms:
        active_bookings = [
            b for b in room.booking_set.all()
            if b.check_in_status not in ('checked_out', 'cancelled') and not b.check_out_status
        ]
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
        context={}
        if rooms:
            _set_display_status_for_rooms([rooms])
        context['room']=rooms
        context['same_priced_rooms']=same_priced_rooms
        context['staffs']=staffs
        context['guests']=guests
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

