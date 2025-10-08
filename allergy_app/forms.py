from django import forms
from django.contrib.auth.models import User
from .models import AllergyProfile, Allergen, ScanHistory

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords don't match.")
        return cd['password2']

class AllergyProfileForm(forms.ModelForm):
    allergens = forms.ModelMultipleChoiceField(
        queryset=Allergen.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    class Meta:
        model = AllergyProfile
        fields = ['allergens']

class ScanForm(forms.ModelForm):
    class Meta:
        model = ScanHistory
        fields = ['image']

    def clean_image(self):
        img = self.cleaned_data.get('image')
        if not img:
            return img
        name_lower = img.name.lower()
        if not (name_lower.endswith('.jpg') or name_lower.endswith('.jpeg')):
            raise forms.ValidationError('Unsupported image format. Please upload a JPG/JPEG file.')
        if getattr(img, 'content_type', '') != 'image/jpeg':
            raise forms.ValidationError('Unsupported image type. Only JPEG is allowed.')
        return img
