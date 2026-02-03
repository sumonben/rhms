from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from rooms.models import Room
from accounts.models import Guest, Staff
from region.forms import AddressForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .cart import Cart
from django.conf import settings
from rooms.models import Room
from django.views.decorators.csrf import csrf_protect
from payment.sslcommerz import sslcommerz_payment_gateway
from django.views.generic import View

def cartAdd(request, room_id):
    cart = Cart(request)
    room = get_object_or_404(Room, id=room_id)
    cart=cart.add(room=room)
    rooms=Room.objects.filter(id__in=cart)
    return JsonResponse({'status':'success','meaasge':'Account created Successfully','rooms':rooms},safe=False)
@csrf_protect
def cartAddRoom(request):
    from datetime import datetime
    
    context={}
    cart = Cart(request)
    room = get_object_or_404(Room, id=request.POST.get('id'))
    check_in = request.POST.get('check_in')
    check_out = request.POST.get('check_out')
    cart=cart.add(room=room, check_in=check_in, check_out=check_out)
    rooms=Room.objects.filter(id__in=cart)
    context['status']='success'
    
    # Calculate number of nights
    nights = 1  # Default to 1 night
    if check_in and check_out:
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
            nights = (check_out_date - check_in_date).days
            if nights <= 0:
                nights = 1  # Minimum 1 night
        except (ValueError, TypeError):
            nights = 1
    
    total=0
    for room in rooms:
        # Calculate amount = room price × number of nights
        total=total+(int(room.price) * nights)
    
    context['total']=total
    print(f"Cart total: {total} (Nights: {nights})")
    rooms=list(rooms.values())
    context['rooms']=rooms
    return JsonResponse(context,safe=False)

def cartDetails(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})
def cartClear(request):
    cart = Cart(request)
    cart.clear()
    context={}
    context['status']='success'
    return JsonResponse(context,safe=False)

class orderCartView(View):
    template_name = 'forms/applicant_details.html'
    def post(self, request, *args, **kwargs):
        context={}
        cart = Cart(request)
        request.session = request.session
        cart_data = request.session.get(settings.CART_SESSION_ID, {})  
        cart_rooms=Room.objects.filter(id__in=cart_data.keys())  
        total_cart_amount=0
        
        # Collect check-in and check-out dates from form
        booking_dates = {}
        first_check_in = None
        first_check_out = None
        
        from datetime import datetime
        
        for room in cart_rooms:
            check_in = request.POST.get(f'check_in_{room.id}')
            check_out = request.POST.get(f'check_out_{room.id}')
            
            # Store first room's dates as default for booking
            if first_check_in is None:
                first_check_in = check_in
                first_check_out = check_out
            
            booking_dates[room.id] = {
                'check_in': check_in,
                'check_out': check_out
            }
            
            # Calculate number of nights
            nights = 1  # Default to 1 night
            if check_in and check_out:
                try:
                    check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
                    check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
                    nights = (check_out_date - check_in_date).days
                    if nights <= 0:
                        nights = 1  # Minimum 1 night
                except ValueError:
                    nights = 1
            
            # Calculate amount = room price × number of nights
            total_cart_amount = total_cart_amount + (int(room.price) * nights)
        
        address = AddressForm(request.POST)
        if address.is_valid:
            address=address.save()
            guest=Guest(
                name=request.POST.get('receiver_name'),
                name_eng=request.POST.get('receiver_name'), 
                phone=request.POST.get('receiver_phone'),
                email=request.POST.get('receiver_email', 'guest@hotel.com'),
                address=address
            )
            guest.save()
            
            # Store booking dates in session for payment processing
            request.session['booking_dates'] = booking_dates
            request.session['check_in'] = first_check_in
            request.session['check_out'] = first_check_out
            request.session['guests'] = request.POST.get('number_of_guests', '1')
            request.session.modified = True
            
            # Debug logging
            print(f"Initiating payment for guest: {guest.name}, Amount: {total_cart_amount}")
            print(f"Check-in: {first_check_in}, Check-out: {first_check_out}")
            print(f"Rooms: {[room.id for room in cart_rooms]}")
            print(f"📅 Booking dates stored in session: {booking_dates}")
            
            payment_url = sslcommerz_payment_gateway(request, guest, cart_rooms, total_cart_amount)
            
            print(f"Payment URL: {payment_url}")
            
            if payment_url and isinstance(payment_url, str) and len(payment_url) > 0:
                # Use HttpResponseRedirect for external URLs
                return HttpResponseRedirect(payment_url)
            else:
                messages.error(request, 'Payment gateway error. Please try again.')
                return redirect('frontpage')
        return HttpResponse('Address Not Valid')

def orderCart(request):
    context={}
    cart = Cart(request)
    request.session = request.session
    cart = request.session.get(settings.CART_SESSION_ID)  
    cart_rooms=Room.objects.filter(id__in=cart)  
    total_cart_amount=0
    
    from datetime import datetime
    
    # Get check-in and check-out dates
    check_in = request.POST.get('check_in', '')
    check_out = request.POST.get('check_out', '')
    
    # Calculate number of nights
    nights = 1  # Default to 1 night
    if check_in and check_out:
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
            nights = (check_out_date - check_in_date).days
            if nights <= 0:
                nights = 1  # Minimum 1 night
        except ValueError:
            nights = 1
    
    for cart_room in cart_rooms:
        # Calculate amount = room price × number of nights
        total_cart_amount = total_cart_amount + (int(cart_room.price) * nights)
    address = AddressForm(request.POST)
    if address.is_valid:
        address=address.save()
        guest=Guest(
            name=request.POST.get('receiver_name'),
            name_eng=request.POST.get('receiver_name'), 
            phone=request.POST.get('receiver_phone'),
            email=request.POST.get('receiver_email', 'guest@hotel.com'),
            address=address
        )
        guest.save()
        
        # Store session data for booking
        request.session['check_in'] = request.POST.get('check_in', '')
        request.session['check_out'] = request.POST.get('check_out', '')
        request.session['guests'] = request.POST.get('number_of_guests', '1')
        request.session.modified = True
        
        payment_url = sslcommerz_payment_gateway(request, guest, cart_rooms, total_cart_amount)
        if payment_url and isinstance(payment_url, str) and len(payment_url) > 0:
            # Use HttpResponseRedirect for external URLs
            return HttpResponseRedirect(payment_url)
        else:
            messages.error(request, 'Payment gateway error. Please try again.')
            return redirect('frontpage')
    return HttpResponse('Address Not Valid')


def orderPage(request):
    context={}
    cart = Cart(request)
    request.session = request.session
    cart_data = request.session.get(settings.CART_SESSION_ID, {})
    
    if not cart_data:
        context['cart_rooms'] = []
        context['total_cart_amount'] = 0
        context['address_form'] = AddressForm()
        context['status'] = 'success'
        return render(request, 'cart/order.html', context)
    
    # Get room IDs from cart data
    room_ids = [int(room_id) for room_id in cart_data.keys()]
    cart_rooms = Room.objects.filter(id__in=room_ids)
    
    # Calculate total (per night price only, since dates haven't been entered yet)
    total_cart_amount = 0
    for room in cart_rooms:
        total_cart_amount += int(room.price)
    
    # Note: This shows per-night total. Actual amount will be calculated when dates are selected
    
    address_form = AddressForm()
    context['address_form'] = address_form
    context['status'] = 'success'
    context['cart_rooms'] = cart_rooms
    context['total_cart_amount'] = total_cart_amount

    return render(request, 'cart/order.html', context)
