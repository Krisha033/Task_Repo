from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail

from .models import Category, Product, Task
from .serializers import (CategorySerializer, ProductSerializer, TaskSerializer,
                          UserSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer)
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_deleted=False)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["parent", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def soft_delete(self, request, pk=None):
        obj = self.get_object()
        obj.soft_delete()
        return Response({"detail": "soft deleted"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.restore()
        return Response({"detail": "restored"}, status=status.HTTP_200_OK)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_deleted=False)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.filter(is_deleted=False)
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "product", "assigned_user"]
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Task.objects.filter(is_deleted=False)
        return Task.objects.filter(assigned_user=user, is_deleted=False)

    def perform_create(self, serializer):
        # allow anyone to create tasks (normal user must assign to themself or admin can assign others)
        serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def soft_delete(self, request, pk=None):
        task = self.get_object()
        # only owner or admin can soft-delete — has_object_permission enforces that.
        task.soft_delete()
        return Response({"detail": "soft deleted"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def restore(self, request, pk=None):
        task = self.get_object()
        task.restore()
        return Response({"detail": "restored"}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "token blacklisted"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"detail": "invalid token"}, status=status.HTTP_400_BAD_REQUEST)


# Password reset: request & confirm
class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        info = serializer.save()
        # Build a simple text email - token & uid printed to console by console backend
        subject = "Password reset request"
        body = f"Use the following token to reset password:\n\nuid: {info['uid']}\ntoken: {info['token']}\n\nPOST to /api/auth/password-reset-confirm/ with {{'uid','token','new_password'}}"
        send_mail(subject, body, None, [info["email"]], fail_silently=False)
        return Response({"detail": "password reset email sent (console)."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"detail": "password updated."}, status=status.HTTP_200_OK)
