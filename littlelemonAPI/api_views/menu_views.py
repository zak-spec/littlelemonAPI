from django.core.paginator import EmptyPage, Paginator
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import MenuItem
from ..serializers import MenuItemserializers


class MenuItemsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        items = MenuItem.objects.select_related("featured").all()
        category_name = request.query_params.get("category")
        to_price = request.query_params.get("to_price")
        search = request.query_params.get("search")
        ordering = request.query_params.get("ordering")
        perpage = request.query_params.get("perpage", default=5)
        page = request.query_params.get("page", default=1)

        if category_name:
            items = items.filter(featured__title=category_name)
        if to_price:
            items = items.filter(price__lte=to_price)
        if search:
            items = items.filter(title__icontains=search)
        if ordering:
            ordering_fields = ordering.split(",")
            items = items.order_by(*ordering_fields)

        paginator = Paginator(items, per_page=perpage)
        try:
            items_page = paginator.page(number=page)
        except EmptyPage:
            items_page = []

        serializer = MenuItemserializers(items_page, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MenuItemserializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MenuItemDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        return get_object_or_404(MenuItem, id=pk)

    def get(self, request, pk):
        serializer = MenuItemserializers(self.get_object(pk))
        return Response(serializer.data)

    def patch(self, request, pk):
        item = self.get_object(pk)
        serializer = MenuItemserializers(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        item = self.get_object(pk)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
