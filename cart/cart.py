# cart/cart.py
from decimal import Decimal
from django.conf import settings
from rooms.models import Room
class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, room, quantity=1, override_quantity=False):
        room_id = str(room.id)
        if room_id not in self.cart:
            self.cart[room_id] = {'quantity': 0, 'price': str(room.price)}
        if override_quantity:
            self.cart[room_id]['quantity'] = quantity
        else:
            self.cart[room_id]['quantity'] += quantity
        self.save()
        return self.session[settings.CART_SESSION_ID]
        
    def remove(self, room):
        room_id = str(room.id)
        if room_id in self.cart:
            del self.cart[room_id]
            self.save()

    def __iter__(self):
        room_ids = self.cart.keys()
        rooms = Room.objects.filter(id__in=room_ids)
        cart = self.cart.copy()
        for room in rooms:
            cart[str(room.id)]['room'] = room
        for item in cart.values():
            item['price'] = int(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def get_total_price(self):
        return sum(int(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def save(self):
        self.session.modified = True

# Add methods for removing items, updating quantities, and calculating totals