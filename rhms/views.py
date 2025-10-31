from django.shortcuts import render
from django.views.generic import View, TemplateView, DetailView
from rooms.models import Room,RoomType
from .models import Carousel
from accounts.models import Staff, Guest,Designation, Department
class Frontpage(View):
    template_name = 'frontpage/frontpage.html'
    
    def get(self, request, *args, **kwargs):
        rooms=Room.objects.all().order_by("serial")
        carousels=Carousel.objects.all().order_by("serial")[0:4]
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        context={}
        context['rooms']=rooms
        context['carousels']=carousels
        context['staffs']=staffs
        context['guests']=guests
        return render(request, self.template_name,context)

    def post(self, request, *args, **kwargs):
        pass
        # context={}
        # admission_type=request.POST.get('admission_type')
        # student_category=StudentCategory.objects.filter(id=admission_type).first()
        # if student_category.title_en=='HSC':
        #     return redirect('admission_login')
        # else:
        #     return redirect('admission_login_others')

