from ..models import Cart, MenuItem
from ..serializers import Cartserializers
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        serializer = Cartserializers(cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        menu_item_id = request.data.get("menu_item_id")
        quantity = request.data.get("quantity", 1)

        if not menu_item_id:
            return Response({"error": "Se requiere menu_item_id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            menu_item = MenuItem.objects.get(id=menu_item_id)
        except MenuItem.DoesNotExist:
            return Response(
                {"error": "El elemento del menú no existe."}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            quantity = int(quantity)
        except ValueError:
            return Response({"error": "Cantidad inválida."}, status=status.HTTP_400_BAD_REQUEST)

        unit_price = menu_item.price
        total_price = unit_price * quantity
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            MenuItem=menu_item,
            defaults={"quantity": quantity, "unit_price": unit_price, "price": total_price},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.price = cart_item.quantity * unit_price
            cart_item.save()

        serializer = Cartserializers(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response({"message": "Carrito vaciado."}, status=status.HTTP_200_OK)


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Cart.objects.get(pk=pk, user=request.user)
        except Cart.DoesNotExist:
            return None

    def get(self, request, pk):
        cart_item = self.get_object(request, pk)
        if not cart_item:
            return Response({"error": "Elemento no encontrado en el carrito."}, status=status.HTTP_404_NOT_FOUND)
        serializer = Cartserializers(cart_item)
        return Response(serializer.data)

    def put(self, request, pk):
        cart_item = self.get_object(request, pk)
        if not cart_item:
            return Response({"error": "Elemento no encontrado en el carrito."}, status=status.HTTP_404_NOT_FOUND)

        quantity = request.data.get("quantity")
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"error": "La cantidad debe ser mayor que cero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            return Response({"error": "Cantidad inválida."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.price = cart_item.unit_price * quantity
        cart_item.save()
        serializer = Cartserializers(cart_item)
        return Response(serializer.data)

    def delete(self, request, pk):
        cart_item = self.get_object(request, pk)
        if not cart_item:
            return Response({"error": "Elemento no encontrado en el carrito."}, status=status.HTTP_404_NOT_FOUND)
        cart_item.delete()
        return Response({"message": "Elemento eliminado del carrito."}, status=status.HTTP_200_OK)
