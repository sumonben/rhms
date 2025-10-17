from django.shortcuts import render
from django.views.generic import View, TemplateView, DetailView
from rooms.models import Room,RoomType
from accounts.models import Staff, Guest,Designation, Department
class Frontpage(View):
    template_name = 'frontpage/index.html'
    
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

