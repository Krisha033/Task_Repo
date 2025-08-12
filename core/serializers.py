from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import Category, Product, Task

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, required=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RecursiveCategorySerializer(serializers.Serializer):
    def to_representation(self, instance):
        return CategorySerializer(instance, context=self.context).data


class CategorySerializer(serializers.ModelSerializer):
    subcategories = RecursiveCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "description", "parent", "subcategories",
                  "is_active", "is_deleted", "created_at", "updated_at", "created_by", "updated_by")
        read_only_fields = ("is_deleted", "created_at", "updated_at", "created_by", "updated_by")


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(is_deleted=False))

    class Meta:
        model = Product
        fields = ("id", "category", "name", "price", "stock", "description",
                  "is_active", "is_deleted", "created_at", "updated_at", "created_by", "updated_by")
        read_only_fields = ("is_deleted", "created_at", "updated_at", "created_by", "updated_by")


class TaskSerializer(serializers.ModelSerializer):
    assigned_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_deleted=False))

    class Meta:
        model = Task
        fields = ("id", "product", "title", "description", "status", "assigned_user", "due_date",
                  "created_at", "updated_at", "is_deleted")
        read_only_fields = ("created_at", "updated_at", "is_deleted")

    def validate_due_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("due_date must be in the future.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user with this email.")
        return value

    def save(self):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        # In dev we send via console, so return token/uid so tests can assert if needed
        return {"email": user.email, "token": token, "uid": uid}


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6)

    def validate(self, attrs):
        from django.utils.http import urlsafe_base64_decode
        try:
            uid = urlsafe_base64_decode(attrs["uid"]).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            raise serializers.ValidationError("Invalid uid")
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid token")
        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
