from django.db import models
from django.contrib.auth.models import AbstractUser
from django_fsm import FSMField, transition
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError


class Company(models.Model):
    """
    Modelo para empresas maquiladoras con multi-tenancy.
    """
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('suspended', 'Suspendida'),
        ('cancelled', 'Cancelada'),
    ]

    PLAN_CHOICES = [
        ('basic', 'Básico'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nombre de la empresa")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug único")
    nit = models.CharField(max_length=20, unique=True, verbose_name="NIT")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Email")
    address = models.TextField(verbose_name="Dirección")
    city = models.CharField(max_length=50, default='', blank=True, verbose_name="Ciudad")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Estado"
    )
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='basic',
        verbose_name="Plan de suscripción"
    )

    # Fechas de control
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    suspended_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de suspensión")
    suspension_reason = models.TextField(blank=True, verbose_name="Motivo de suspensión")

    # Configuración de facturación
    billing_email = models.EmailField(blank=True, verbose_name="Email de facturación")
    last_payment_date = models.DateField(null=True, blank=True, verbose_name="Último pago")
    next_payment_date = models.DateField(null=True, blank=True, verbose_name="Próximo pago")

    def __str__(self):
        return f"{self.name} ({self.slug})"

    @property
    def is_active(self):
        return self.status == 'active'

    def suspend(self, reason=""):
        """Suspender la empresa"""
        if self.status != 'active':
            raise ValidationError("La empresa no está activa")
        self.status = 'suspended'
        self.suspended_at = timezone.now()
        self.suspension_reason = reason
        self.save()

    def activate(self):
        """Activar la empresa"""
        if self.status == 'cancelled':
            raise ValidationError("No se puede activar una empresa cancelada")
        self.status = 'active'
        self.suspended_at = None
        self.suspension_reason = ""
        self.save()

    def cancel(self, reason=""):
        """Cancelar la empresa"""
        self.status = 'cancelled'
        self.suspension_reason = reason
        self.save()

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['name']


