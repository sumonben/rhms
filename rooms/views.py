from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView, DetailView
from django.contrib import messages
from rooms.models import Room, RoomType, RoomReview
from accounts.models import Staff, Guest, Designation, Department

class Rooms(View):
    template_name = 'rooms/rooms.html'
    
    def get(self, request, *args, **kwargs):
        rooms=Room.objects.all().order_by("serial")
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
        rooms=Room.objects.filter(room_type=room_type)
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        context={}
        context['room_type']=room_type
        context['rooms']=rooms
        context['staffs']=staffs
        context['guests']=guests
        return render(request, self.template_name,context)

    def post(self, request, *args, **kwargs):
        room_type=RoomType.objects.filter(id=int(kwargs['id'])).first()
        rooms=Room.objects.filter(room_type=room_type)
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        context={}
        context['room_type']=room_type
        context['rooms']=rooms
        context['staffs']=staffs
        context['guests']=guests
        return render(request, self.template_name,context)


class RoomDetails(View):
    template_name = 'rooms/room_details.html'
    
    def get(self, request, *args, **kwargs):
        rooms=Room.objects.filter(id=int(kwargs['id'])).first()
        
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
        context['room']=rooms
        context['same_priced_rooms']=same_priced_rooms
        context['staffs']=staffs
        context['guests']=guests
        context['room_reviews'] = room_reviews
        context['average_rating'] = average_rating
        context['average_rating_int'] = average_rating_int
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
        room = Room.objects.filter(id=id).first()
        if not room:
            messages.error(request, 'Room not found.')
            return redirect('rooms_view')

        name = (request.POST.get('name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        rating = request.POST.get('rating')
        comment = (request.POST.get('comment') or '').strip()

        if not name or not email or not phone or not rating or not comment:
            messages.error(request, 'Please fill in all review fields, including mobile number.')
            context=[]
            context['messages'] = messages.get_messages(request)
            return redirect('room_details', id=id,context=context)

        def _normalize_phone(value):
            if not value:
                return ''
            return ''.join(ch for ch in value if ch.isdigit())

        normalized_phone = _normalize_phone(phone)
        print(f"Normalized phone: {normalized_phone} from input: {phone}")
        guest = Guest.objects.filter(phone=normalized_phone).first()
        if not guest:
            print(f"No guest found with phone: {normalized_phone}")
            messages.error(request, 'You have to be our guest to submit a review.')
            if messages.get_messages(request):
                for message in messages.get_messages(request):
                    print(f"Message: {message.tags} - {message.message}")
            return redirect('room_details', id=id)
           
        if guest:
            comment_count= RoomReview.objects.filter(room=room, phone=guest.phone).count()

            if comment_count > 4:
                messages.error(request, 'You have already submitted more than 5 review for this room.')
                return redirect('room_details', id=id)
            guest_phone = _normalize_phone(guest.phone)
            if guest_phone and normalized_phone != guest_phone:
                messages.error(request, 'Mobile number does not match our guest records.')
                return redirect('room_details', id=id)

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            messages.error(request, 'Invalid rating.')
            return redirect('room_details', id=id)

        if rating < 1 or rating > 5:
            messages.error(request, 'Rating must be between 1 and 5.')
            return redirect('room_details', id=id)


        RoomReview.objects.create(
            room=room,
            name=name,
            email=email,
            phone=phone,
            rating=rating,
            comment=comment,
            is_approved=True,
        )

        messages.success(request, 'Thank you! Your review has been submitted.')
        return redirect('room_details', id=id)

