from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm, AllergyProfileForm, ScanForm
from .models import ScanHistory, FoodItem, AllergyProfile
from .ml_model.load_model import predict_food  
import random
def home(request):
    history = []
    if request.user.is_authenticated:
        user = request.user
        if user.is_active and (user.is_staff or user.is_superuser):
                return redirect('adminpanel:dashboard')
        history = (ScanHistory.objects
                   .filter(user=request.user)
                   .select_related('food_item')
                   .order_by('-scanned_at'))
    return render(request, 'home.html', {'history': history})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            AllergyProfile.objects.create(user=user)
            login(request, user)
            return redirect('profile')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_active and (user.is_staff or user.is_superuser):
                return redirect('adminpanel:dashboard')
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile(request):
    profile, created = AllergyProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = AllergyProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = AllergyProfileForm(instance=profile)
    return render(request, 'profile.html', {'form': form})

# CONFIDENCE_THRESHOLD = 0.6  # Set your desired threshold (60%)

# from django.db.models import Prefetch
# @login_required
# def scan_food(request):
#     if request.method == 'POST':
#         form = ScanForm(request.POST, request.FILES)
#         if form.is_valid():
#             scan = form.save(commit=False)
#             scan.user = request.user
#             scan.save()

#             food_name, confidence = predict_food(scan.image.path)
#             confidence_pct = round(float(confidence) * 100.0, 2)
#             scan.confidence = confidence_pct
#             scan.save()
#             print(f"Predicted: {food_name} ({confidence_pct}%)")

#             if confidence < CONFIDENCE_THRESHOLD:
#                 return render(request, 'result.html', {
#                     'scan': scan,
#                     'food_name': food_name,
#                     'confidence': confidence_pct,
#                     'allergen_detected': False,
#                     'allergens': None,
#                     'matched_allergens': [],
#                     'low_confidence': True,
#                     'threshold': CONFIDENCE_THRESHOLD * 100,
#                     'alternatives': [],
#                 })

#             try:
#                 food_item = (FoodItem.objects
#                              .prefetch_related('allergens')
#                              .get(name__iexact=food_name))
#             except FoodItem.DoesNotExist:
#                 return render(request, 'scan.html', {
#                     'form': form,
#                     'error': f"The detected food '{food_name}' is not in our database."
#                 })

#             # Sets of names for fast overlap test
#             user_allergen_names = set(
#                 request.user.allergyprofile.allergens.values_list('name', flat=True)
#             )
#             food_allergen_qs = food_item.allergens.all()
#             food_allergen_names = set(food_allergen_qs.values_list('name', flat=True))

#             overlap_names = user_allergen_names & food_allergen_names
#             detected = bool(overlap_names)

#             # Persist detection
#             scan.food_item = food_item
#             scan.allergen_detected = detected
#             scan.save()

#             # Only the user's allergens that are present in this food
#             matched_allergens_qs = food_allergen_qs.filter(name__in=overlap_names)

#             # Alternatives (unchanged)
#             alternatives = []
#             if detected:
#                 candidates = (FoodItem.objects
#                               .exclude(pk=food_item.pk)
#                               .prefetch_related('allergens')
#                               .only('id', 'name'))
#                 safe = []
#                 for fi in candidates:
#                     fi_names = set(fi.allergens.values_list('name', flat=True))
#                     if not (fi_names & overlap_names):
#                         safe.append(fi.name)
#                 alternatives = sorted(safe)[:3]

#             context = {
#                 'scan': scan,
#                 'food_name': food_name,
#                 'confidence': confidence_pct,
#                 'allergen_detected': detected,
#                 'allergens': matched_allergens_qs,   # pass only user-triggering allergens
#                 'matched_allergens': matched_allergens_qs,  # alias if template uses this name
#                 'low_confidence': False,
#                 'alternatives': alternatives,
#             }
#             return render(request, 'result.html', context)
#     else:
#         form = ScanForm()

#     return render(request, 'scan.html', {'form': form})


from django.db.models import Prefetch
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Confidence threshold (e.g., 40% for full Food-101)
CONFIDENCE_THRESHOLD = 0.40

@login_required
def scan_food(request):
    if request.method == 'POST':
        form = ScanForm(request.POST, request.FILES)
        if form.is_valid():
            scan = form.save(commit=False)
            scan.user = request.user
            scan.save()

            # Predict food
            predicted_name, confidence_raw = predict_food(scan.image.path)
            # `predict_food` now returns display name like 'Apple Pie'
            confidence_pct = round(float(confidence_raw) * 100, 2)
            scan.confidence = confidence_pct
            print(f"Predicted: {predicted_name} ({confidence_pct}%)")

            # Threshold check
            if confidence_raw < CONFIDENCE_THRESHOLD:
                context = {
                    'scan': scan,
                    'food_name': predicted_name,
                    'confidence': confidence_pct,
                    'allergen_detected': False,
                    'allergens': [],
                    'matched_allergens': [],
                    'low_confidence': True,
                    'threshold': int(CONFIDENCE_THRESHOLD * 100),
                    'alternatives': [],
                }
                return render(request, 'result.html', context)

            # Find matching food item (case-insensitive)
            try:
                food_item = FoodItem.objects.prefetch_related('allergens').get(name__iexact=predicted_name)
                print(f"Matched DB item: {food_item.name}")
            except FoodItem.DoesNotExist:
                print(f"Food item '{predicted_name}' not found in DB.")
                # Food not in DB — don't fail, show low help
                return render(request, 'result.html', {
                    'scan': scan,
                    'food_name': predicted_name,
                    'confidence': confidence_pct,
                    'allergen_detected': False,
                    'allergens': [],
                    'matched_allergens': [],
                    'message': f"'{predicted_name}' is not supported yet.",
                })

            # Update scan
            scan.food_item = food_item
            scan.allergen_detected = False
            scan.save()

            # Safety check: user profile exists?
            try:
                profile = request.user.allergyprofile
                user_allergens = set(profile.allergens.values_list('name', flat=True))
                food_allergens = set(food_item.allergens.values_list('name', flat=True))
                triggering = user_allergens & food_allergens
                detected = len(triggering) > 0

                # Save result
                scan.allergen_detected = detected
                scan.save()

                # Matched allergens queryset
                matched_qs = food_item.allergens.filter(name__in=triggering)

                # Alternatives: 3 safest options
                alternatives = []
                if detected:
                    candidates = FoodItem.objects.exclude(pk=food_item.pk).prefetch_related('allergens')
                    safe = [
                        fi.name for fi in candidates
                        if not (set(fi.allergens.values_list('name', flat=True)) & user_allergens)
                    ]
                    if len(safe) > 3:
                        alternatives = random.sample(safe, 3)  # get 3 random items
                    else:
                        alternatives = safe  # return all if less than 3
            except Exception:  # profile not set etc.
                user_allergens = set()
                triggering = set()
                matched_qs = []
                detected = False
                alternatives = []

            # Final context
            context = {
                'scan': scan,
                'food_name': predicted_name,
                'confidence': confidence_pct,
                'allergen_detected': detected,
                'allergens': matched_qs,
                'matched_allergens': matched_qs,
                'low_confidence': False,
                'alternatives': alternatives,
            }
            return render(request, 'result.html', context)
    else:
        form = ScanForm()

    return render(request, 'scan.html', {'form': form})