class User(AbstractUser):
    """
    Modelo de usuario personalizado con roles específicos y multi-tenancy.
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrador'),
        ('admin_company', 'Administrador de Empresa'),
        ('aux_registro', 'Auxiliar de Registro'),
        ('aux_tostion', 'Auxiliar de Tostión'),
        ('aux_produccion', 'Auxiliar de Producción'),
        ('aux_facturacion', 'Auxiliar de Facturación'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='aux_registro',
        verbose_name="Rol"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        verbose_name="Empresa"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    last_access = models.DateTimeField(null=True, blank=True, verbose_name="Último acceso")

    def __str__(self):
        company_name = self.company.name if self.company else "Sin empresa"
        return f"{self.get_full_name()} - {company_name}"

    def has_company_permission(self, permission_codename):
        """Verificar si el usuario tiene permiso en su empresa"""
        if not self.company or not self.company.is_active:
            return False
        return self.has_perm(f'core.{permission_codename}')

    def is_company_admin(self):
        """Verificar si es admin de empresa"""
        return self.role == 'admin_company'

    def is_super_admin(self):
        """Verificar si es super admin"""
        return self.role == 'super_admin'

    def can_manage_company(self):
        """Verificar si puede gestionar la empresa"""
        return self.is_super_admin() or self.is_company_admin()

    def log_access(self, ip_address=None):
        """Registrar acceso del usuario"""
        self.last_access = timezone.now()
        self.save(update_fields=['last_access'])

        # Crear log de actividad
        ActivityLog.objects.create(
            user=self,
            company=self.company,
            action='login',
            description=f'Inicio de sesión desde IP: {ip_address or "desconocida"}',
            ip_address=ip_address
        )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"


class Client(models.Model):
    """
    Modelo para clientes (productores de café).
    """
    CLIENT_TYPE_CHOICES = [
        ('new', 'Nuevo'),
        ('frequent', 'Frecuente'),
        ('vip', 'VIP'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='clients'
    )
    first_name = models.CharField(max_length=50, verbose_name="Nombres")
    last_name = models.CharField(max_length=50, verbose_name="Apellidos")
    business_name = models.CharField(max_length=100, blank=True, verbose_name="Razón social")
    document_type = models.CharField(
        max_length=10,
        choices=[
            ('cc', 'Cédula'),
            ('nit', 'NIT'),
        ],
        default='cc',
        verbose_name="Tipo de documento"
    )
    document_number = models.CharField(max_length=20, verbose_name="Número de documento")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Email")
    address = models.TextField(verbose_name="Dirección")
    city = models.CharField(max_length=50, default='', blank=True, verbose_name="Ciudad")
    client_type = models.CharField(
        max_length=10,
        choices=CLIENT_TYPE_CHOICES,
        default='new',
        verbose_name="Tipo de cliente"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_orders_count(self):
        """Cuenta total de pedidos del cliente"""
        return self.orders.count()

    def get_last_order(self):
        """Obtiene el último pedido del cliente"""
        return self.orders.order_by('-created_at').first()

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        unique_together = ['company', 'document_number']
        ordering = ['-created_at']


class Order(models.Model):
    """
    Modelo para pedidos de maquila con estados FSM completos.
    """
    STATE_CHOICES = [
        ('registered', 'Registrado'),
        ('in_toasting', 'En Tostión'),
        ('toasting_complete', 'Tostión Completa'),
        ('in_production', 'En Producción'),
        ('ready_for_billing', 'Listo para Facturar'),
        ('billed', 'Facturado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    DELIVERY_METHOD_CHOICES = [
        ('pickup', 'Recogida en local'),
        ('delivery', 'Entrega a domicilio'),
        ('shipping', 'Envío por transporte'),
    ]

    PACKAGING_PRESENTATION_CHOICES = [
        ('cps', 'CPS (Café Pergamino Seco)'),
        ('excelso', 'Excelso'),
    ]

    COFFEE_TYPE_CHOICES = PACKAGING_PRESENTATION_CHOICES  # Alias for compatibility

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Cliente"
    )
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Número de pedido")
    quantity_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad en KG"
    )
    coffee_type = models.CharField(
        max_length=20,
        choices=PACKAGING_PRESENTATION_CHOICES,
        default='excelso',
        verbose_name="Tipo de café"
    )
    original_coffee_type = models.CharField(
        max_length=20,
        choices=PACKAGING_PRESENTATION_CHOICES,
        null=True,
        blank=True,
        verbose_name="Tipo de café original (recepción)"
    )

    # Nuevos campos para el proceso de maquila
    kg_despues_trilla = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="KG después de trilla (Excelso)"
    )
    porcentaje_reduccion_excelso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        verbose_name="Reducción Excelso (%)"
    )

    # Información de empaque y entrega
    packaging_type = models.CharField(
        max_length=100,
        verbose_name="Tipo de empaque"
    )
    packaging_details = models.TextField(
        blank=True,
        verbose_name="Detalles de empaque"
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_METHOD_CHOICES,
        default='pickup',
        verbose_name="Forma de entrega"
    )
    delivery_address = models.TextField(
        blank=True,
        verbose_name="Dirección de entrega"
    )
    committed_date = models.DateField(verbose_name="Fecha comprometida")

    # Estado FSM
    state = FSMField(
        default='registered',
        choices=STATE_CHOICES,
        protected=True,
        verbose_name="Estado"
    )

    # Fechas de proceso
    registered_at = models.DateTimeField(default=timezone.now, verbose_name="Fecha de registro")
    toasting_started_at = models.DateTimeField(null=True, blank=True, verbose_name="Inicio de tostión")
    toasting_completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fin de tostión")
    production_started_at = models.DateTimeField(null=True, blank=True, verbose_name="Inicio de producción")
    production_completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fin de producción")
    billed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de facturación")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de entrega")

    # Usuarios responsables
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_orders',
        verbose_name="Creado por"
    )
    toasted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='toasted_orders',
        verbose_name="Tostado por"
    )
    produced_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produced_orders',
        verbose_name="Producido por"
    )
    billed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='billed_orders',
        verbose_name="Facturado por"
    )
    delivered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivered_orders',
        verbose_name="Entregado por"
    )

    # Notas y observaciones
    notes = models.TextField(blank=True, verbose_name="Notas")
    internal_notes = models.TextField(blank=True, verbose_name="Notas internas")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generar número de maquila si no existe
        if not self.order_number:
            self.order_number = self.generate_order_number()

        # Establecer original_coffee_type si es una nueva maquila
        if self._state.adding and not self.original_coffee_type:
            self.original_coffee_type = self.coffee_type

        # Calcular porcentaje de reducción y manejar kg_despues_trilla según la lógica
        if self.original_coffee_type == 'cps' and self.coffee_type == 'excelso':
            if self.quantity_kg and self.kg_despues_trilla is not None:
                if self.quantity_kg > 0:  # Evitar división por cero
                    reduction = self.quantity_kg - self.kg_despues_trilla
                    self.porcentaje_reduccion_excelso = (reduction / self.quantity_kg) * 100
                else:
                    self.porcentaje_reduccion_excelso = Decimal(0.00)
            else:
                # Si es excelso pero no hay kg_despues_trilla (e.g., error o no se ha llenado)
                self.kg_despues_trilla = None  # Asegurarse de que sea None si no es válido
                self.porcentaje_reduccion_excelso = None
        else:
            # Si el café original no fue CPS, o si es CPS pero no se ha trillado a excelso
            self.kg_despues_trilla = None
            self.porcentaje_reduccion_excelso = None

        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Genera número único de maquila"""
        import datetime
        today = datetime.date.today()
        base_number = f"MAQ-{self.company.nit}-{today.strftime('%Y%m%d')}"

        # Buscar el último número del día
        last_order = Order.objects.filter(
            company=self.company,
            order_number__startswith=base_number
        ).order_by('-order_number').first()

        if last_order:
            # Extraer el número secuencial
            last_num = int(last_order.order_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{base_number}-{new_num:03d}"

    def get_days_to_delivery(self):
        """Calcula días para entrega"""
        if self.committed_date:
            from datetime import date
            return (self.committed_date - date.today()).days
        return None

    def is_overdue(self):
        """Verifica si el pedido está atrasado"""
        days = self.get_days_to_delivery()
        return days is not None and days < 0

    def can_transition_to(self, new_state):
        """Valida si puede transicionar a un estado"""
        valid_transitions = {
            'registered': ['in_toasting', 'cancelled'],
            'in_toasting': ['toasting_complete', 'cancelled'],
            'toasting_complete': ['in_production', 'cancelled'],
            'in_production': ['ready_for_billing', 'cancelled'],
            'ready_for_billing': ['billed', 'cancelled'],
            'billed': ['delivered', 'cancelled'],
            'delivered': [],  # Estado final
            'cancelled': [],  # Estado final
        }
        return new_state in valid_transitions.get(self.state, [])

    def __str__(self):
        return f"Maquila {self.order_number} - {self.client.full_name}"

    # Transiciones FSM
    @transition(field=state, source='registered', target='in_toasting')
    def start_toasting(self):
        self.toasting_started_at = timezone.now()

    @transition(field=state, source='in_toasting', target='toasting_complete')
    def complete_toasting(self):
        self.toasting_completed_at = timezone.now()

    @transition(field=state, source='toasting_complete', target='in_production')
    def start_production(self):
        self.production_started_at = timezone.now()

    @transition(field=state, source='in_production', target='ready_for_billing')
    def complete_production(self):
        self.production_completed_at = timezone.now()

    @transition(field=state, source='ready_for_billing', target='billed')
    def bill_order(self):
        self.billed_at = timezone.now()

    @transition(field=state, source='billed', target='delivered')
    def deliver_order(self):
        self.delivered_at = timezone.now()

    @transition(field=state, source=['registered', 'in_toasting', 'toasting_complete', 'in_production', 'ready_for_billing', 'billed'], target='cancelled')
    def cancel_order(self):
        pass

    class Meta:
        verbose_name = "Maquila"
        verbose_name_plural = "Maquilas"
        ordering = ['created_at']
        permissions = [
            ('can_manage_orders', 'Puede gestionar maquilas'),
            ('can_view_all_orders', 'Puede ver todas las maquilas'),
        ]


class ToastingProcess(models.Model):
    """
    Control completo del proceso de tostión paso a paso.
    """
    PROCESS_STATUS_CHOICES = [
        ('received', 'Recibido'),
        ('started', 'Iniciado'),
        ('monitoring', 'Monitoreando'),
        ('completed', 'Completado'),
    ]

    TOASTING_EQUIPMENT_CHOICES = [
        ('industrial_200kg', 'Industrial 200kg'),
        ('industrial_500kg', 'Industrial 500kg'),
        ('artisanal_50kg', 'Artesanal 50kg'),
        ('experimental_10kg', 'Experimental 10kg'),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='toasting_process',
        verbose_name="Maquila"
    )

    # Estado del proceso
    process_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='received',
        verbose_name="Estado del proceso"
    )

    # Fechas del proceso
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de recepción")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de inicio")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de finalización")

    # Equipo de tostión
    toasting_equipment = models.CharField(
        max_length=30,
        choices=TOASTING_EQUIPMENT_CHOICES,
        default='industrial_200kg',
        verbose_name="Equipo de tostión"
    )
    equipment_capacity_kg = models.PositiveIntegerField(
        default=200,
        verbose_name="Capacidad del equipo (kg)"
    )

    # Control de kilos
    received_quantity_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Kilos recibidos"
    )
    processed_quantity_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Kilos procesados"
    )
    yield_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        verbose_name="Rendimiento (%)"
    )

    # Parámetros técnicos iniciales
    initial_temperature_celsius = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=150.0,
        verbose_name="Temperatura inicial (°C)"
    )
    target_temperature_celsius = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=200.0,
        verbose_name="Temperatura objetivo (°C)"
    )
    estimated_time_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name="Tiempo estimado (min)"
    )

    # Monitoreo en tiempo real
    current_temperature_celsius = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Temperatura actual (°C)"
    )
    current_time_elapsed_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="Tiempo transcurrido (min)"
    )
    current_humidity_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Humedad actual (%)"
    )
    current_weight_loss_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Pérdida de peso actual (kg)"
    )

    roast_type = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Claro'),
            ('medium', 'Medio'),
            ('dark', 'Oscuro'),
        ],
        verbose_name="Tipo de tueste"
    )

    # Muestras de calidad durante el proceso (JSON)
    quality_samples = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Muestras de calidad"
    )

    # Control de calidad final
    final_grain_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excelente'),
            ('good', 'Buena'),
            ('regular', 'Regular'),
            ('poor', 'Deficiente'),
        ],
        null=True,
        blank=True,
        verbose_name="Calidad final del grano"
    )
    final_quality_notes = models.TextField(blank=True, verbose_name="Notas finales de calidad")

    # Usuario responsable
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='toasting_processes',
        verbose_name="Procesado por"
    )

    # Notas adicionales
    notes = models.TextField(blank=True, verbose_name="Notas")

    def save(self, *args, **kwargs):
        # Calcular rendimiento automáticamente cuando se complete
        if self.process_status == 'completed' and self.processed_quantity_kg:
            self.yield_percentage = (self.processed_quantity_kg / self.received_quantity_kg) * 100
        super().save(*args, **kwargs)

    def can_start_toasting(self):
        """Verifica si puede iniciar el proceso de tostión"""
        return self.process_status == 'received'

    def can_monitor_toasting(self):
        """Verifica si puede monitorear el proceso"""
        return self.process_status in ['started', 'monitoring']

    def can_complete_toasting(self):
        """Verifica si puede completar el proceso"""
        return self.process_status == 'monitoring'

    def start_process(self):
        """Inicia el proceso de tostión"""
        if self.can_start_toasting():
            self.process_status = 'started'
            self.started_at = timezone.now()
            self.save()

    def update_monitoring(self, temperature, time_elapsed, humidity=None, weight_loss=None):
        """Actualiza datos de monitoreo"""
        if self.can_monitor_toasting():
            self.process_status = 'monitoring'
            self.current_temperature_celsius = temperature
            self.current_time_elapsed_minutes = time_elapsed
            if humidity is not None:
                self.current_humidity_percentage = humidity
            if weight_loss is not None:
                self.current_weight_loss_kg = weight_loss
            self.save()

    def complete_process(self, processed_quantity, final_quality, notes=""):
        """Completa el proceso de tostión"""
        if self.can_complete_toasting():
            self.process_status = 'completed'
            self.completed_at = timezone.now()
            self.processed_quantity_kg = processed_quantity
            self.final_grain_quality = final_quality
            self.final_quality_notes = notes
            self.yield_percentage = (processed_quantity / self.received_quantity_kg) * 100
            self.save()

    def __str__(self):
        return f"Tostión - Maquila {self.order.order_number}"

    class Meta:
        verbose_name = "Proceso de Tostión"
        verbose_name_plural = "Procesos de Tostión"
        ordering = ['received_at']


