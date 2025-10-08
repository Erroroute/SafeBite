from django import forms
from allergy_app.models import FoodItem, Allergen, ScanHistory  # adjust import if models live in a different app

class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['name','allergens']   # image removed; ingredients spelled correctly
        widgets = {
            'allergens': forms.CheckboxSelectMultiple,
        }

class AllergenForm(forms.ModelForm):
    class Meta:
        model = Allergen
        fields = ['name']
        

class ScanHistoryForm(forms.ModelForm):
    class Meta:
        model = ScanHistory
        fields = ['user', 'food_item', 'image', 'allergen_detected']
