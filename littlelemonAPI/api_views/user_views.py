from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, Paginator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import MANAGER_GROUP
from ..serializers import UserSerializer


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff and not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 10))
        search = request.query_params.get("search", "")

        users = User.objects.all().order_by("username")
        if search:
            users = users.filter(username__icontains=search) | users.filter(email__icontains=search)

        paginator = Paginator(users, per_page)
        try:
            users_page = paginator.page(page)
        except EmptyPage:
            users_page = []

        serializer = UserSerializer(users_page, many=True)
        return Response(
            {
                "count": paginator.count,
                "pages": paginator.num_pages,
                "current_page": page,
                "results": serializer.data,
            }
        )


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        if not (
            request.user.is_staff
            or request.user.groups.filter(name=MANAGER_GROUP).exists()
            or request.user.id == int(pk)
        ):
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object(pk)
        if not user:
            return Response(status=status.HTTP_404_NOT_FOUND)

        groups = [group.name for group in user.groups.all()]
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_active": user.is_active,
            "groups": groups,
            "date_joined": user.date_joined,
        }
        return Response(data)

    def put(self, request, pk):
        return self._update(request, pk)

    def patch(self, request, pk):
        return self._update(request, pk)

    def _update(self, request, pk):
        if not (
            request.user.is_staff
            or request.user.groups.filter(name=MANAGER_GROUP).exists()
            or request.user.id == int(pk)
        ):
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object(pk)
        if not user:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if request.user.id != int(pk) and not (
            request.user.is_staff or request.user.groups.filter(name=MANAGER_GROUP).exists()
        ):
            return Response(
                {"error": "No tienes permisos para modificar este usuario."},
                status=status.HTTP_403_FORBIDDEN,
            )

        allowed_fields = ["first_name", "last_name", "email"]
        if request.user.is_staff:
            allowed_fields.extend(["is_active", "username"])

        filtered_data = {field: request.data[field] for field in allowed_fields if field in request.data}
        for key, value in filtered_data.items():
            setattr(user, key, value)

        try:
            user.save()
            return Response({"message": "Usuario actualizado correctamente"})
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {"error": "Solo administradores pueden desactivar usuarios."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object(pk)
        if not user:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.is_active = False
        user.save()
        return Response({"message": "Usuario desactivado correctamente"}, status=status.HTTP_200_OK)
