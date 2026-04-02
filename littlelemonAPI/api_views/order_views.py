from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import DELIVERY_GROUP, MANAGER_GROUP
from ..models import Cart, Order, OrderItem, OrderStatus
from ..serializers import OrderItemserializers, Orderserializers


class OrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = Orderserializers(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"error": "El carrito está vacío."}, status=status.HTTP_400_BAD_REQUEST)

        total = sum(item.price for item in cart_items)
        order = Order.objects.create(user=request.user, total=total, date=timezone.now().date())

        order_items = [
            OrderItem(
                order=order,
                menuitem=item.MenuItem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price,
            )
            for item in cart_items
        ]
        OrderItem.objects.bulk_create(order_items)
        cart_items.delete()

        serializer = Orderserializers(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.user != request.user:
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        order_items = OrderItem.objects.filter(order=order)
        serializer = OrderItemserializers(order_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrdersAllView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)
        orders = Order.objects.all()
        serializer = Orderserializers(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        order = get_object_or_404(Order, pk=pk)

        if "status" in request.data:
            new_status = str(request.data["status"]).upper()
            valid_statuses = {choice[0] for choice in OrderStatus.choices}
            if new_status not in valid_statuses:
                return Response(
                    {
                        "error": (
                            "Status inválido. Valores permitidos: "
                            f"{', '.join(sorted(valid_statuses))}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            order.status = new_status

        crew_id = request.data.get("delivery_crew_id")
        if crew_id is None and "delivery_crew_ids" in request.data:
            crew_ids = request.data["delivery_crew_ids"]
            if isinstance(crew_ids, list) and crew_ids:
                crew_id = crew_ids[0]
            elif crew_ids:
                crew_id = crew_ids

        if crew_id is not None:
            try:
                delivery_user = User.objects.get(pk=crew_id)
            except User.DoesNotExist:
                return Response(
                    {"error": f"El usuario con id {crew_id} no existe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not delivery_user.groups.filter(name=DELIVERY_GROUP).exists():
                return Response(
                    {"error": f"El usuario con id {crew_id} no pertenece al grupo de entrega."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            order.delivery_crew = delivery_user

        if request.data.get("delivery_crew_id") is None and request.data.get("clear_delivery_crew") is True:
            order.delivery_crew = None

        order.save()
        serializer = Orderserializers(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.user != request.user and not request.user.groups.filter(name=MANAGER_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)
        order.delete()
        return Response({"message": "Pedido eliminado."}, status=status.HTTP_200_OK)


class DeliveryOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.groups.filter(name__in=[MANAGER_GROUP, DELIVERY_GROUP]).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        if request.user.groups.filter(name=MANAGER_GROUP).exists():
            orders = Order.objects.filter(delivery_crew__isnull=False).distinct()
        else:
            orders = Order.objects.filter(delivery_crew=request.user)

        serializer = Orderserializers(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeliveryOrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.groups.filter(name=DELIVERY_GROUP).exists():
            return Response({"error": "Acceso no autorizado."}, status=status.HTTP_403_FORBIDDEN)

        order = get_object_or_404(Order, pk=pk)
        if order.delivery_crew_id != request.user.id:
            return Response(
                {"error": "Solo puedes actualizar pedidos asignados a ti."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if "status" not in request.data:
            return Response(
                {"error": "El campo 'status' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_status = str(request.data["status"]).upper()
        allowed_statuses = {OrderStatus.IN_DELIVERY, OrderStatus.DELIVERED, OrderStatus.CANCELLED}
        if new_status not in allowed_statuses:
            return Response(
                {
                    "error": (
                        "Status inválido para repartidor. "
                        "Usa IN_DELIVERY, DELIVERED o CANCELLED."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        order.save()
        serializer = Orderserializers(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
