import datetime
from django import forms
from django.forms import modelformset_factory
from .models import Upazilla,District,Division,Address
from django.db.models import Q,Count

class AddressForm(forms.ModelForm):
    division= forms.ModelChoiceField(queryset=None,widget=forms.Select(attrs={'class':'form-control form-control-sm'})),
    district=forms.ModelChoiceField(queryset=None,widget=forms.Select(attrs={'class':'form-control form-control-sm',})),
    upazilla= forms.ModelChoiceField(queryset=Upazilla.objects.all(),widget=forms.Select(attrs={'class':'form-control form-control-sm'})),

    class Meta:
        model = Address
        fields = "__all__"
        exclude=['serial']

        
        widgets = {
            'Others': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder':  'Bogura-5800','onkeypress' : "myFunction(this.id);"}),
            'division': forms.Select(attrs={'class': 'form-control form-control-sm','onchange' : "myFunctionTeacher(this.id);"}),
            'district': forms.Select(attrs={'class': 'form-control form-control-sm','onchange' : "myFunctionTeacher(this.id);"}),            
            'upazilla': forms.Select(attrs={'class': 'form-control form-control-sm',}),


        }