class ProductionProcess(models.Model):
    """
    Gestión del empaque y preparación final.
    """
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='production_process',
        verbose_name="Maquila"
    )

    # Fechas del proceso
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de inicio")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de finalización")

    # Tipo de proceso
    process_type = models.CharField(
        max_length=20,
        choices=[
            ('grinding', 'Molido'),
            ('packaging', 'Empacado'),
            ('bulk', 'Granel'),
        ],
        verbose_name="Proceso realizado"
    )

    # Detalles de empaque
    grinding_type = models.CharField(
        max_length=20,
        choices=[
            ('fine', 'Fino'),
            ('medium', 'Medio'),
            ('coarse', 'Grueso'),
        ],
        null=True,
        blank=True,
        verbose_name="Tipo de molido"
    )
    packaging_details = models.TextField(verbose_name="Detalles de empaque")

    # Control de calidad
    weight_check = models.BooleanField(default=False, verbose_name="Control de peso ✓")
    packaging_check = models.BooleanField(default=False, verbose_name="Control de empaque ✓")
    labeling_check = models.BooleanField(default=False, verbose_name="Control de etiquetado ✓")

    # Resultados finales
    final_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Peso total producido (KG)"
    )
    units_produced = models.PositiveIntegerField(verbose_name="Unidades producidas")

    # Usuario responsable
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='production_processes',
        verbose_name="Procesado por"
    )

    # Notas
    notes = models.TextField(blank=True, verbose_name="Notas")

    def is_quality_complete(self):
        """Verifica si todos los controles de calidad están completos"""
        return self.weight_check and self.packaging_check and self.labeling_check

    def __str__(self):
        return f"Producción - Maquila {self.order.order_number}"

    class Meta:
        verbose_name = "Proceso de Producción"
        verbose_name_plural = "Procesos de Producción"
        ordering = ['started_at']


