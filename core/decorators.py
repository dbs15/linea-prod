from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def rol_requerido(*roles_permitidos):
    """
    Decorador para verificar que el usuario tenga uno de los roles permitidos.

    Args:
        *roles_permitidos: Lista de roles que pueden acceder a la vista.
                           Ej: 'aux_registro', 'admin_company', 'super_admin'

    Uso:
        @rol_requerido('aux_registro', 'admin_company')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Verificar si el usuario está autenticado
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                messages.warning(request, 'Debe iniciar sesión para acceder a esta página.')
                return redirect('core:login')

            # Verificar si el usuario tiene empresa asignada (excepto super_admin)
            if not hasattr(request.user, 'company') or not request.user.company:
                if request.user.role != 'super_admin':
                    messages.error(request, 'Su cuenta no está asociada a una empresa. Contacte al administrador.')
                    return redirect('core:dashboard')

            # Verificar si la empresa está activa
            if hasattr(request.user, 'company') and request.user.company and not request.user.company.is_active:
                messages.error(request, 'Su empresa está suspendida. Contacte al administrador.')
                return redirect('core:dashboard')

            # Verificar rol del usuario
            if request.user.role not in roles_permitidos:
                messages.error(request, 'No tiene permisos para acceder a esta sección.')
                return redirect('core:dashboard')

            # Ejecutar la vista original
            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator


def empresa_activa_requerida(view_func):
    """
    Decorador para verificar que la empresa del usuario esté activa.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            messages.warning(request, 'Debe iniciar sesión para acceder a esta página.')
            return redirect('core:login')

        if hasattr(request.user, 'company') and request.user.company and not request.user.company.is_active:
            messages.error(request, 'Su empresa está suspendida. Contacte al administrador.')
            return redirect('core:dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def super_admin_requerido(view_func):
    """
    Decorador específico para vistas que requieren super administrador.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            messages.warning(request, 'Debe iniciar sesión para acceder a esta página.')
            return redirect('core:login')

        if request.user.role != 'super_admin':
            messages.error(request, 'Esta sección requiere permisos de super administrador.')
            return redirect('core:dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view