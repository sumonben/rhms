from django.shortcuts import render
from django.views.generic import View, TemplateView, DetailView
from rooms.models import Room,RoomType
from accounts.models import Staff, Guest,Designation, Department

class Rooms(View):
    template_name = 'rooms/rooms.html'
    
    def get(self, request, *args, **kwargs):
        rooms=Room.objects.all().order_by("serial")
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        context={}
        context['rooms']=rooms
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

class RoomDetails(View):
    template_name = 'rooms/room_details.html'
    
    def get(self, request, *args, **kwargs):
        rooms=Room.objects.filter(id=int(kwargs['id'])).first()
        staffs=Staff.objects.all().order_by("serial")
        guests=Guest.objects.all().order_by("-id")
        context={}
        context['room']=rooms
        context['staffs']=staffs
        context['guests']=guests
        return render(request, self.template_name,context)

    def post(self, request, *args, **kwargs):
        context={}
        return render(request, self.template_name,context)

        # admission_type=request.POST.get('admission_type')
        # student_category=StudentCategory.objects.filter(id=admission_type).first()
        # if student_category.title_en=='HSC':
        #     return redirect('admission_login')
        # else:
        #     return redirect('admission_login_others')

