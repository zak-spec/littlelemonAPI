from django.contrib.auth.models import Group, User
from django.core.paginator import EmptyPage, Paginator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import DELIVERY_GROUP, MANAGER_GROUP


class ManagersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        managers = User.objects.filter(groups__name=MANAGER_GROUP)
        managers_data = [{"id": u.id, "username": u.username, "email": u.email} for u in managers]
        return Response(managers_data)


class ManagerRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, userId):
        try:
            group = Group.objects.get(name=MANAGER_GROUP)
        except Group.DoesNotExist:
            return Response({"error": "El grupo Manager no existe."}, status=status.HTTP_404_NOT_FOUND)

        try:
            target_user = User.objects.get(pk=userId)
        except User.DoesNotExist:
            return Response({"error": "El usuario no existe."}, status=status.HTTP_404_NOT_FOUND)

        if group not in target_user.groups.all():
            return Response(
                {"error": "Usuario no pertenece al grupo de gerentes."},
                status=status.HTTP_404_NOT_FOUND,
            )

        target_user.groups.remove(group)
        return Response({"message": "Usuario eliminado del grupo de gerentes."}, status=status.HTTP_200_OK)


class DeliveryCrewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        delivery_users = User.objects.filter(groups__name=DELIVERY_GROUP)
        data = [{"id": u.id, "username": u.username, "email": u.email} for u in delivery_users]
        return Response(data)


class DeliveryCrewRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, userId):
        try:
            group = Group.objects.get(name=DELIVERY_GROUP)
        except Group.DoesNotExist:
            return Response(
                {"error": "El grupo Delivery_crew no existe."}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            target_user = User.objects.get(pk=userId)
        except User.DoesNotExist:
            return Response({"error": "El usuario no existe."}, status=status.HTTP_404_NOT_FOUND)

        if group not in target_user.groups.all():
            return Response(
                {"error": "El usuario no pertenece al grupo Delivery_crew."},
                status=status.HTTP_404_NOT_FOUND,
            )

        target_user.groups.remove(group)
        return Response(
            {"message": "Usuario eliminado del grupo de Delivery_crew."}, status=status.HTTP_200_OK
        )


class GroupListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff and not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        groups = Group.objects.all().order_by("name")
        data = [{"id": group.id, "name": group.name, "user_count": group.user_set.count()} for group in groups]
        return Response(data)

    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "Solo administradores pueden crear grupos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        name = request.data.get("name")
        if not name:
            return Response(
                {"error": "Se requiere un nombre para el grupo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Group.objects.filter(name=name).exists():
            return Response(
                {"error": "Ya existe un grupo con este nombre."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = Group.objects.create(name=name)
        return Response(
            {"id": group.id, "name": group.name, "message": "Grupo creado correctamente"},
            status=status.HTTP_201_CREATED,
        )


class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return None

    def get(self, request, pk):
        if not request.user.is_staff and not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        group = self.get_object(pk)
        if not group:
            return Response(status=status.HTTP_404_NOT_FOUND)

        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 20))
        users = group.user_set.all().order_by("username")
        paginator = Paginator(users, per_page)

        try:
            paginated_users = paginator.page(page)
        except EmptyPage:
            paginated_users = []

        users_data = [{"id": user.id, "username": user.username, "email": user.email} for user in paginated_users]
        return Response(
            {
                "id": group.id,
                "name": group.name,
                "user_count": group.user_set.count(),
                "users": users_data,
                "page": page,
                "pages": paginator.num_pages,
            }
        )

    def put(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {"error": "Solo administradores pueden modificar grupos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        group = self.get_object(pk)
        if not group:
            return Response(status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name")
        if not name:
            return Response(
                {"error": "Se requiere un nombre para el grupo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Group.objects.filter(name=name).exclude(pk=pk).exists():
            return Response(
                {"error": "Ya existe otro grupo con este nombre."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group.name = name
        group.save()
        return Response({"id": group.id, "name": group.name, "message": "Grupo actualizado correctamente"})

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {"error": "Solo administradores pueden eliminar grupos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        group = self.get_object(pk)
        if not group:
            return Response(status=status.HTTP_404_NOT_FOUND)

        group.delete()
        return Response({"message": "Grupo eliminado correctamente."}, status=status.HTTP_200_OK)


class GroupUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff and not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        try:
            group = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response({"error": "Grupo no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        user_ids = request.data.get("user_ids", [])
        if not isinstance(user_ids, list):
            user_ids = [user_ids]
        if not user_ids:
            return Response(
                {"error": "Se requiere al menos un ID de usuario."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        added_users = []
        errors = []
        for user_id in user_ids:
            try:
                user = User.objects.get(pk=user_id)
                if user not in group.user_set.all():
                    group.user_set.add(user)
                    added_users.append({"id": user.id, "username": user.username})
                else:
                    errors.append(f"Usuario {user.username} ya pertenece al grupo.")
            except User.DoesNotExist:
                errors.append(f"Usuario con ID {user_id} no encontrado.")

        return Response(
            {
                "message": f"Se añadieron {len(added_users)} usuarios al grupo.",
                "added_users": added_users,
                "errors": errors,
            }
        )

    def delete(self, request, pk):
        if not request.user.is_staff and not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        try:
            group = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response({"error": "Grupo no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        user_ids = request.data.get("user_ids", [])
        if not isinstance(user_ids, list):
            user_ids = [user_ids]
        if not user_ids:
            return Response(
                {"error": "Se requiere al menos un ID de usuario."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        removed_users = []
        errors = []
        for user_id in user_ids:
            try:
                user = User.objects.get(pk=user_id)
                if user in group.user_set.all():
                    group.user_set.remove(user)
                    removed_users.append({"id": user.id, "username": user.username})
                else:
                    errors.append(f"Usuario {user.username} no pertenece al grupo.")
            except User.DoesNotExist:
                errors.append(f"Usuario con ID {user_id} no encontrado.")

        return Response(
            {
                "message": f"Se eliminaron {len(removed_users)} usuarios del grupo.",
                "removed_users": removed_users,
                "errors": errors,
            }
        )
