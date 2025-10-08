from django.db import models
from django.contrib.auth.models import User

class Allergen(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class AllergyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    allergens = models.ManyToManyField(Allergen)

    def __str__(self):
        return f"{self.user.username}'s Allergy Profile"

class FoodItem(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ingredients = models.TextField()
    allergens = models.ManyToManyField(Allergen, blank=True)

    def __str__(self):
        return self.name

class ScanHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem,null=True, blank=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='scans/')
    scanned_at = models.DateTimeField(auto_now_add=True)
    allergen_detected = models.BooleanField(default=False)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) 

    def __str__(self):
        food_name = self.food_item.name if self.food_item else "Unknown"
        return f"{self.user.username} - {food_name}"
