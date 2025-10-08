from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from .decorators import staff_required
from .forms import FoodItemForm, AllergenForm
from allergy_app.models import FoodItem, Allergen, ScanHistory  # adjust module

User = get_user_model()

@login_required
@staff_required
def dashboard(request):
    stats = {
        'users': User.objects.filter(is_staff=False).count(),
        'foods': FoodItem.objects.count(),
        'allergens': Allergen.objects.count(),
        'scans': ScanHistory.objects.count(),
        'alerts': ScanHistory.objects.filter(allergen_detected=True).count(),
    }
    recent_scans = (ScanHistory.objects
                    .select_related('user', 'food_item')
                    .order_by('-scanned_at')[:15])
    
    users = User.objects.order_by('-date_joined')[:20]


    foods = (FoodItem.objects
             .prefetch_related('allergens')
             .order_by('name')[:20])
    
    affected = (Allergen.objects
                .annotate(affected_users=Count('allergyprofile', distinct=True))
                .order_by('name'))
    
    top_foods = (ScanHistory.objects
                 .values('food_item__name')
                 .annotate(n=Count('id'))
                 .order_by('-n')[:5])
    
    return render(request, 'adminpanel/dashboard.html', {
        'stats': stats,
        'top_foods': top_foods,
        'recent_scans': recent_scans,
        'users': users,
        'foods': foods,
        'allergens': affected
        
    })

@login_required 
@staff_required
def users_list(request):
    users = User.objects.order_by('-date_joined')
    return render(request, 'adminpanel/users_list.html', {'users': users})
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django import forms

# Form for editing a user
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
        }

@login_required
@staff_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Prevent editing superuser by non-superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You cannot edit a superuser.")
        return redirect('adminpanel:users_list')

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect('adminpanel:users_list')
    else:
        form = UserEditForm(instance=user)

    # Fetch all scan history for this user
    scans = ScanHistory.objects.filter(user=user).order_by('-scanned_at')
    

    return render(request, 'adminpanel/edit_user.html', {
        'form': form,
        'user_obj': user,
        'scans': scans
    })


def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_staff:
        user.delete()
        messages.success(request, "User deleted successfully.")
    else:
        messages.error(request, "Cannot delete staff users.")
    return redirect('adminpanel:users_list')

@login_required
@staff_required
def food_list(request):
    foods = FoodItem.objects.prefetch_related('allergens').order_by('name')
    return render(request, 'adminpanel/food_list.html', {'foods': foods})

@login_required
@staff_required
def food_create(request):
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Food created.')
            return redirect('adminpanel:food_list')
    else:
        form = FoodItemForm()
    return render(request, 'adminpanel/food_form.html', {'form': form, 'mode':'Create'})

@login_required
@staff_required
def food_edit(request, pk):
    food = get_object_or_404(FoodItem, pk=pk)
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES, instance=food)
        if form.is_valid():
            form.save()
            messages.success(request, 'Food updated.')
            return redirect('adminpanel:food_list')
    else:
        form = FoodItemForm(instance=food)
    return render(request, 'adminpanel/food_form.html', {'form': form, 'mode':'Edit'})

@login_required
@staff_required
def food_delete(request, pk):
    food = get_object_or_404(FoodItem, pk=pk)
    if request.method == 'POST':
        food.delete()
        messages.success(request, 'Food deleted.')
        return redirect('adminpanel:food_list')
    return render(request, 'adminpanel/confirm_delete.html', {'obj': food})

@login_required
@staff_required
def allergen_list(request):
    allergens = Allergen.objects.order_by('name')
    return render(request, 'adminpanel/allergen_list.html', {'allergens': allergens})

@login_required
@staff_required
def allergen_create(request):
    if request.method == 'POST':
        form = AllergenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Allergen created.')
            return redirect('adminpanel:allergen_list')
    else:
        form = AllergenForm()
    return render(request, 'adminpanel/allergen_form.html', {'form': form, 'mode':'Create'})

@login_required 
@staff_required
def allergen_edit(request, pk):
    allergen = get_object_or_404(Allergen, pk=pk)
    if request.method == 'POST':
        form = AllergenForm(request.POST, instance=allergen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Allergen updated.')
            return redirect('adminpanel:allergen_list')
    else:
        form = AllergenForm(instance=allergen)
    return render(request, 'adminpanel/allergen_form.html', {'form': form, 'mode':'Edit'})

@login_required
@staff_required
def allergen_delete(request, pk):
    allergen = get_object_or_404(Allergen, pk=pk)
    if request.method == 'POST':
        allergen.delete()
        messages.success(request, 'Allergen deleted.')
        return redirect('adminpanel:allergen_list')
    return render(request, 'adminpanel/confirm_delete.html', {'obj': allergen})

@login_required 
@staff_required
def scan_list(request):
    scans = (ScanHistory.objects
             .select_related('user', 'food_item')
             .order_by('-scanned_at')[:200])
    return render(request, 'adminpanel/scan_list.html', {'scans': scans})
# views.py
@login_required
@staff_required
def scan_delete(request, pk):
    scan = get_object_or_404(ScanHistory, pk=pk)
    if request.method == 'POST':
        scan.delete()
        messages.success(request, 'Scan deleted.')
        return redirect('adminpanel:scan_list')
    return render(request, 'adminpanel/confirm_delete.html', {'obj': scan})

