from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Category, MenuItem
from ..serializers import Categoryserializer
from .constants import MANAGER_GROUP


class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.all()
        serializer = Categoryserializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_staff and not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        serializer = Categoryserializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = Categoryserializer(category)
        return Response(serializer.data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        category = self.get_object(pk)
        if not category:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_staff and not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        serializer = Categoryserializer(category, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_staff and not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        if MenuItem.objects.filter(featured=category).exists():
            return Response(
                {"error": "No se puede eliminar la categoría porque tiene elementos de menú asociados"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
