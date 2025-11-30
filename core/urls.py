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
    # Lista de maquilas con filtros
    path('maquilas/', views.MaquilaListView.as_view(), name='maquila_list'),
    # Crear maquila
    path('maquilas/crear/', views.MaquilaCreateView.as_view(), name='maquila_create'),
    # Editar maquila
    path('maquilas/<int:pk>/editar/', views.MaquilaUpdateView.as_view(), name='maquila_update'),

    # ==================== MÓDULO DE TOSTIÓN ====================
    # Lista de maquilas para tostión
    path('tostion/', views.TostionListView.as_view(), name='tostion_list'),
    # Iniciar tostión (cambiar estado de maquila)
    path('tostion/<int:order_id>/iniciar/', views.StartToastingView.as_view(), name='start_toasting'),
    # Crear proceso de tostión para una maquila específica
    path('tostion/<int:order_id>/crear/', views.TostionCreateView.as_view(), name='tostion_create'),

    # ==================== MÓDULO DE PRODUCCIÓN ====================
    # Lista de maquilas para producción
    path('produccion/', views.ProduccionListView.as_view(), name='produccion_list'),
    # Crear proceso de producción para una maquila específica
    path('produccion/<int:order_id>/crear/', views.ProduccionCreateView.as_view(), name='produccion_create'),

    # ==================== MÓDULO DE FACTURACIÓN ====================
    # Lista de maquilas para facturar
    path('facturacion/', views.FacturacionListView.as_view(), name='facturacion_list'),
    # Crear factura para una maquila específica
    path('facturacion/<int:order_id>/crear/', views.FacturacionCreateView.as_view(), name='facturacion_create'),

    # ==================== GESTIÓN DE CLIENTES ====================
    # Lista de clientes con filtros
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    # Crear cliente
    path('clientes/crear/', views.ClienteCreateView.as_view(), name='cliente_create'),
    # Editar cliente
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),

    # ==================== GESTIÓN DE MAQUILAS (LEGACY) ====================
    # Vistas funcionales (mantener compatibilidad)
    path('maquilas-legacy/', views.maquila_list_legacy, name='maquila_list_legacy'),
    path('maquilas-legacy/create/', views.maquila_create_legacy, name='maquila_create_legacy'),
    path('maquilas-legacy/<int:pk>/', views.maquila_detail_legacy, name='maquila_detail_legacy'),
    path('maquilas-legacy/<int:pk>/update/', views.maquila_update_legacy, name='maquila_update_legacy'),

    # ==================== REPORTES ====================
    path('reportes/', views.reports, name='reports'),

    # ==================== ENDPOINTS AJAX ====================
    # Toggle de estado de empresas (super admin)
    path('ajax/toggle-company-status/', views.toggle_company_status, name='toggle_company_status'),

    # Detalle de maquila (modal AJAX)
    path('ajax/maquila/<int:pk>/detalle/', views.maquila_detalle_ajax, name='maquila_detalle_ajax'),

    # Búsqueda de clientes (autocompletado)
    path('ajax/clientes/buscar/', views.cliente_buscar_ajax, name='cliente_buscar_ajax'),
]