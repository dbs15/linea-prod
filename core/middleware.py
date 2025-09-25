import logging
from django.http import HttpResponseForbidden
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.apps import apps
from .models import ActivityLog

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Middleware para verificar estado de empresa y usuario en sistema multi-tenant.
    Filtra datos por empresa, registra actividad y obtiene IP del cliente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obtener IP del cliente
        ip_address = self.get_client_ip(request)

        # Verificar si el usuario está autenticado
        # Asegurarse de que el request tenga el atributo user
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user

            # Verificar estado del usuario
            if not user.is_active:
                logout(request)
                messages.error(request, 'Tu cuenta ha sido desactivada.')
                return redirect('core:login')

            # Verificar empresa del usuario
            if hasattr(user, 'company') and user.company:
                company = user.company

                # Verificar estado de la empresa
                if not company.is_active:
                    logout(request)
                    messages.error(request, 'La empresa ha sido suspendida. Contacta al administrador.')
                    return redirect('core:login')

                # Establecer empresa en el request para filtrado automático
                request.company = company

                # Registrar actividad de navegación (solo para URLs importantes)
                if self.should_log_activity(request):
                    self.log_activity(request, user, company, ip_address)

            else:
                # Usuario sin empresa asignada
                if not user.is_superuser:
                    logout(request)
                    messages.error(request, 'No tienes una empresa asignada.')
                    return redirect('core:login')

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """
        Obtener la IP real del cliente considerando proxies.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def should_log_activity(self, request):
        """
        Determinar si la actividad debe ser registrada.
        Solo registrar actividades importantes, no cada petición.
        """
        # No registrar para archivos estáticos, admin media, etc.
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return False

        # No registrar para AJAX requests menores
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return False

        # Registrar para acciones importantes
        important_actions = [
            '/admin/',  # Admin
            '/login/',  # Login
            '/logout/',  # Logout
            '/orders/',  # Pedidos
            '/clients/',  # Clientes
            '/reports/',  # Reportes
        ]

        return any(request.path.startswith(action) for action in important_actions)

    def log_activity(self, request, user, company, ip_address):
        """
        Registrar actividad del usuario.
        """
        try:
            action = self.get_action_from_request(request)

            ActivityLog.objects.create(
                user=user,
                company=company,
                action=action,
                description=f'Acceso a {request.path}',
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
        except Exception as e:
            logger.error(f'Error logging activity: {e}')

    def get_action_from_request(self, request):
        """
        Determinar el tipo de acción basado en la URL y método.
        """
        path = request.path

        if path.startswith('/admin/'):
            if request.method == 'POST':
                return 'update' if 'change' in path else 'create'
            return 'view'

        if path == '/login/':
            return 'login'
        if path == '/logout/':
            return 'logout'

        if path.startswith('/orders/'):
            if request.method == 'POST':
                return 'create' if 'create' in path else 'update'
            return 'view'

        if path.startswith('/clients/'):
            if request.method == 'POST':
                return 'create' if 'create' in path else 'update'
            return 'view'

        return 'view'  # Default action


class CompanyFilterMiddleware:
    """
    Middleware para filtrar automáticamente las consultas por empresa.
    Aplica filtro de empresa a todos los modelos que lo requieran.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si el usuario tiene empresa asignada, filtrar consultas
        if hasattr(request, 'company'):
            # Monkey patch el manager por defecto para incluir filtro de empresa
            from django.db import models
            from .models import Company

            # Guardar el manager original
            original_manager = None

            # Aplicar filtro a modelos que tienen campo company
            models_with_company = [Company]  # Lista de modelos que NO filtrar

            for model in apps.get_app_config('core').get_models():
                if hasattr(model, 'company') and model not in models_with_company:
                    # Solo filtrar si el modelo tiene campo company
                    if hasattr(model._meta, 'get_field'):
                        try:
                            field = model._meta.get_field('company')
                            if field and hasattr(request, 'user') and not request.user.is_superuser:
                                # Aplicar filtro de empresa al queryset por defecto
                                original_manager = model.objects
                                model.objects = CompanyFilteredManager(request.company, original_manager)
                        except:
                            pass

        response = self.get_response(request)

        # Restaurar managers originales
        if hasattr(request, 'company'):
            for model in apps.get_app_config('core').get_models():
                if hasattr(model, 'objects') and isinstance(model.objects, CompanyFilteredManager):
                    model.objects = model.objects.original_manager

        return response


class CompanyFilteredManager:
    """
    Manager personalizado que filtra automáticamente por empresa.
    """

    def __init__(self, company, original_manager):
        self.company = company
        self.original_manager = original_manager

    def get_queryset(self):
        # Usar el queryset del manager original y filtrar por empresa
        queryset = self.original_manager.get_queryset()
        if hasattr(self.original_manager.model, 'company'):
            return queryset.filter(company=self.company)
        return queryset

    def __getattr__(self, name):
        # Delegar otros métodos al manager original
        return getattr(self.original_manager, name)