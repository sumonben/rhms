from django.shortcuts import render
import os
import string
import random
from django.conf import settings
from sslcommerz_lib import SSLCOMMERZ
from .models import PaymentGateway,Transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse 
from django.views.generic import View, TemplateView, DetailView
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse,HttpResponseNotFound
from datetime import datetime
from django.db.models import Q
# Create your views here.
gateway = PaymentGateway.objects.filter(is_active=True).first()
cradentials = {'store_id': gateway.store_id,
            'store_pass': gateway.store_pass, 'issandbox': gateway.is_sandbox}
  
sslcommez = SSLCOMMERZ(cradentials)



@method_decorator(csrf_exempt, name='dispatch')
class CheckoutSuccessView(View):
    model = Transaction
    template_name = 'payment/payment_receipt.html'
    
    def get(self, request, *args, **kwargs):
        return HttpResponse('nothing to see')

    def post(self, request, *args, **kwargs):
        
        context={}
        data = self.request.POST
        #print(data)

        
        #print(tran_purpose.payment_type.id)
        transaction=Transaction.objects.filter(val_id=data['val_id']).first()
        #tran_type=PaymentType.objects.filter(id=data['value_d']).first()
        
        return render(request,self.template_name,context)



@method_decorator(csrf_exempt, name='dispatch')
class CheckoutIPNView(View):
    model = Transaction
    template_name = 'payment/payment_receipt.html'
    
    def get(self, request, *args, **kwargs):
        return HttpResponse('nothing to see')

    def post(self, request, *args, **kwargs):
        
        context={}
        data = self.request.POST
        post_body={}
        # print(data)
        

        if data['status'] == 'VALID' and data['store_id'] == gateway.store_id:
            post_body['val_id'] = data['val_id']
            response = sslcommez.validationTransactionOrder(post_body['val_id'])
            transaction=Transaction.objects.create(
                            class_roll=student.class_roll,
                            name = student.name,
                            group=student.group,
                            session=student.session,
                            department=student.department,
                            phone=data['value_c'],
                            email=data['value_c'],
                            tran_id=data['tran_id'],
                            tran_purpose=tran_purpose,
                            val_id=data['val_id'],
                            amount=data['amount'],
                            card_type=data['card_type'],
                            card_no=data['card_no'],
                            store_amount=data['store_amount'],
                            bank_tran_id=data['bank_tran_id'],
                            status=data['status'],
                            tran_date=data['tran_date'],
                            currency=data['currency'],
                            card_issuer=data['card_issuer'],
                            card_brand=data['card_brand'],
                            card_issuer_country=data['card_issuer_country'],
                            card_issuer_country_code=data['card_issuer_country_code'],
                            verify_sign=data['verify_sign'],
                            verify_sign_sha2=data['verify_sign_sha2'],
                            currency_rate=data['currency_rate'],
                            risk_title=data['risk_title'],
                            risk_level=data['risk_level'],
            
                        )
        elif data['store_id'] == gateway.store_id:
            transaction=Transaction.objects.create(
                            class_roll=data['value_a'],
                            name = data['value_b'],
                            group=student.group,
                            session=student.session,
                            department=student.department,
                            phone=data['value_c'],
                            email=data['value_c'],
                            tran_id=data['tran_id'],
                            tran_purpose=tran_purpose,
                            val_id="None",
                            amount=data['amount'],
                            card_type=data['card_type'],
                            card_no=data['card_no'],
                            store_amount=0,
                            bank_tran_id=data['bank_tran_id'],
                            status=data['status'],
                            tran_date=data['tran_date'],
                            currency=data['currency'],
                            card_issuer=data['card_issuer'],
                            card_brand=data['card_brand'],
                            card_issuer_country=data['card_issuer_country'],
                            card_issuer_country_code=data['card_issuer_country_code'],
                            verify_sign=data['verify_sign'],
                            verify_sign_sha2=data['verify_sign_sha2'],
                            currency_rate=data['currency_rate'],
                            risk_title='None',
                            risk_level='0',
            
                        )            # if response['status']== 'VALID' or response['status']== 'VALIDATED' or response['status'] == 'INVALID_TRANSACTION':
        
        else:
            transaction=Transaction.objects.create(
                            class_roll=data['value_a'],
                            name = data['value_b'],
                            group=student.group,
                            session=student.session,
                            department=student.department,
                            phone=data['value_c'],
                            email=data['value_c'],
                            tran_id=data['tran_id'],
                            tran_purpose=tran_purpose,
                            val_id="None",
                            amount=data['amount'],
                            card_type=data['card_type'],
                            card_no=data['card_no'],
                            store_amount=0,
                            bank_tran_id=data['bank_tran_id'],
                            status='RISKY TRANSACTION',
                            tran_date=data['tran_date'],
                            currency=data['currency'],
                            card_issuer=data['card_issuer'],
                            card_brand=data['card_brand'],
                            card_issuer_country=data['card_issuer_country'],
                            card_issuer_country_code=data['card_issuer_country_code'],
                            verify_sign=data['verify_sign'],
                            verify_sign_sha2=data['verify_sign_sha2'],
                            currency_rate=data['currency_rate'],
                            risk_title='None',
                            risk_level='0',
            
                        )
        messages.success(request,'Something Went Wrong! or attacked by intruders')
        context['messages']=messages
        # print('IPN Hit Exeption: ',data)
        return redirect('/')



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

