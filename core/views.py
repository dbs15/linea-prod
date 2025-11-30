from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, FormView, ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from .models import Order, Client, Invoice, Company, ActivityLog, ToastingProcess, ProductionProcess
from .forms import (
    LoginForm, CompanyForm, UserForm, ClienteForm, MaquilaForm,
    ProcesoTostionForm, ProcesoProduccionForm, FacturaForm
)
from .decorators import rol_requerido, super_admin_requerido


class HomeView(TemplateView):
    """
    Vista de inicio con landing page para no autenticados y preview para autenticados.
    """
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            user = self.request.user
            # Preview del dashboard
            context.update({
                'user_role': user.get_role_display(),
                'company_name': user.company.name if user.company else 'Sin empresa',
                'total_maquilas': Order.objects.filter(company=user.company).count() if user.company else 0,
                'active_maquilas': Order.objects.filter(
                    company=user.company,
                    state__in=['registered', 'in_toasting', 'toasting_complete', 'in_production']
                ).count() if user.company else 0,
                'total_clients': Client.objects.filter(company=user.company).count() if user.company else 0,
            })
        return context


class LoginView(FormView):
    """
    Vista de login personalizada con validaciones de estado.
    """
    template_name = 'core/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('core:dashboard')

    def form_valid(self, form):
        """Validar login con checks adicionales."""
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        user = authenticate(self.request, username=username, password=password)

        if user:
            # Verificar estado del usuario
            if not user.is_active:
                messages.error(self.request, 'Tu cuenta ha sido desactivada.')
                return self.form_invalid(form)

            # Verificar empresa del usuario
            if hasattr(user, 'company') and user.company:
                if not user.company.is_active:
                    messages.error(self.request, 'La empresa ha sido suspendida. Contacta al administrador.')
                    return self.form_invalid(form)

            # Login exitoso
            login(self.request, user)

            # Registrar último acceso
            user.log_access(self.request.META.get('REMOTE_ADDR'))

            # Redirección inteligente según rol
            next_url = self.request.GET.get('next')
            if next_url:
                return redirect(next_url)

            # Redirección por rol
            if user.is_superuser or user.role == 'super_admin':
                return redirect('admin:index')
            elif user.role in ['admin_company', 'aux_registro', 'aux_tostion', 'aux_produccion', 'aux_facturacion']:
                return redirect('core:dashboard')

            return redirect('core:dashboard')

        messages.error(self.request, 'Credenciales inválidas.')
        return self.form_invalid(form)


