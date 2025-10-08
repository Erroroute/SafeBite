from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users_list, name='users_list'),
    path('foods/', views.food_list, name='food_list'),
    path('foods/create/', views.food_create, name='food_create'),
    path('foods/<int:pk>/edit/', views.food_edit, name='food_edit'),
    path('foods/<int:pk>/delete/', views.food_delete, name='food_delete'),
    path('allergens/', views.allergen_list, name='allergen_list'),
    path('allergens/create/', views.allergen_create, name='allergen_create'),
    path('allergens/<int:pk>/edit/', views.allergen_edit, name='allergen_edit'),
    path('allergens/<int:pk>/delete/', views.allergen_delete, name='allergen_delete'),
    path('scans/', views.scan_list, name='scan_list'),
    path('scans/<int:pk>/delete/', views.scan_delete, name='scan_delete'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),


]
