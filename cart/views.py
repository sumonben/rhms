from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rooms.models import Room
from django.shortcuts import render, redirect, get_object_or_404
from .cart import Cart
from rooms.models import Room
from django.views.decorators.csrf import csrf_protect


def cartAdd(request, room_id):
    cart = Cart(request)
    print(cart)
    room = get_object_or_404(Room, id=room_id)
    cart=cart.add(room=room)
    rooms=Room.objects.filter(id__in=cart)
    return JsonResponse({'status':'success','meaasge':'Account created Successfully','rooms':rooms},safe=False)
@csrf_protect
def cartAddRoom(request):
    print("from view addroom")
    cart = Cart(request)
    room = get_object_or_404(Room, id=request.POST.get('id'))
    cart=cart.add(room=room)
    rooms=Room.objects.filter(id__in=cart)
    rooms=list(rooms.values())
    return JsonResponse({'status':'success','meaasge':'Account created Successfully','rooms':rooms},safe=False)

def cartDetails(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})