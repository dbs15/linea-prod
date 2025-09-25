from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ==================== PÁGINAS PRINCIPALES ====================
    # Página principal
    path('', views.HomeView.as_view(), name='home'),

    # Autenticación
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Estados especiales
    path('suspended/', views.SuspendedView.as_view(), name='suspended'),

    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # ==================== GESTIÓN DE EMPRESAS (SUPER ADMIN) ====================
    path('crear-empresa/', views.CrearEmpresaView.as_view(), name='crear_empresa'),

    # ==================== MÓDULO DE REGISTRO ====================
    # Lista de pedidos con filtros
    path('pedidos/', views.PedidoListView.as_view(), name='pedido_list'),
    # Crear pedido
    path('pedidos/crear/', views.PedidoCreateView.as_view(), name='pedido_create'),

    # ==================== MÓDULO DE TOSTIÓN ====================
    # Lista de pedidos para tostión
    path('tostion/', views.TostionListView.as_view(), name='tostion_list'),
    # Iniciar tostión (cambiar estado de pedido)
    path('tostion/<int:order_id>/iniciar/', views.StartToastingView.as_view(), name='start_toasting'),
    # Crear proceso de tostión para un pedido específico
    path('tostion/<int:order_id>/crear/', views.TostionCreateView.as_view(), name='tostion_create'),

    # ==================== MÓDULO DE PRODUCCIÓN ====================
    # Lista de pedidos para producción
    path('produccion/', views.ProduccionListView.as_view(), name='produccion_list'),
    # Crear proceso de producción para un pedido específico
    path('produccion/<int:order_id>/crear/', views.ProduccionCreateView.as_view(), name='produccion_create'),

    # ==================== MÓDULO DE FACTURACIÓN ====================
    # Lista de pedidos para facturar
    path('facturacion/', views.FacturacionListView.as_view(), name='facturacion_list'),
    # Crear factura para un pedido específico
    path('facturacion/<int:order_id>/crear/', views.FacturacionCreateView.as_view(), name='facturacion_create'),

    # ==================== GESTIÓN DE CLIENTES ====================
    # Lista de clientes con filtros
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    # Crear cliente
    path('clientes/crear/', views.ClienteCreateView.as_view(), name='cliente_create'),
    # Editar cliente
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),

    # ==================== GESTIÓN DE PEDIDOS (LEGACY) ====================
    # Vistas funcionales (mantener compatibilidad)
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/update/', views.order_update, name='order_update'),

    # ==================== REPORTES ====================
    path('reportes/', views.reports, name='reports'),

    # ==================== ENDPOINTS AJAX ====================
    # Toggle de estado de empresas (super admin)
    path('ajax/toggle-company-status/', views.toggle_company_status, name='toggle_company_status'),

    # Detalle de pedido (modal AJAX)
    path('ajax/pedido/<int:pk>/detalle/', views.pedido_detalle_ajax, name='pedido_detalle_ajax'),

    # Búsqueda de clientes (autocompletado)
    path('ajax/clientes/buscar/', views.cliente_buscar_ajax, name='cliente_buscar_ajax'),
]