from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import View, TemplateView, DetailView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models import Q
from datetime import datetime
import os
import string
import random

from .models import PaymentGateway, Transaction
from rhms.models import Booking
from accounts.models import Guest
from rooms.models import Room


# Create your views here.



@method_decorator(csrf_exempt, name='dispatch')
class CheckoutSuccessView(View):
    model = Transaction
    template_name = 'payment/success.html'
    
    def get(self, request, *args, **kwargs):
        # Support GET requests with transaction ID
        # SSL Commerz often uses GET for success callback
        from payment.sslcommerz import process_payment_callback
        from rhms.models import Booking
        
        # Get transaction ID from query parameters
        tran_id = request.GET.get('tran_id')
        
        print(f"GET /payment/success/ - tran_id: {tran_id}")
        print(f"GET parameters: {dict(request.GET)}")
        
        if tran_id:
            context = {}
            transaction = Transaction.objects.filter(tran_id=tran_id).first()
            
            if transaction:
                print(f"Found transaction: {transaction.tran_id}, Status: {transaction.status}")
                
                # Check if booking already exists
                booking = Booking.objects.filter(transaction=transaction).first()
                
                if not booking and transaction.status == 'VALID':
                    # Try to create booking from GET callback data
                    print(f"No booking found, attempting to create from GET data...")
                    transaction_updated, booking = process_payment_callback(dict(request.GET), request)
                    if booking:
                        print(f"✅ Booking created from GET callback: {booking.id}")
                    else:
                        print(f"⚠ Could not create booking from GET callback")
                
                context['transaction'] = transaction
                context['guest'] = transaction.guest
                context['rooms'] = transaction.room.all()
                context['booking'] = booking
                
                # Get individual room booking dates from transaction (more reliable than session)
                booking_dates = transaction.booking_dates_json if hasattr(transaction, 'booking_dates_json') and transaction.booking_dates_json else {}
                # Fallback to session if transaction doesn't have it
                if not booking_dates:
                    booking_dates = request.session.get('booking_dates', {})
                context['booking_dates'] = booking_dates
                print(f"📅 Booking dates passed to template: {booking_dates}")
                
                # Calculate duration if booking exists
                if booking and booking.start_day and booking.end_day:
                    duration = (booking.end_day - booking.start_day).days
                    context['nights'] = duration
                    context['total_nights'] = duration
                    
                if booking:
                    messages.success(request, 'Booking confirmed successfully!')
                else:
                    messages.warning(request, 'Payment received but booking needs to be confirmed manually.')
                
                return render(request, self.template_name, context)
        
        return HttpResponse('No transaction found')

    def post(self, request, *args, **kwargs):
        from rhms.models import Booking
        from payment.sslcommerz import process_payment_callback
        
        print(f"POST /payment/success/ received")
        print(f"POST data keys: {list(request.POST.keys())}")
        print(f"Session keys: {list(request.session.keys())}")
        
        context = {}
        data = self.request.POST
        
        # Use the new helper function to process payment
        print(f"Calling process_payment_callback...")
        transaction, booking = process_payment_callback(data, request)
        
        if transaction:
            print(f"Transaction processed: {transaction.tran_id}, Booking: {'Created' if booking else 'NOT CREATED'}")
            context['transaction'] = transaction
            context['guest'] = transaction.guest
            context['rooms'] = transaction.room.all()
            context['booking'] = booking
            
            # Get individual room booking dates from transaction (more reliable than session)
            booking_dates = transaction.booking_dates_json if hasattr(transaction, 'booking_dates_json') and transaction.booking_dates_json else {}
            # Fallback to session if transaction doesn't have it
            if not booking_dates:
                booking_dates = request.session.get('booking_dates', {})
            context['booking_dates'] = booking_dates
            print(f"📅 Booking dates passed to template: {booking_dates}")
            
            # Calculate duration if booking exists
            if booking and booking.start_day and booking.end_day:
                duration = (booking.end_day - booking.start_day).days
                context['nights'] = duration
                context['total_nights'] = duration
            
            if transaction.status == 'VALID':
                if booking:
                    messages.success(request, 'Payment completed successfully! Booking confirmed.')
                else:
                    messages.warning(request, 'Payment completed but booking creation pending.')
            else:
                messages.warning(request, f'Payment status: {transaction.status}')
        else:
            print(f"❌ Transaction processing failed!")
            messages.error(request, 'Failed to process payment')
            return redirect('frontpage')
        
        return render(request, self.template_name, context)



@method_decorator(csrf_exempt, name='dispatch')
class CheckoutIPNView(View):
    model = Transaction
    template_name = 'payment/payment_receipt.html'
    
    def get(self, request, *args, **kwargs):
        return HttpResponse('nothing to see')

    def post(self, request, *args, **kwargs):
        from payment.sslcommerz import process_payment_callback
        
        data = self.request.POST
        
        # Check if transaction already exists
        existing_transaction = Transaction.objects.filter(tran_id=data.get('tran_id')).first()
        if existing_transaction:
            return HttpResponse('Transaction already processed')
        
        # Use the new helper function to process payment
        transaction, booking = process_payment_callback(data, request)
        
        if transaction:
            if transaction.status == 'VALID':
                return HttpResponse('IPN processed successfully - Order confirmed')
            else:
                return HttpResponse(f'IPN processed - Status: {transaction.status}')
        else:
            return HttpResponse('Failed to process IPN')



@method_decorator(csrf_exempt, name='dispatch')
class CheckoutFaildView(View):
    template_name = 'payment/failed.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        data=request.POST
        context={}
        return HttpResponse('Payment Failed')

@method_decorator(csrf_exempt, name='dispatch')
class CheckoutCanceledView(View):
    template_name = 'payment/canceled.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        data=request.POST
        context={}
        return HttpResponse('Payment Cancailed')

