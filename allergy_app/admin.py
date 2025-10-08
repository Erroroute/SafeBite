from django.contrib import admin
from django.utils.html import format_html

from .models import Allergen, AllergyProfile, FoodItem, ScanHistory


@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    ordering = ["name"]
    list_per_page = 25  # usability in larger datasets


class AllergyProfileInline(admin.StackedInline):
    model = AllergyProfile
    extra = 0
    filter_horizontal = ["allergens"]


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "allergen_list", "short_ingredients"]
    search_fields = ["name", "ingredients", "allergens__name"]
    list_filter = ["allergens"]
    filter_horizontal = ["allergens"]
    ordering = ["name"]
    list_per_page = 25

    def allergen_list(self, obj):
        return ", ".join(a.name for a in obj.allergens.all()) or "-"
    allergen_list.short_description = "Allergens"

    def short_ingredients(self, obj):
        if not obj.ingredients:
            return "-"
        text = obj.ingredients.strip()
        return (text[:80] + "…") if len(text) > 80 else text
    short_ingredients.short_description = "Ingredients"


@admin.register(AllergyProfile)
class AllergyProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "user_username", "allergen_count"]
    search_fields = ["user__username", "user__email", "allergens__name"]
    filter_horizontal = ["allergens"]
    list_select_related = ["user"]
    ordering = ["user__username"]
    list_per_page = 25

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = "User"

    def allergen_count(self, obj):
        return obj.allergens.count()
    allergen_count.short_description = "Allergen count"


class FoodItemInline(admin.StackedInline):
    model = ScanHistory
    extra = 0
    fk_name = "food_item"
    fields = ("user", "image_preview", "image", "allergen_detected", "scanned_at")
    readonly_fields = ("image_preview", "scanned_at")
    can_delete = False
    verbose_name = "Scan record"
    verbose_name_plural = "Scan records"

    def image_preview(self, obj):
        if getattr(obj, "image", None) and getattr(obj.image, "url", None):
            return format_html('<img src="{}" style="max-height:120px; max-width:160px; border:1px solid #ddd;"/>', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"


@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "user_username", "food_item_name", "allergen_detected", "scanned_at", "thumbnail"]
    list_filter = ["allergen_detected", "scanned_at", "food_item", "user"]
    search_fields = ["user__username", "food_item__name"]
    date_hierarchy = "scanned_at"
    readonly_fields = ["scanned_at", "image_preview"]
    fields = ["user", "food_item", "image_preview", "image", "allergen_detected", "scanned_at"]
    list_select_related = ["user", "food_item"]
    ordering = ["-scanned_at"]
    list_per_page = 25

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = "User"

    def food_item_name(self, obj):
        return getattr(obj.food_item, "name", "-")
    food_item_name.short_description = "Food"

    def thumbnail(self, obj):
        if getattr(obj, "image", None) and getattr(obj.image, "url", None):
            return format_html('<img src="{}" style="height:40px; width:auto; border-radius:4px;"/>', obj.image.url)
        return "-"
    thumbnail.short_description = "Image"

    def image_preview(self, obj):
        if getattr(obj, "image", None) and getattr(obj.image, "url", None):
            return format_html('<img src="{}" style="max-height:240px; max-width:320px; border:1px solid #ddd;"/>', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"
