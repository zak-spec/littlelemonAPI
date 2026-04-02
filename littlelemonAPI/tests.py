from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Cart, Category, MenuItem, Order, OrderItem


class LittleLemonAPISmokeTests(APITestCase):
	def setUp(self):
		self.user_password = "StrongPass123!"
		self.user = User.objects.create_user(
			username="testuser",
			email="test@example.com",
			password=self.user_password,
		)
		self.category = Category.objects.create(title="Bebidas", slug="bebidas")
		self.menu_item = MenuItem.objects.create(
			title="Limonada",
			price=Decimal("4.50"),
			featured=self.category,
		)

	def authenticate_with_jwt(self):
		token_response = self.client.post(
			"/api/token/",
			{"username": self.user.username, "password": self.user_password},
			format="json",
		)
		self.assertEqual(token_response.status_code, status.HTTP_200_OK)
		access_token = token_response.data.get("access")
		self.assertIsNotNone(access_token)
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

	def test_root_endpoint_returns_ok(self):
		response = self.client.get("/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("message", response.json())

	def test_can_obtain_jwt_token(self):
		response = self.client.post(
			"/api/token/",
			{"username": self.user.username, "password": self.user_password},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("access", response.data)
		self.assertIn("refresh", response.data)

	def test_public_menu_list_works(self):
		response = self.client.get("/api/menu-items/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertGreaterEqual(len(response.data), 1)

	def test_authenticated_user_can_add_to_cart(self):
		self.authenticate_with_jwt()
		response = self.client.post(
			"/api/cart/menu-items/add/",
			{"menu_item_id": self.menu_item.id, "quantity": 2},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)

	def test_authenticated_user_can_create_order_from_cart(self):
		self.authenticate_with_jwt()
		Cart.objects.create(
			user=self.user,
			MenuItem=self.menu_item,
			quantity=2,
			unit_price=self.menu_item.price,
			price=self.menu_item.price * 2,
		)

		response = self.client.post("/api/orders/create/", {}, format="json")
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Order.objects.filter(user=self.user).count(), 1)
		self.assertEqual(OrderItem.objects.count(), 1)
		self.assertEqual(Cart.objects.filter(user=self.user).count(), 0)