@login_required
def logout_view(request):
    """
    Vista de logout con registro de actividad.
    """
    if request.user.is_authenticated:
        # Registrar logout en actividad
        ActivityLog.objects.create(
            user=request.user,
            company=getattr(request.user, 'company', None),
            action='logout',
            description='Cierre de sesión',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('core:home')


class SuspendedView(TemplateView):
    """
    Vista para empresas suspendidas.
    """
    template_name = 'core/suspended.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'company'):
            context['company'] = self.request.user.company
            context['suspension_reason'] = self.request.user.company.suspension_reason
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard con contenido diferenciado por rol.
    """
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Información básica del usuario
        context.update({
            'user_role': user.get_role_display(),
            'company': user.company,
            'is_admin': user.can_manage_company(),
            'is_super_admin': user.is_superuser or user.role == 'super_admin',
        })

        # Dashboard para Super Admin
        if user.is_superuser or user.role == 'super_admin':
            context.update(self._get_super_admin_context())
        else:
            # Dashboard para usuarios de empresa
            context.update(self._get_company_user_context(user))

        return context

    def _get_super_admin_context(self):
        """Contexto específico para super admin"""
        from django.db.models import Count, Q
        from django.contrib.auth import get_user_model

        # Métricas principales
        companies = Company.objects.all()
        total_companies = companies.count()
        active_companies = companies.filter(status='active').count()
        suspended_companies = companies.filter(status='suspended').count()
        total_users = get_user_model().objects.count()

        # Actividad reciente
        recent_activity = ActivityLog.objects.select_related('user', 'company').order_by('-timestamp')[:10]

        # Empresas activas y suspendidas para gestión
        active_companies_list = companies.filter(status='active')[:5]
        suspended_companies_list = companies.filter(status='suspended')[:5]

        return {
            'dashboard_type': 'super_admin',
            'dashboard_title': 'Panel de Super Administrador',
            'dashboard_description': 'Gestión global del sistema multi-empresa',

            # Métricas
            'total_companies': total_companies,
            'active_companies': active_companies,
            'suspended_companies': suspended_companies,
            'total_users': get_user_model().objects.count(),

            # Gestión de empresas
            'active_companies_list': active_companies_list,
            'suspended_companies_list': suspended_companies_list,

            # Actividad reciente
            'recent_activity': recent_activity,
        }

    def _get_company_user_context(self, user):
        """Contexto específico para usuarios de empresa"""
        if not user.company:
            return {
                'dashboard_type': 'no_company',
                'dashboard_title': 'Usuario sin Empresa',
                'dashboard_description': 'Contacta al administrador para asignarte a una empresa',
            }

        # Información de la empresa
        company = user.company

        # Módulos disponibles según rol
        modules = self._get_available_modules(user)

        # Actividad reciente de la empresa
        company_activity = ActivityLog.objects.filter(
            company=company
        ).select_related('user').order_by('-timestamp')[:8]

        # Métricas específicas de la empresa
        metrics = self._get_company_metrics(company)

        return {
            'dashboard_type': 'company_user',
            'dashboard_title': f'Panel de {company.name}',
            'dashboard_description': f'Bienvenido, {user.first_name}. Rol: {user.get_role_display()}',
            'company': company,
            'modules': modules,
            'company_activity': company_activity,
            'metrics': metrics,
        }

    def _get_available_modules(self, user):
        """Retorna módulos disponibles según el rol del usuario"""
        base_modules = []

        if user.role in ['aux_registro', 'admin_company', 'super_admin']:
            base_modules.append({
                'name': 'Clientes',
                'icon': 'fas fa-users',
                'description': 'Gestionar clientes del sistema',
                'url': 'core:cliente_list',
                'color': 'green',
                'permissions': ['view_client', 'add_client']
            })

        if user.role in ['aux_registro', 'admin_company', 'super_admin']:
            base_modules.append({
                'name': 'Maquilas',
                'icon': 'fas fa-shopping-cart',
                'description': 'Gestionar maquilas existentes',
                'url': 'core:maquila_list',
                'color': 'blue',
                'permissions': ['view_order', 'add_order', 'view_client', 'add_client']
            })

        if user.role in ['aux_tostion', 'admin_company', 'super_admin']:
            base_modules.append({
                'name': 'Tostión',
                'icon': 'fas fa-fire',
                'description': 'Controlar proceso de tostión',
                'url': 'core:tostion_list',  # Filtrar por estado
                'color': 'orange',
                'permissions': ['view_order', 'change_order']
            })

        if user.role in ['aux_produccion', 'admin_company', 'super_admin']:
            base_modules.append({
                'name': 'Producción',
                'icon': 'fas fa-boxes',
                'description': 'Gestionar empaque y producción',
                'url': 'core:produccion_list',
                'color': 'purple',
                'permissions': ['view_order', 'change_order']
            })

        if user.role in ['aux_facturacion', 'admin_company', 'super_admin']:
            base_modules.append({
                'name': 'Facturación',
                'icon': 'fas fa-file-invoice-dollar',
                'description': 'Generar facturas y controlar pagos',
                'url': 'core:facturacion_list',
                'color': 'green',
                'permissions': ['view_order', 'view_invoice', 'add_invoice']
            })

        if user.role in ['admin_company', 'super_admin']:
            base_modules.append({
                'name': 'Reportes',
                'icon': 'fas fa-chart-bar',
                'description': 'Ver reportes y estadísticas',
                'url': 'core:reports',
                'color': 'teal',
                'permissions': ['view_reports']
            })

        return base_modules

    def _get_company_metrics(self, company):
        """Métricas específicas de la empresa"""
        return {
            'total_maquilas': Order.objects.filter(company=company).count(),
            'active_maquilas': Order.objects.filter(
                company=company,
                state__in=['registered', 'in_toasting', 'toasting_complete', 'in_production']
            ).count(),
            'completed_maquilas': Order.objects.filter(
                company=company,
                state__in=['billed', 'delivered']
            ).count(),
            'total_clients': Client.objects.filter(company=company).count(),
            'pending_invoices': Invoice.objects.filter(
                company=company,
                status='pending'
            ).count(),
            'overdue_invoices': Invoice.objects.filter(
                company=company,
                status='pending',
                due_date__lt=timezone.now().date()
            ).count(),
        }


class CrearEmpresaView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Vista para crear nuevas empresas (solo super admin).
    """
    model = Company
    form_class = CompanyForm
    template_name = 'core/crear_empresa.html'
    success_url = reverse_lazy('core:dashboard')

    def test_func(self):
        """Solo super admin puede crear empresas"""
        return self.request.user.is_superuser or self.request.user.role == 'super_admin'

    def form_valid(self, form):
        # Crear la empresa
        company = form.save()

        # Registrar actividad
        ActivityLog.objects.create(
            user=self.request.user,
            company=company,
            action='company_create',
            description=f'Nueva empresa creada: {company.name}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
        )

        messages.success(self.request, f'Empresa "{company.name}" creada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear la empresa. Verifica los datos.')
        return super().form_invalid(form)


@login_required
@csrf_exempt
def toggle_company_status(request):
    """
    Vista AJAX para toggle de estado de empresas (solo super admin).
    """
    if not request.user.is_superuser and request.user.role != 'super_admin':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        action = request.POST.get('action')  # 'suspend', 'activate', 'cancel'

        try:
            company = Company.objects.get(pk=company_id)

            if action == 'suspend':
                company.suspend("Suspendido por administrador del sistema")
                message = f'Empresa {company.name} suspendida'
            elif action == 'activate':
                company.activate()
                message = f'Empresa {company.name} activada'
            elif action == 'cancel':
                company.cancel("Cancelado por administrador del sistema")
                message = f'Empresa {company.name} cancelada'
            else:
                return JsonResponse({'error': 'Acción inválida'}, status=400)

            # Registrar actividad
            ActivityLog.objects.create(
                user=request.user,
                company=company,
                action=f'company_{action}',
                description=f'Estado de empresa cambiado: {message}',
                ip_address=request.META.get('REMOTE_ADDR'),
            )

            return JsonResponse({
                'success': True,
                'message': message,
                'new_status': company.get_status_display()
            })

        except Company.DoesNotExist:
            return JsonResponse({'error': 'Empresa no encontrada'}, status=404)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# Vistas básicas para compatibilidad (serán reemplazadas por vistas basadas en clases)
@login_required
def client_list(request):
    """Lista de clientes"""
    clients = Client.objects.filter(company=request.user.company)
    return render(request, 'core/client_list.html', {'clients': clients})


@login_required
def client_create(request):
    """Crear cliente"""
    if request.method == 'POST':
        # Lógica para crear cliente
        pass
    return render(request, 'core/client_form.html')


@login_required
def client_detail(request, pk):
    """Detalle de cliente"""
    client = Client.objects.get(pk=pk, company=request.user.company)
    return render(request, 'core/client_detail.html', {'client': client})


@login_required
def maquila_list_legacy(request):
    """Lista de maquilas"""
    maquilas = Order.objects.filter(company=request.user.company)
    return render(request, 'core/maquilas/maquila_list.html', {'maquilas': maquilas})


@login_required
def maquila_create_legacy(request):
    """
    Crear maquila
    """
    if request.method == 'POST':
        # Lógica para crear maquila
        pass
    clients = Client.objects.filter(company=request.user.company)
    return render(request, 'core/maquilas/maquila_create.html', {'clients': clients})


@login_required
def maquila_detail_legacy(request, pk):
    """
    Detalle de maquila
    """
    maquila = Order.objects.get(pk=pk, company=request.user.company)
    return render(request, 'core/maquilas/maquila_create.html', {'maquila': maquila})


@login_required
def maquila_update_legacy(request, pk):
    """
    Actualizar maquila
    """
    maquila = Order.objects.get(pk=pk, company=request.user.company)
    if request.method == 'POST':
        # Lógica para actualizar maquila según estado
        pass
    return render(request, 'core/maquilas/maquila_create.html', {'maquila': maquila})


@login_required
def reports(request):
    """
    Reportes
    """
    user = request.user
    company = user.company

    # Verificar que el usuario tenga una empresa asignada
    if not company:
        messages.error(request, 'No tienes una empresa asignada. Contacta al administrador.')
        return redirect('core:dashboard')

    # Filtros de fecha
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    report_type = request.GET.get('report_type', 'general')

    # Base queryset para maquilas
    maquilas_queryset = Order.objects.filter(company=company)

    # Aplicar filtros de fecha si existen
    if date_from:
        maquilas_queryset = maquilas_queryset.filter(created_at__date__gte=date_from)
    if date_to:
        maquilas_queryset = maquilas_queryset.filter(created_at__date__lte=date_to)

    # Métricas principales
    total_maquilas = maquilas_queryset.count()
    total_revenue = maquilas_queryset.aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    total_clients = Client.objects.filter(company=company).count()

    # Calcular tiempo promedio de procesamiento (simplificado)
    completed_maquilas = maquilas_queryset.filter(state__in=['billed', 'delivered'])
    avg_processing_time = 0
    if completed_maquilas.exists():
        total_days = sum(
            (maquila.updated_at.date() - maquila.created_at.date()).days
            for maquila in completed_maquilas
        )
        avg_processing_time = round(total_days / completed_maquilas.count(), 1)

    # Maquilas recientes
    recent_maquilas = maquilas_queryset.order_by('-created_at')[:10]

    # Top clientes (simplificado)
    top_clients = []
    clients_with_maquilas = Client.objects.filter(
        company=company,
        orders__isnull=False
    ).annotate(
        orders_count=Count('orders'),
        total_amount=Sum('orders__total_amount')
    ).order_by('-total_amount')[:5]

    for client in clients_with_maquilas:
        top_clients.append({
            'name': client.full_name,
            'orders_count': client.orders_count,
            'total_amount': str(client.total_amount)
        })

    # Top productos (por tipo de café)
    top_products = []
    coffee_types = maquilas_queryset.values('coffee_type').annotate(
        quantity=Sum('quantity_kg'),
        revenue=Sum('total_amount'),
        orders_count=Count('id')
    ).order_by('-revenue')[:5]

    for coffee in coffee_types:
        top_products.append({
            'name': dict(Order.COFFEE_TYPE_CHOICES).get(coffee['coffee_type'], coffee['coffee_type']),
            'quantity': str(coffee['quantity']),
            'revenue': str(coffee['revenue'])
        })

    # Rendimiento mensual (últimos 6 meses)
    monthly_performance = []
    from django.db.models.functions import TruncMonth
    from django.utils import timezone
    import datetime

    six_months_ago = timezone.now() - datetime.timedelta(days=180)
    monthly_data = maquilas_queryset.filter(
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        maquilas=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('month')

    for data in monthly_data:
        monthly_performance.append({
            'month': data['month'].strftime('%B %Y'),
            'maquilas': data['maquilas'],
            'revenue': str(data['revenue'] or 0)
        })

    context = {
        'company': company,
        'total_maquilas': total_maquilas,
        'total_revenue': f"{total_revenue:.2f}",
        'total_clients': total_clients,
        'avg_processing_time': avg_processing_time,
        'recent_maquilas': recent_maquilas,
        'top_clients': top_clients,
        'top_products': top_products,
        'monthly_performance': monthly_performance,
        'date_from': date_from,
        'date_to': date_to,
        'report_type': report_type,
    }

    return render(request, 'core/reports.html', context)


# ==================== MÓDULO DE REGISTRO ====================

class MaquilaListView(LoginRequiredMixin, ListView):
    """
    Lista de maquilas con filtros avanzados y paginación.
    Acceso: aux_registro, admin_company, super_admin
    """
    model = Order
    template_name = 'core/maquilas/maquila_list.html'
    context_object_name = 'maquilas'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.filter(company=user.company)

        # Filtros
        status = self.request.GET.get('status')
        client = self.request.GET.get('client')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(state=status)
        if client:
            queryset = queryset.filter(client__id=client)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Filtros disponibles
        context['status_choices'] = Order.STATE_CHOICES
        context['clients'] = Client.objects.filter(company=user.company).order_by('first_name', 'last_name')

        # Estadísticas rápidas
        queryset = self.get_queryset()
        context['total_maquilas'] = queryset.count()
        context['pending_maquilas'] = queryset.filter(
            state__in=['registered', 'in_toasting', 'toasting_complete', 'in_production']
        ).count()
        context['completed_maquilas'] = queryset.filter(
            state__in=['billed', 'delivered']
        ).count()

        return context

    @method_decorator(rol_requerido('aux_registro', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class MaquilaCreateView(LoginRequiredMixin, CreateView):
    """
    Crear maquila con opción de cliente existente o nuevo.
    Usa transacción atómica para garantizar integridad.
    """
    model = Order
    form_class = MaquilaForm
    template_name = 'core/maquilas/maquila_create.html'
    success_url = reverse_lazy('core:maquila_list')

    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario tenga una empresa asignada
        if not hasattr(request.user, 'company') or not request.user.company:
            messages.error(request, 'No tienes una empresa asignada. Contacta al administrador.')
            return redirect('core:dashboard')

        # Verificar que haya clientes disponibles para la empresa
        available_clients = Client.objects.filter(
            company=request.user.company,
            is_active=True
        )
        if not available_clients.exists():
            messages.warning(
                request,
                'No hay clientes registrados para tu empresa. Debes crear al menos un cliente antes de crear maquilas.'
            )
            return redirect('core:cliente_list')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            # El formulario ya maneja la creación del cliente si es necesario
            maquila = form.save()

            # Registrar actividad
            ActivityLog.objects.create(
                user=self.request.user,
                company=self.request.user.company,
                action='maquila_create',
                description=f'Maquila {maquila.order_number} creada para {maquila.client.full_name}',
                ip_address=self.request.META.get('REMOTE_ADDR'),
                related_order=maquila
            )

            messages.success(
                self.request,
                f'Maquila {maquila.order_number} creada exitosamente para {maquila.client.full_name}.'
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear la maquila. Verifica los datos.')
        return super().form_invalid(form)

    @method_decorator(rol_requerido('aux_registro', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class MaquilaUpdateView(LoginRequiredMixin, UpdateView):
    """
    Actualizar una maquila existente.
    Acceso: aux_registro, admin_company, super_admin
    """
    model = Order
    form_class = MaquilaForm
    template_name = 'core/maquilas/maquila_update.html' # Se creará este template
    success_url = reverse_lazy('core:maquila_list')
    context_object_name = 'maquila'

    def get_queryset(self):
        """Solo permitir editar maquilas de la empresa del usuario"""
        return Order.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        maquila = form.save()

        ActivityLog.objects.create(
            user=self.request.user,
            company=self.request.user.company,
            action='maquila_update',
            description=f'Maquila {maquila.order_number} actualizada para {maquila.client.full_name}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            related_order=maquila
        )

        messages.success(
            self.request,
            f'Maquila {maquila.order_number} actualizada exitosamente para {maquila.client.full_name}.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al actualizar la maquila. Verifica los datos.')
        return super().form_invalid(form)

    @method_decorator(rol_requerido('aux_registro', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# ==================== MÓDULO DE TOSTIÓN ====================

class TostionListView(LoginRequiredMixin, ListView):
    """
    Lista de maquilas disponibles para tostión.
    Muestra maquilas registradas (para iniciar tostión) y en tostión (para procesar).
    Acceso: aux_tostion, admin_company, super_admin
    """
    model = Order
    template_name = 'core/tostion/lista.html'
    context_object_name = 'maquilas'
    paginate_by = 15

    def get_queryset(self):
        return Order.objects.filter(
            company=self.request.user.company,
            state__in=['registered', 'in_toasting']
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Estadísticas de tostión
        maquilas = self.get_queryset()
        in_toasting_maquilas = maquilas.filter(state='in_toasting')
        registered_maquilas = maquilas.filter(state='registered')

        context['total_pending'] = maquilas.count()
        context['in_toasting_count'] = in_toasting_maquilas.count()
        context['registered_count'] = registered_maquilas.count()
        context['with_process'] = in_toasting_maquilas.filter(toasting_process__isnull=False).count()
        context['without_process'] = in_toasting_maquilas.filter(toasting_process__isnull=True).count()

        # Separar listas para mostrar en secciones diferentes
        context['registered_maquilas'] = registered_maquilas
        context['toasting_maquilas'] = in_toasting_maquilas

        return context

    @method_decorator(rol_requerido('aux_tostion', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class StartToastingView(LoginRequiredMixin, View):
    """
    Vista para iniciar el proceso de tostión cambiando el estado de la maquila.
    Acceso: aux_tostion, admin_company, super_admin
    """

    @method_decorator(rol_requerido('aux_tostion', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, order_id):
        try:
            maquila = Order.objects.get(
                id=order_id,
                company=request.user.company,
                state='registered'
            )

            # Cambiar estado de la maquila a 'in_toasting'
            maquila.start_toasting()
            maquila.toasted_by = request.user
            maquila.save()

            # Registrar actividad
            ActivityLog.objects.create(
                user=request.user,
                company=request.user.company,
                action='toasting_start',
                description=f'Inicio de tostión para maquila {maquila.order_number}',
                ip_address=request.META.get('REMOTE_ADDR'),
                related_order=maquila
            )

            messages.success(
                request,
                f'Proceso de tostión iniciado para maquila {maquila.order_number}.'
            )

            # Redirigir al proceso paso a paso
            return redirect('core:tostion_create', order_id=maquila.id)

        except Order.DoesNotExist:
            messages.error(request, 'Maquila no encontrada o no disponible para iniciar tostión.')
            return redirect('core:tostion_list')


class TostionCreateView(LoginRequiredMixin, CreateView):
    """
    Proceso de tostión paso a paso para una maquila.
    """
    model = ToastingProcess
    form_class = ProcesoTostionForm
    template_name = 'core/tostion/crear.html'

    def get(self, request, *args, **kwargs):
        # Verificar que la maquila existe y está en estado correcto
        order_id = self.kwargs.get('order_id')
        try:
            maquila = Order.objects.get(
                id=order_id,
                company=request.user.company,
                state='in_toasting'
            )
        except Order.DoesNotExist:
            messages.error(request, 'Maquila no encontrada o no disponible para tostión.')
            return redirect('core:tostion_list')

        self.order = maquila
        self.object = maquila # Asegurar que self.object también se establezca
        
        # Obtener o crear proceso de tostión
        toasting_process, created = ToastingProcess.objects.get_or_create(
            order=maquila,
            defaults={
                'processed_by': request.user,
                'received_quantity_kg': maquila.quantity_kg
            }
        )
        self.toasting_process = toasting_process
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Verificar que la maquila existe y está en estado correcto
        order_id = self.kwargs.get('order_id')
        try:
            maquila = Order.objects.get(
                id=order_id,
                company=request.user.company,
                state='in_toasting'
            )
        except Order.DoesNotExist:
            messages.error(request, 'Maquila no encontrada o no disponible para tostión.')
            return redirect('core:tostion_list')

        self.order = maquila
        self.object = maquila # Asegurar que self.object también se establezca
        
        # Obtener proceso de tostión
        toasting_process, created = ToastingProcess.objects.get_or_create(
            order=maquila,
            defaults={
                'processed_by': request.user,
                'received_quantity_kg': maquila.quantity_kg
            }
        )
        self.toasting_process = toasting_process
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # El step se determina en get_context_data o se pasa desde la URL
        current_step = getattr(self, 'current_step', 'reception')
        kwargs['step'] = current_step
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['maquila'] = self.order
        context['toasting_process'] = self.toasting_process
        context['object'] = self.order # Añadir como 'object' también, por si acaso
        context['order'] = self.order # Añadir como 'order' también, por si acaso

        # Determinar paso actual y progreso
        # Primero intentar desde GET (para navegación por URL), luego desde POST (para navegación por formulario)
        current_step = self.request.GET.get('step', 'reception')
        if self.request.method == 'POST':
            # Si es POST, usar el valor del formulario si existe
            post_step = self.request.POST.get('current_step')
            if post_step:
                current_step = post_step

        # Validar que el paso sea válido
        steps = ['reception', 'setup', 'monitoring', 'completion']
        if current_step not in steps:
            current_step = 'reception'  # Paso por defecto si es inválido

        self.current_step = current_step  # Guardar para usar en get_form_kwargs
        current_step_number = steps.index(current_step) + 1
        progress_percentage = (current_step_number - 1) * 25

        context.update({
            'current_step': current_step,
            'current_step_number': current_step_number,
            'progress_percentage': progress_percentage,
            'steps': steps,  # Agregar lista de pasos para debugging
        })

        return context

    def form_valid(self, form):
        current_step = self.request.POST.get('current_step', 'reception')
        steps = ['reception', 'setup', 'monitoring', 'completion']

        with transaction.atomic():
            # Actualizar proceso según el paso
            if current_step == 'reception':
                self.toasting_process.received_quantity_kg = form.cleaned_data['received_quantity_kg']
                self.toasting_process.process_status = 'received'
                self.toasting_process.save()

            elif current_step == 'setup':
                self.toasting_process.toasting_equipment = form.cleaned_data['toasting_equipment']
                self.toasting_process.equipment_capacity_kg = dict(ToastingProcess.TOASTING_EQUIPMENT_CHOICES)[form.cleaned_data['toasting_equipment']]
                self.toasting_process.initial_temperature_celsius = form.cleaned_data['initial_temperature_celsius']
                self.toasting_process.target_temperature_celsius = form.cleaned_data['target_temperature_celsius']
                self.toasting_process.estimated_time_minutes = form.cleaned_data['estimated_time_minutes']
                self.toasting_process.roast_type = form.cleaned_data['roast_type']
                self.toasting_process.start_process()
                self.toasting_process.save()

            elif current_step == 'monitoring':
                # Actualizar datos de monitoreo
                if form.cleaned_data.get('current_temperature_celsius'):
                    self.toasting_process.update_monitoring(
                        temperature=form.cleaned_data['current_temperature_celsius'],
                        time_elapsed=self.toasting_process.current_time_elapsed_minutes + 1,  # Simplificado
                        humidity=form.cleaned_data.get('current_humidity_percentage')
                    )

                # Agregar muestras de calidad si se proporcionan
                # (Aquí se podría implementar lógica para guardar muestras)

            elif current_step == 'completion':
                # Completar el proceso
                self.toasting_process.complete_process(
                    processed_quantity=form.cleaned_data['processed_quantity_kg'],
                    final_quality=form.cleaned_data['final_grain_quality'],
                    notes=form.cleaned_data.get('final_quality_notes', '')
                )

                # Cambiar estado de la maquila
                self.order.complete_toasting()
                self.order.toasted_by = self.request.user
                self.order.save()

                # Registrar actividad
                ActivityLog.objects.create(
                    user=self.request.user,
                    company=self.request.user.company,
                    action='toasting_complete',
                    description=f'Proceso de tostión completado para maquila {self.order.order_number}',
                    ip_address=self.request.META.get('REMOTE_ADDR'),
                    related_order=self.order
                )

                messages.success(
                    self.request,
                    f'Proceso de tostión completado para maquila {self.order.order_number}.'
                )

                return redirect('core:tostion_list')

            # Determinar siguiente paso y redirigir
            current_index = steps.index(current_step)
            if current_index < len(steps) - 1:
                next_step = steps[current_index + 1]
                # Redirigir al siguiente paso con el parámetro step en la URL
                return redirect(f"{self.request.path_info}?step={next_step}")
            else:
                return redirect('core:tostion_list')

    @method_decorator(rol_requerido('aux_tostion', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# ==================== MÓDULO DE PRODUCCIÓN ====================

class ProduccionListView(LoginRequiredMixin, ListView):
    """
    Lista de maquilas listos para producción.
    Acceso: aux_produccion, admin_company, super_admin
    """
    model = Order
    template_name = 'core/produccion/lista.html'
    context_object_name = 'maquilas'
    paginate_by = 15

    def get_queryset(self):
        return Order.objects.filter(
            company=self.request.user.company,
            state='in_production'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Estadísticas de producción
        maquilas = self.get_queryset()
        context['total_pending'] = maquilas.count()
        context['with_process'] = maquilas.filter(production_process__isnull=False).count()
        context['without_process'] = maquilas.filter(production_process__isnull=True).count()

        return context

    @method_decorator(rol_requerido('aux_produccion', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ProduccionCreateView(LoginRequiredMixin, CreateView):
    """
    Crear proceso de producción para una maquila.
    """
    model = ProductionProcess
    form_class = ProcesoProduccionForm
    template_name = 'core/produccion/crear.html'

    def get(self, request, *args, **kwargs):
        # Verificar que la maquila existe y está en estado correcto
        order_id = self.kwargs.get('order_id')
        try:
            maquila = Order.objects.get(
                id=order_id,
                company=request.user.company,
                state='in_production'
            )
            # Verificar que no tenga proceso de producción ya creado
            if hasattr(maquila, 'production_process'):
                messages.error(request, 'Esta maquila ya tiene un proceso de producción iniciado.')
                return redirect('core:produccion_list')
        except Order.DoesNotExist:
            messages.error(request, 'Maquila no encontrada o no disponible para producción.')
            return redirect('core:produccion_list')

        self.order = maquila
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Verificar que la maquila existe y está en estado correcto
        order_id = self.kwargs.get('order_id')
        try:
            maquila = Order.objects.get(
                id=order_id,
                company=request.user.company,
                state='in_production'
            )
            # Verificar que no tenga proceso de producción ya creado
            if hasattr(maquila, 'production_process'):
                messages.error(request, 'Esta maquila ya tiene un proceso de producción iniciado.')
                return redirect('core:produccion_list')
        except Order.DoesNotExist:
            messages.error(request, 'Maquila no encontrada o no disponible para producción.')
            return redirect('core:produccion_list')

        self.order = maquila
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['maquila'] = self.order
        return context

    def form_valid(self, form):
        production_process = form.save(commit=False)
        production_process.order = self.order
        production_process.processed_by = self.request.user
        production_process.save()

        # Cambiar estado de la maquila
        self.order.complete_production()
        self.order.produced_by = self.request.user
        self.order.save()

        # Registrar actividad
        ActivityLog.objects.create(
            user=self.request.user,
            company=self.request.user.company,
            action='production_complete',
            description=f'Proceso de producción completado para maquila {self.order.order_number}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            related_order=self.order
        )

        messages.success(
            self.request,
            f'Proceso de producción completado para maquila {self.order.order_number}.'
        )

        return redirect('core:produccion_list')

    @method_decorator(rol_requerido('aux_produccion', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# ==================== MÓDULO DE FACTURACIÓN ====================

class FacturacionListView(LoginRequiredMixin, ListView):
    """
    Lista de maquilas listos para facturar.
    Acceso: aux_facturacion, admin_company, super_admin
    """
    model = Order
    template_name = 'core/facturacion/lista.html'
    context_object_name = 'maquilas'
    paginate_by = 15

    def get_queryset(self):
        return Order.objects.filter(
            company=self.request.user.company,
            state='ready_for_billing'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Estadísticas de facturación
        maquilas = self.get_queryset()
        context['total_pending'] = maquilas.count()
        context['with_invoice'] = maquilas.filter(invoice__isnull=False).count()
        context['without_invoice'] = maquilas.filter(invoice__isnull=True).count()

        # Facturas pendientes de pago
        context['pending_invoices'] = Invoice.objects.filter(
            company=self.request.user.company,
            status='pending'
        ).order_by('due_date')[:10]

        return context

    @method_decorator(rol_requerido('aux_facturacion', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class FacturacionCreateView(LoginRequiredMixin, CreateView):
    """
    Crear factura para una maquila.
    """
    model = Invoice
    form_class = FacturaForm
    template_name = 'core/facturacion/crear.html'

    def get(self, request, *args, **kwargs):
        # Verificar que la maquila existe y está en estado correcto
        order_id = self.kwargs.get('order_id')
        try:
            maquila = Order.objects.get(
                id=order_id,
                company=request.user.company,
                state='ready_for_billing'
            )
            # Verificar que no tenga factura ya creada
            if hasattr(maquila, 'invoice'):
                messages.error(request, 'Esta maquila ya tiene una factura creada.')
                return redirect('core:facturacion_list')
        except Order.DoesNotExist:
            messages.error(request, 'Maquila no encontrada o no disponible para facturación.')
            return redirect('core:facturacion_list')

        self.order = maquila
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Verificar que la maquila existe y está en estado correcto
        order_id = self.kwargs.get('order_id')
        try:
            maquila = Order.objects.get(
                id=order_id,
                company=request.user.company,
                state='ready_for_billing'
            )
            # Verificar que no tenga factura ya creada
            if hasattr(maquila, 'invoice'):
                messages.error(request, 'Esta maquila ya tiene una factura creada.')
                return redirect('core:facturacion_list')
        except Order.DoesNotExist:
            messages.error(request, 'Maquila no encontrada o no disponible para facturación.')
            return redirect('core:facturacion_list')

        self.order = maquila
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['maquila'] = self.order
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Poblar el subtotal con el total de la maquila
        initial = kwargs.get('initial', {})
        initial['subtotal'] = self.order.total_amount
        kwargs['initial'] = initial
        return kwargs

    def form_valid(self, form):
        invoice = form.save(commit=False)
        invoice.order = self.order
        invoice.company = self.request.user.company
        invoice.created_by = self.request.user
        invoice.save()

        # Cambiar estado de la maquila
        self.order.bill_order()
        self.order.billed_by = self.request.user
        self.order.save()

        # Registrar actividad
        ActivityLog.objects.create(
            user=self.request.user,
            company=self.request.user.company,
            action='invoice_create',
            description=f'Factura {invoice.invoice_number} creada para maquila {self.order.order_number}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            related_order=self.order,
            related_invoice=invoice
        )

        messages.success(
            self.request,
            f'Factura {invoice.invoice_number} creada exitosamente para maquila {self.order.order_number}.'
        )

        return redirect('core:facturacion_list')

    @method_decorator(rol_requerido('aux_facturacion', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# ==================== MÓDULO DE CLIENTES ====================

class ClienteListView(LoginRequiredMixin, ListView):
    """
    Lista de clientes con filtros avanzados y paginación.
    Acceso: aux_registro, admin_company, super_admin
    """
    model = Client
    template_name = 'core/clientes/lista.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        queryset = Client.objects.filter(company=user.company)

        # Filtros
        client_type = self.request.GET.get('client_type')
        search = self.request.GET.get('search')

        if client_type:
            queryset = queryset.filter(client_type=client_type)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(document_number__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Estadísticas rápidas
        queryset = self.get_queryset()
        context['total_clients'] = queryset.count()
        context['active_clients'] = queryset.filter(is_active=True).count()
        context['vip_clients'] = queryset.filter(client_type='vip').count()

        return context

    @method_decorator(rol_requerido('aux_registro', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ClienteCreateView(LoginRequiredMixin, CreateView):
    """
    Crear nuevo cliente con validaciones completas.
    """
    model = Client
    form_class = ClienteForm
    template_name = 'core/clientes/crear.html'
    success_url = reverse_lazy('core:cliente_list')

    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario tenga una empresa asignada
        if not hasattr(request.user, 'company') or not request.user.company:
            messages.error(request, 'No tienes una empresa asignada. Contacta al administrador.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        client = form.save()

        # Registrar actividad
        ActivityLog.objects.create(
            user=self.request.user,
            company=self.request.user.company,
            action='client_create',
            description=f'Cliente {client.full_name} creado exitosamente',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            related_order=None # No related maquila for client creation
        )

        messages.success(
            self.request,
            f'Cliente "{client.full_name}" creado exitosamente.'
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear el cliente. Verifica los datos.')
        return super().form_invalid(form)

    @method_decorator(rol_requerido('aux_registro', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    """
    Editar cliente existente con validaciones completas.
    """
    model = Client
    form_class = ClienteForm
    template_name = 'core/clientes/editar.html'
    success_url = reverse_lazy('core:cliente_list')

    def get_queryset(self):
        """Solo permitir editar clientes de la empresa del usuario"""
        return Client.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        client = form.save()

        # Registrar actividad
        ActivityLog.objects.create(
            user=self.request.user,
            company=self.request.user.company,
            action='client_update',
            description=f'Cliente {client.full_name} actualizado exitosamente',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            related_order=None # No related maquila for client update
        )

        messages.success(
            self.request,
            f'Cliente "{client.full_name}" actualizado exitosamente.'
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al actualizar el cliente. Verifica los datos.')
        return super().form_invalid(form)

    @method_decorator(rol_requerido('aux_registro', 'admin_company', 'super_admin'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# ==================== VISTAS AJAX ====================

@login_required
def maquila_detalle_ajax(request, pk):
    """
    Vista AJAX para obtener detalle completo de una maquila.
    """
    try:
        maquila = Order.objects.select_related(
            'client', 'created_by', 'toasted_by', 'produced_by', 'billed_by', 'delivered_by'
        ).get(id=pk, company=request.user.company)

        data = {
            'id': maquila.id,
            'order_number': maquila.order_number,
            'client': {
                'name': maquila.client.full_name,
                'document': f"{maquila.client.document_type.upper()}: {maquila.client.document_number}",
                'phone': maquila.client.phone,
                'email': maquila.client.email,
            },
            'quantity_kg': str(maquila.quantity_kg),
            'coffee_type': maquila.get_coffee_type_display(),
            'kg_despues_trilla': str(maquila.kg_despues_trilla) if maquila.kg_despues_trilla is not None else None,
            'porcentaje_reduccion_excelso': str(maquila.porcentaje_reduccion_excelso) if maquila.porcentaje_reduccion_excelso is not None else None,
            'packaging_type': maquila.packaging_type,
            'packaging_details': maquila.packaging_details,
            'delivery_method': maquila.get_delivery_method_display(),
            'delivery_address': maquila.delivery_address,
            'committed_date': maquila.committed_date.strftime('%Y-%m-%d') if maquila.committed_date else None,
            'state': maquila.get_state_display(),
            'state_code': maquila.state,
            'created_at': maquila.created_at.strftime('%Y-%m-%d %H:%M'),
            'created_by': maquila.created_by.get_full_name() if maquila.created_by else None,
            'toasted_by': maquila.toasted_by.get_full_name() if maquila.toasted_by else None,
            'produced_by': maquila.produced_by.get_full_name() if maquila.produced_by else None,
            'billed_by': maquila.billed_by.get_full_name() if maquila.billed_by else None,
            'delivered_by': maquila.delivered_by.get_full_name() if maquila.delivered_by else None,
        }

        # Agregar información de procesos si existen
        if hasattr(maquila, 'toasting_process'):
            tp = maquila.toasting_process
            data['toasting_process'] = {
                'temperature': str(tp.temperature_celsius),
                'time': tp.toasting_time_minutes,
                'roast_type': tp.get_roast_type_display(),
                'yield_percentage': str(tp.yield_percentage),
            }

        if hasattr(maquila, 'production_process'):
            pp = maquila.production_process
            data['production_process'] = {
                'process_type': pp.get_process_type_display(),
                'final_weight': str(pp.final_weight_kg),
                'units_produced': pp.units_produced,
                'quality_checks': {
                    'weight': pp.weight_check,
                    'packaging': pp.packaging_check,
                    'labeling': pp.labeling_check,
                }
            }

        if hasattr(maquila, 'invoice'):
            inv = maquila.invoice
            data['invoice'] = {
                'number': inv.invoice_number,
                'total': str(inv.total_amount),
                'status': inv.get_status_display(),
                'due_date': inv.due_date.strftime('%Y-%m-%d') if inv.due_date else None,
            }

        return JsonResponse(data)

    except Order.DoesNotExist:
        return JsonResponse({'error': 'Maquila no encontrada'}, status=404)


@login_required
def cliente_buscar_ajax(request):
    """
    Vista AJAX para autocompletado de clientes.
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    clients = Client.objects.filter(
        company=request.user.company
    ).filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(document_number__icontains=query)
    )[:10]  # Limitar resultados

    results = []
    for client in clients:
        results.append({
            'id': client.id,
            'text': f"{client.full_name} - {client.document_type.upper()}: {client.document_number}",
            'first_name': client.first_name,
            'last_name': client.last_name,
            'document_number': client.document_number,
            'phone': client.phone,
            'email': client.email,
        })

    return JsonResponse({'results': results})
