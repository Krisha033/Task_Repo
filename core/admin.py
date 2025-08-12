from django.contrib import admin
from .models import Category, Product, Task

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "is_active", "is_deleted")
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "stock", "is_active", "is_deleted")
    search_fields = ("name", "description")

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "product", "assigned_user", "status", "due_date", "is_deleted")
    list_filter = ("status", "due_date")
