from django.http import HttpResponse, JsonResponse
from rooms.models import Room
from accounts.models import Guest, Staff
from region.forms import AddressForm
from django.shortcuts import render, redirect, get_object_or_404
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
    context={}
    cart = Cart(request)
    room = get_object_or_404(Room, id=request.POST.get('id'))
    cart=cart.add(room=room)
    rooms=Room.objects.filter(id__in=cart)
    context['status']='success'
    total=0
    for room in rooms:
        total=total+int(room.price)
    context['total']=total
    print(total)
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
        cart = request.session.get(settings.CART_SESSION_ID)  
        cart_rooms=Room.objects.filter(id__in=cart)  
        total_cart_amount=0
        for cart_room in cart_rooms:
            total_cart_amount = total_cart_amount+int(cart_room.price)
        address = AddressForm(request.POST)
        if address.is_valid:
            address=address.save()
            guest=Guest(name=request.POST.get('receiver_name'),name_eng=request.POST.get('receiver_name'), phone=request.POST.get('receiver_phone'),address=address)
            guest.save()
            return redirect(sslcommerz_payment_gateway(request, guest, cart_rooms, total_cart_amount))
        return HttpResponse('Address Not Valid')

def orderCart(request):
    context={}
    cart = Cart(request)
    request.session = request.session
    cart = request.session.get(settings.CART_SESSION_ID)  
    cart_rooms=Room.objects.filter(id__in=cart)  
    total_cart_amount=0
    for cart_room in cart_rooms:
        total_cart_amount = total_cart_amount+int(cart_room.price)
    address = AddressForm(request.POST)
    if address.is_valid:
        address=address.save()
        guest=Guest(name=request.POST.get('receiver_name'),name_eng=request.POST.get('receiver_name'), phone=request.POST.get('receiver_phone'), address=address)
        guest.save()
        return redirect(sslcommerz_payment_gateway(request, guest, cart_rooms, total_cart_amount))
    return HttpResponse('Address Not Valid')


def orderPage(request):
    context={}
    room_ids = [int(s) for s in request.POST.getlist('items[]')]
    rooms = Room.objects.filter(id__in=room_ids)
    address_form=AddressForm()
    context['address_form']=address_form
    context['status']='success'
    context['rooms']=list(rooms)

    return render(request, 'cart/order.html', context)
    context={}
    room_ids = [int(s) for s in request.POST.getlist('items[]')]
    rooms = Room.objects.filter(id__in=room_ids)
    print(rooms)
    context['rooms']=rooms
    return HttpResponse('hello')
    return render(request, 'cart/order.html', context)
