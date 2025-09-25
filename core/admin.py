from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from .models import (
    Company, User, Client, Order, Invoice, ActivityLog,
    ToastingProcess, ProductionProcess
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """
    Admin personalizado para empresas con acciones de suspensión/activación.
    """
    list_display = ['name', 'slug', 'nit', 'status_badge', 'plan', 'city', 'created_at', 'user_count']
    list_filter = ['status', 'plan', 'city', 'created_at']
    search_fields = ['name', 'slug', 'nit', 'email']
    readonly_fields = ['created_at', 'suspended_at']
    ordering = ['name']

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'nit', 'phone', 'email')
        }),
        ('Ubicación', {
            'fields': ('address', 'city')
        }),
        ('Estado y Plan', {
            'fields': ('status', 'plan', 'suspended_at', 'suspension_reason')
        }),
        ('Facturación', {
            'fields': ('billing_email', 'last_payment_date', 'next_payment_date'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Badge coloreado para el estado"""
        colors = {
            'active': 'green',
            'suspended': 'orange',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def user_count(self, obj):
        """Contar usuarios activos de la empresa"""
        return obj.users.filter(is_active=True).count()
    user_count.short_description = 'Usuarios Activos'

    def get_queryset(self, request):
        """Filtrar empresas según permisos del usuario"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Si no es superuser, solo ver su empresa
            if hasattr(request.user, 'company') and request.user.company:
                return qs.filter(pk=request.user.company.pk)
        return qs

    def has_add_permission(self, request):
        """Solo superusers pueden crear empresas"""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Solo superusers pueden eliminar empresas"""
        return request.user.is_superuser

    actions = ['suspend_companies', 'activate_companies', 'cancel_companies']

    def suspend_companies(self, request, queryset):
        """Acción para suspender empresas"""
        for company in queryset:
            if company.status == 'active':
                company.suspend("Suspendido por administrador")
        self.message_user(request, f"{queryset.count()} empresas suspendidas.")
    suspend_companies.short_description = "Suspender empresas seleccionadas"

    def activate_companies(self, request, queryset):
        """Acción para activar empresas"""
        for company in queryset:
            if company.status in ['suspended', 'active']:
                company.activate()
        self.message_user(request, f"{queryset.count()} empresas activadas.")
    activate_companies.short_description = "Activar empresas seleccionadas"

    def cancel_companies(self, request, queryset):
        """Acción para cancelar empresas"""
        for company in queryset:
            company.cancel("Cancelado por administrador")
        self.message_user(request, f"{queryset.count()} empresas canceladas.")
    cancel_companies.short_description = "Cancelar empresas seleccionadas"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin personalizado para usuarios con filtros por empresa y rol.
    """
    list_display = ['username', 'get_full_name', 'role_badge', 'company', 'is_active', 'last_access', 'date_joined']
    list_filter = ['role', 'is_active', 'company', 'date_joined', 'last_access']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'company__name']
    ordering = ['username']

    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'company', 'phone', 'last_access')
        }),
    )
    readonly_fields = ['last_access', 'date_joined', 'last_login']

    def role_badge(self, obj):
        """Badge coloreado para el rol"""
        colors = {
            'super_admin': 'purple',
            'admin_company': 'blue',
            'aux_registro': 'green',
            'aux_tostion': 'orange',
            'aux_produccion': 'red',
            'aux_facturacion': 'teal'
        }
        color = colors.get(obj.role, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Rol'

    def get_queryset(self, request):
        """Filtrar usuarios según permisos"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Si no es superuser, solo ver usuarios de su empresa
            if hasattr(request.user, 'company') and request.user.company:
                return qs.filter(company=request.user.company)
        return qs

    def has_add_permission(self, request):
        """Verificar permisos para crear usuarios"""
        if request.user.is_superuser:
            return True
        return request.user.can_manage_company()

    def has_change_permission(self, request, obj=None):
        """Verificar permisos para cambiar usuarios"""
        if request.user.is_superuser:
            return True
        if obj and obj.company == request.user.company:
            return request.user.can_manage_company()
        return False

    def has_delete_permission(self, request, obj=None):
        """Verificar permisos para eliminar usuarios"""
        if request.user.is_superuser:
            return True
        if obj and obj.company == request.user.company:
            return request.user.can_manage_company()
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtrar empresas disponibles según permisos"""
        if db_field.name == 'company':
            if not request.user.is_superuser:
                # Solo mostrar la empresa del usuario
                if hasattr(request.user, 'company') and request.user.company:
                    kwargs['queryset'] = Company.objects.filter(pk=request.user.company.pk)
                else:
                    kwargs['queryset'] = Company.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """
    Admin de solo lectura para logs de actividad.
    """
    list_display = ['timestamp', 'user', 'company', 'action_badge', 'description_short', 'ip_address']
    list_filter = ['action', 'timestamp', 'company']
    search_fields = ['user__username', 'company__name', 'description', 'ip_address']
    readonly_fields = ['user', 'company', 'action', 'description', 'ip_address', 'user_agent',
                      'timestamp', 'related_order', 'related_invoice']
    ordering = ['-timestamp']

    def description_short(self, obj):
        """Descripción corta para la lista"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Descripción'

    def action_badge(self, obj):
        """Badge para la acción"""
        return format_html(
            '<span style="background-color: lightblue; padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.get_action_display()
        )
    action_badge.short_description = 'Acción'

    def has_add_permission(self, request):
        """No permitir crear logs manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo superusers pueden eliminar logs antiguos"""
        return request.user.is_superuser


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Admin personalizado para clientes con métricas y filtros avanzados.
    """
    list_display = ['full_name', 'document_number', 'client_type_badge', 'company', 'phone', 'email', 'orders_count', 'total_orders_value', 'created_at']
    list_filter = ['company', 'client_type', 'city', 'created_at', 'is_active']
    search_fields = ['first_name', 'last_name', 'document_number', 'email', 'phone']
    ordering = ['-created_at']
    readonly_fields = ['orders_count', 'total_orders_value', 'created_at', 'updated_at']

    fieldsets = (
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'document_type', 'document_number')
        }),
        ('Información de Contacto', {
            'fields': ('phone', 'email', 'address', 'city')
        }),
        ('Clasificación', {
            'fields': ('client_type', 'is_active', 'notes')
        }),
        ('Empresa', {
            'fields': ('company',),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('orders_count', 'total_orders_value'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def client_type_badge(self, obj):
        """Badge coloreado para el tipo de cliente"""
        colors = {
            'new': 'blue',
            'frequent': 'green',
            'vip': 'gold'
        }
        color = colors.get(obj.client_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_client_type_display()
        )
    client_type_badge.short_description = 'Tipo'

    def orders_count(self, obj):
        """Cuenta de pedidos del cliente"""
        return obj.get_orders_count()
    orders_count.short_description = 'Pedidos'

    def total_orders_value(self, obj):
        """Valor total de pedidos"""
        total = obj.get_total_orders_value()
        return f"${total:,.0f}" if total else "$0"
    total_orders_value.short_description = 'Valor Total'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            if hasattr(request.user, 'company') and request.user.company:
                return qs.filter(company=request.user.company)
        return qs

    def has_add_permission(self, request):
        """Verificar permisos para crear clientes"""
        if request.user.is_superuser:
            return True
        return request.user.role in ['aux_registro', 'admin_company']

    def has_change_permission(self, request, obj=None):
        """Verificar permisos para cambiar clientes"""
        if request.user.is_superuser:
            return True
        if obj and obj.company == request.user.company:
            return request.user.role in ['aux_registro', 'admin_company']
        return False

    def has_delete_permission(self, request, obj=None):
        """Verificar permisos para eliminar clientes"""
        if request.user.is_superuser:
            return True
        if obj and obj.company == request.user.company:
            return request.user.can_manage_company()
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtrar empresas disponibles según permisos"""
        if db_field.name == 'company':
            if not request.user.is_superuser:
                if hasattr(request.user, 'company') and request.user.company:
                    kwargs['queryset'] = Company.objects.filter(pk=request.user.company.pk)
                else:
                    kwargs['queryset'] = Company.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin personalizado para pedidos con badges de estado y filtros avanzados.
    """
    list_display = ['order_number', 'client', 'company', 'state_badge', 'quantity_kg', 'coffee_type', 'total_amount', 'committed_date', 'days_to_delivery', 'created_by', 'created_at']
    list_filter = ['state', 'company', 'coffee_type', 'delivery_method', 'created_at', 'committed_date', 'created_by']
    search_fields = ['order_number', 'client__first_name', 'client__last_name', 'client__document_number']
    ordering = ['-created_at']
    readonly_fields = ['order_number', 'total_amount', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Información General', {
            'fields': ('order_number', 'client', 'company', 'created_by')
        }),
        ('Producto y Cantidades', {
            'fields': ('quantity_kg', 'coffee_type', 'price_per_kg', 'total_amount')
        }),
        ('Empaque y Entrega', {
            'fields': ('packaging_type', 'packaging_details', 'delivery_method', 'delivery_address', 'committed_date')
        }),
        ('Estado del Pedido', {
            'fields': ('state',),
            'classes': ('collapse',)
        }),
        ('Fechas de Proceso', {
            'fields': ('registered_at', 'toasting_started_at', 'toasting_completed_at', 'production_started_at', 'production_completed_at', 'billed_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
        ('Usuarios Responsables', {
            'fields': ('toasted_by', 'produced_by', 'billed_by', 'delivered_by'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def state_badge(self, obj):
        """Badge coloreado para el estado del pedido"""
        colors = {
            'registered': 'blue',
            'in_toasting': 'orange',
            'toasting_complete': 'yellow',
            'in_production': 'purple',
            'ready_for_billing': 'teal',
            'billed': 'green',
            'delivered': 'emerald',
            'cancelled': 'red'
        }
        color = colors.get(obj.state, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;">{}</span>',
            color, obj.get_state_display()
        )
    state_badge.short_description = 'Estado'

    def days_to_delivery(self, obj):
        """Días para entrega"""
        days = obj.get_days_to_delivery()
        if days is None:
            return '-'
        elif days < 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', f"{abs(days)} días atrasado")
        elif days == 0:
            return format_html('<span style="color: orange; font-weight: bold;">Hoy</span>')
        else:
            return f"{days} días"
    days_to_delivery.short_description = 'Días para entrega'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            if hasattr(request.user, 'company') and request.user.company:
                return qs.filter(company=request.user.company)
        return qs

    def has_add_permission(self, request):
        """Verificar permisos para crear pedidos"""
        if request.user.is_superuser:
            return True
        return request.user.role in ['aux_registro', 'admin_company']

    def has_change_permission(self, request, obj=None):
        """Verificar permisos para cambiar pedidos según estado y rol"""
        if request.user.is_superuser:
            return True

        if not obj or not hasattr(request.user, 'company') or obj.company != request.user.company:
            return False

        # Permisos según estado y rol
        state_permissions = {
            'registered': ['aux_registro', 'aux_tostion', 'admin_company'],
            'in_toasting': ['aux_tostion', 'admin_company'],
            'toasting_complete': ['aux_produccion', 'admin_company'],
            'in_production': ['aux_produccion', 'admin_company'],
            'ready_for_billing': ['aux_facturacion', 'admin_company'],
            'billed': ['aux_facturacion', 'admin_company'],
            'delivered': ['admin_company'],  # Solo admin puede marcar como entregado
            'cancelled': ['admin_company']
        }

        allowed_roles = state_permissions.get(obj.state, [])
        return request.user.role in allowed_roles or request.user.can_manage_company()

    def has_delete_permission(self, request, obj=None):
        """Solo admins pueden eliminar pedidos"""
        if request.user.is_superuser:
            return True
        if obj and obj.company == request.user.company:
            return request.user.can_manage_company()
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtrar opciones según permisos"""
        if db_field.name == 'company':
            if not request.user.is_superuser:
                if hasattr(request.user, 'company') and request.user.company:
                    kwargs['queryset'] = Company.objects.filter(pk=request.user.company.pk)
                else:
                    kwargs['queryset'] = Company.objects.none()
        elif db_field.name == 'client':
            if not request.user.is_superuser:
                if hasattr(request.user, 'company') and request.user.company:
                    kwargs['queryset'] = Client.objects.filter(company=request.user.company)
                else:
                    kwargs['queryset'] = Client.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    actions = ['mark_as_cancelled', 'export_selected']

    def mark_as_cancelled(self, request, queryset):
        """Marcar pedidos como cancelados"""
        updated = 0
        for order in queryset:
            if order.state != 'cancelled' and order.state != 'delivered':
                order.cancel_order()
                updated += 1
        self.message_user(request, f"{updated} pedidos marcados como cancelados.")
    mark_as_cancelled.short_description = "Marcar como cancelados"

    def export_selected(self, request, queryset):
        """Exportar pedidos seleccionados (placeholder)"""
        self.message_user(request, f"Exportando {queryset.count()} pedidos...")
    export_selected.short_description = "Exportar pedidos"


@admin.register(ToastingProcess)
class ToastingProcessAdmin(admin.ModelAdmin):
    """
    Admin para procesos de tostión con métricas de rendimiento.
    """
    list_display = ['order', 'company', 'process_status_badge', 'received_quantity_kg', 'processed_quantity_kg', 'yield_percentage_display', 'current_temperature_celsius', 'roast_type', 'final_grain_quality_badge', 'processed_by', 'completed_at']
    list_filter = ['process_status', 'final_grain_quality', 'roast_type', 'received_at', 'completed_at']
    search_fields = ['order__order_number', 'processed_by__username']
    ordering = ['-received_at']
    readonly_fields = ['yield_percentage', 'received_at', 'started_at', 'completed_at']

    fieldsets = (
        ('Pedido Asociado', {
            'fields': ('order',)
        }),
        ('Estado del Proceso', {
            'fields': ('process_status',)
        }),
        ('Equipo y Configuración', {
            'fields': ('toasting_equipment', 'equipment_capacity_kg', 'initial_temperature_celsius', 'target_temperature_celsius', 'estimated_time_minutes', 'roast_type')
        }),
        ('Cantidades', {
            'fields': ('received_quantity_kg', 'processed_quantity_kg', 'yield_percentage')
        }),
        ('Monitoreo en Tiempo Real', {
            'fields': ('current_temperature_celsius', 'current_time_elapsed_minutes', 'current_humidity_percentage', 'current_weight_loss_kg')
        }),
        ('Control de Calidad', {
            'fields': ('final_grain_quality', 'final_quality_notes', 'quality_samples')
        }),
        ('Procesamiento', {
            'fields': ('processed_by', 'notes')
        }),
        ('Fechas', {
            'fields': ('received_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def company(self, obj):
        return obj.order.company
    company.short_description = 'Empresa'

    def process_status_badge(self, obj):
        """Badge para el estado del proceso"""
        colors = {
            'received': 'blue',
            'started': 'orange',
            'monitoring': 'yellow',
            'completed': 'green'
        }
        color = colors.get(obj.process_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_process_status_display()
        )
    process_status_badge.short_description = 'Estado'

    def yield_percentage_display(self, obj):
        """Mostrar rendimiento con color"""
        if obj.yield_percentage is None:
            return '-'
        percentage = obj.yield_percentage
        if percentage >= 95:
            color = 'green'
        elif percentage >= 90:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, percentage)
    yield_percentage_display.short_description = 'Rendimiento'

    def final_grain_quality_badge(self, obj):
        """Badge para calidad final del grano"""
        if not obj.final_grain_quality:
            return '-'
        colors = {
            'excellent': 'green',
            'good': 'blue',
            'regular': 'yellow',
            'poor': 'red'
        }
        color = colors.get(obj.final_grain_quality, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_final_grain_quality_display()
        )
    final_grain_quality_badge.short_description = 'Calidad Final'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            if hasattr(request.user, 'company') and request.user.company:
                return qs.filter(order__company=request.user.company)
        return qs

    def has_add_permission(self, request):
        """Solo admin_company puede crear procesos de tostión"""
        if request.user.is_superuser:
            return True
        return request.user.role == 'admin_company'

    def has_change_permission(self, request, obj=None):
        """Solo admin_company puede editar procesos de tostión"""
        if request.user.is_superuser:
            return True
        if obj and obj.order.company == request.user.company:
            return request.user.role == 'admin_company'
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo admin_company puede eliminar procesos de tostión"""
        if request.user.is_superuser:
            return True
        if obj and obj.order.company == request.user.company:
            return request.user.role == 'admin_company'
        return False

    def has_view_permission(self, request, obj=None):
        """Admin_company y aux_tostion pueden ver procesos de tostión"""
        if request.user.is_superuser:
            return True
        if obj and obj.order.company == request.user.company:
            return request.user.role in ['aux_tostion', 'admin_company']
        elif not obj:
            # Para la vista de lista
            return request.user.role in ['aux_tostion', 'admin_company']
        return False

    def has_module_permission(self, request):
        """Controlar acceso al módulo completo"""
        if request.user.is_superuser:
            return True
        return request.user.role in ['aux_tostion', 'admin_company']


@admin.register(ProductionProcess)
class ProductionProcessAdmin(admin.ModelAdmin):
    """
    Admin para procesos de producción con controles de calidad.
    """
    list_display = ['order', 'company', 'process_type', 'final_weight_kg', 'units_produced', 'quality_status', 'processed_by', 'completed_at']
    list_filter = ['process_type', 'weight_check', 'packaging_check', 'labeling_check', 'started_at', 'completed_at']
    search_fields = ['order__order_number', 'processed_by__username']
    ordering = ['-started_at']
    readonly_fields = ['started_at', 'completed_at']

    fieldsets = (
        ('Pedido Asociado', {
            'fields': ('order',)
        }),
        ('Tipo de Proceso', {
            'fields': ('process_type', 'grinding_type', 'packaging_details')
        }),
        ('Resultados', {
            'fields': ('final_weight_kg', 'units_produced')
        }),
        ('Control de Calidad', {
            'fields': ('weight_check', 'packaging_check', 'labeling_check')
        }),
        ('Procesamiento', {
            'fields': ('processed_by', 'notes')
        }),
        ('Fechas', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def company(self, obj):
        return obj.order.company
    company.short_description = 'Empresa'

    def quality_status(self, obj):
        """Estado de controles de calidad"""
        checks = [obj.weight_check, obj.packaging_check, obj.labeling_check]
        passed = sum(checks)
        total = len(checks)

        if passed == total:
            return format_html('<span style="color: green;">✓ Completo ({}/{})</span>', passed, total)
        elif passed > 0:
            return format_html('<span style="color: orange;">⚠ Parcial ({}/{})</span>', passed, total)
        else:
            return format_html('<span style="color: red;">✗ Pendiente ({}/{})</span>', passed, total)
    quality_status.short_description = 'Calidad'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            if hasattr(request.user, 'company') and request.user.company:
                return qs.filter(order__company=request.user.company)
        return qs

    def has_add_permission(self, request):
        """Solo usuarios de producción pueden crear procesos"""
        if request.user.is_superuser:
            return True
        return request.user.role in ['aux_produccion', 'admin_company']

    def has_change_permission(self, request, obj=None):
        """Verificar permisos según empresa"""
        if request.user.is_superuser:
            return True
        if obj and obj.order.company == request.user.company:
            return request.user.role in ['aux_produccion', 'admin_company']
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin personalizado para facturas con estados y alertas.
    """
    list_display = ['invoice_number', 'order', 'company', 'total_amount', 'status_badge', 'issue_date', 'due_date', 'days_overdue', 'created_by']
    list_filter = ['status', 'company', 'issue_date', 'due_date', 'created_by']
    search_fields = ['invoice_number', 'order__order_number', 'order__client__first_name', 'order__client__last_name']
    ordering = ['-issue_date']
    readonly_fields = ['invoice_number', 'tax_amount', 'total_amount', 'created_at', 'updated_at']
    date_hierarchy = 'issue_date'

    fieldsets = (
        ('Información General', {
            'fields': ('invoice_number', 'order', 'company', 'created_by')
        }),
        ('Fechas', {
            'fields': ('issue_date', 'due_date', 'payment_date')
        }),
        ('Valores', {
            'fields': ('subtotal', 'tax_rate', 'tax_amount', 'total_amount')
        }),
        ('Estado', {
            'fields': ('status',)
        }),
        ('Entrega', {
            'fields': ('delivery_person', 'recipient_person', 'delivery_notes'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Badge coloreado para el estado de la factura"""
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'overdue': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def days_overdue(self, obj):
        """Días de vencimiento"""
        days = obj.days_overdue()
        if days == 0:
            return '-'
        else:
            return format_html('<span style="color: red; font-weight: bold;">{} días</span>', days)
    days_overdue.short_description = 'Días Vencida'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            if hasattr(request.user, 'company') and request.user.company:
                return qs.filter(company=request.user.company)
        return qs

    def has_add_permission(self, request):
        """Solo usuarios de facturación pueden crear facturas"""
        if request.user.is_superuser:
            return True
        return request.user.role in ['aux_facturacion', 'admin_company']

    def has_change_permission(self, request, obj=None):
        """Verificar permisos según empresa"""
        if request.user.is_superuser:
            return True
        if obj and obj.company == request.user.company:
            return request.user.role in ['aux_facturacion', 'admin_company']
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo admins pueden eliminar facturas"""
        if request.user.is_superuser:
            return True
        if obj and obj.company == request.user.company:
            return request.user.can_manage_company()
        return False

    actions = ['mark_as_paid', 'mark_as_overdue']

    def mark_as_paid(self, request, queryset):
        """Marcar facturas como pagadas"""
        updated = queryset.filter(status__in=['pending', 'overdue']).update(
            status='paid',
            payment_date=timezone.now()
        )
        self.message_user(request, f"{updated} facturas marcadas como pagadas.")
    mark_as_paid.short_description = "Marcar como pagadas"

    def mark_as_overdue(self, request, queryset):
        """Marcar facturas como vencidas"""
        updated = queryset.filter(status='pending').update(status='overdue')
        self.message_user(request, f"{updated} facturas marcadas como vencidas.")
    mark_as_overdue.short_description = "Marcar como vencidas"
