from django.urls import path
from . import views
urlpatterns = [
    path('register/', views.RegisterUserView.as_view(), name="register_user"),
    path('users/users/me/', views.CurrentUserView.as_view(), name="current_user"),
    path('secret/', views.SecretV2View.as_view(), name="secreto"),
    path('throttle-check/', views.ThrottleCheckView.as_view(), name="throttle_check"),
    path("throttle-check-auth/", views.ThrottleCheckAuthView.as_view(), name="throttle_check_auth"),
    # Rutas para menú
    path('menu-items/', views.MenuItemsView.as_view(), name="menu_items"),
    path('menu-items/<str:pk>/', views.MenuItemDetailView.as_view(), name="menu_item_detail"),
    
    # Rutas para categorías
    path('categories/', views.CategoryListCreateView.as_view(), name="create_category"),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name="category_detail"),
    
    # Rutas para usuarios
    path('users/', views.UserListView.as_view(), name="user_list"),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name="user_detail"),
    
    # Rutas para grupos
    path('groups/', views.GroupListView.as_view(), name="group_list"),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name="group_detail"),
    path('groups/<int:pk>/users/', views.GroupUsersView.as_view(), name="group_users"),
    path('groups/manager/users/', views.ManagersListView.as_view(), name="get_managers"),
    path('groups/manager/users/<str:userId>/', views.ManagerRemoveView.as_view(), name="remove_manager"),
    path('groups/delivery-crew/users/', views.DeliveryCrewListView.as_view(), name="get_delivery_crew"),
    path('groups/delivery-crew/users/<str:userId>/', views.DeliveryCrewRemoveView.as_view(), name="remove_delivery_crew"),
    
    # Rutas para carrito
    path('cart/menu-items/', views.CartView.as_view(), name="view_cart"),
    path('cart/menu-items/<int:pk>/', views.CartItemDetailView.as_view(), name="cart_item_detail"),
    path('cart/menu-items/add/', views.CartAddView.as_view(), name="add_to_cart"),
    path('cart/menu-items/clear/', views.CartClearView.as_view(), name="clear_cart"),
    
    # Rutas para pedidos
    path('orders/', views.OrdersView.as_view(), name="view_orders"),
    path('orders/create/', views.OrderCreateView.as_view(), name="create_order"),
    path('orders/<int:pk>/', views.OrderItemsView.as_view(), name="get_order_items"),
    path('orders/all/', views.OrdersAllView.as_view(), name="view_all_orders"),
    path('orders/<int:pk>/update/', views.OrderUpdateView.as_view(), name="update_order"),
    path('orders/<int:pk>/delete/', views.OrderDeleteView.as_view(), name="delete_order"),
    path('orders/delivery/', views.DeliveryOrdersView.as_view(), name="view_delivery_orders"),
    path('orders/<int:pk>/status/', views.DeliveryOrderStatusUpdateView.as_view(), name="update_order_status_delivery"),
]