from django.shortcuts import render
from .models import Division, District, Upazilla
from django.http import JsonResponse, HttpResponse
# Create your views here.
def SubprocessesView(request):
        print(request.POST.get('id'))
        if request.POST.get('id') == 'id_division':
            division=Division.objects.filter(id=request.POST.get('value')).first()
            district=District.objects.filter(division=division)
            district=list(district.values())

        if request.POST.get('id') == 'id_district':
            division=District.objects.filter(id=request.POST.get('value')).first()
            upazilla=Upazilla.objects.filter(district=division)
            district=list(upazilla.values())
        return JsonResponse({'status':'success','meaasge':'Account created Successfully','district':district},safe=False)