class Invoice(models.Model):
    """
    Información completa de facturación.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='invoice',
        verbose_name="Maquila"
    )
    invoice_number = models.CharField(max_length=20, unique=True, verbose_name="Número de factura")

    # Fechas
    issue_date = models.DateField(default=timezone.now, verbose_name="Fecha de emisión")
    due_date = models.DateField(verbose_name="Fecha de vencimiento")
    payment_date = models.DateField(null=True, blank=True, verbose_name="Fecha de pago")

    # Valores con cálculos automáticos
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Subtotal"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=19,  # IVA Colombia
        verbose_name="Tasa de impuesto (%)"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        verbose_name="Valor del impuesto"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        verbose_name="Total"
    )

    # Estado de la factura
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('paid', 'Pagada'),
            ('overdue', 'Vencida'),
            ('cancelled', 'Cancelada'),
        ],
        default='pending',
        verbose_name="Estado"
    )

    # Información de entrega
    delivery_person = models.CharField(max_length=100, blank=True, verbose_name="Persona que entrega")
    recipient_person = models.CharField(max_length=100, blank=True, verbose_name="Persona que recibe")
    delivery_notes = models.TextField(blank=True, verbose_name="Notas de entrega")

    # Usuario responsable
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices',
        verbose_name="Creada por"
    )

    # Notas generales
    notes = models.TextField(blank=True, verbose_name="Notas")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calcular valores automáticamente
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total_amount = self.subtotal + self.tax_amount

        # Generar número de factura si no existe
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        """Genera número único de factura"""
        import datetime
        today = datetime.date.today()
        base_number = f"FAC-{self.company.nit}-{today.strftime('%Y%m%d')}"

        # Buscar el último número del día
        last_invoice = Invoice.objects.filter(
            company=self.company,
            invoice_number__startswith=base_number
        ).order_by('-invoice_number').first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{base_number}-{new_num:03d}"

    def is_overdue(self):
        """Verifica si la factura está vencida"""
        if self.status == 'paid':
            return False
        return self.due_date < timezone.now().date()

    def days_overdue(self):
        """Calcula días de vencimiento"""
        if not self.is_overdue():
            return 0
        return (timezone.now().date() - self.due_date).days

    def __str__(self):
        return f"Factura {self.invoice_number}"

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-created_at']
        permissions = [
            ('can_manage_invoices', 'Puede gestionar facturas'),
            ('can_view_invoices', 'Puede ver facturas'),
        ]


class ActivityLog(models.Model):
    """
    Log de actividades del sistema para auditoría completa.
    """
    ACTION_CHOICES = [
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('client_create', 'Creación de cliente'),
        ('client_update', 'Actualización de cliente'),
        ('maquila_create', 'Creación de maquila'),
        ('maquila_update', 'Actualización de maquila'),
        ('toasting_start', 'Inicio de tostión'),
        ('toasting_complete', 'Tostión completada'),
        ('production_start', 'Inicio de producción'),
        ('production_complete', 'Producción completada'),
        ('invoice_create', 'Creación de factura'),
        ('invoice_payment', 'Pago de factura'),
        ('company_create', 'Creación de empresa'),
        ('company_suspend', 'Empresa suspendida'),
        ('company_activate', 'Empresa activada'),
        ('user_create', 'Creación de usuario'),
        ('user_update', 'Actualización de usuario'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities',
        verbose_name="Usuario"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities',
        verbose_name="Empresa"
    )
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name="Acción"
    )
    description = models.TextField(verbose_name="Descripción")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Fecha y hora")

    # Objetos relacionados (opcional)
    related_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        verbose_name="Pedido relacionado"
    )
    related_invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        verbose_name="Factura relacionada"
    )

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else "Usuario desconocido"
        company_name = self.company.name if self.company else "Empresa desconocida"
        return f"{user_name} - {self.get_action_display()} - {company_name} - {self.timestamp}"

    class Meta:
        verbose_name = "Log de Actividad"
        verbose_name_plural = "Logs de Actividad"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
