from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    Company, User, Client, Order, Invoice,
    ToastingProcess, ProductionProcess
)


class LoginForm(AuthenticationForm):
    """
    Formulario de login personalizado con estilos Tailwind CSS.
    """
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Nombre de usuario',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Contraseña',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar labels
        self.fields['username'].label = 'Usuario'
        self.fields['password'].label = 'Contraseña'


class CompanyForm(forms.ModelForm):
    """
    Formulario completo para empresas con validaciones.
    """
    class Meta:
        model = Company
        fields = [
            'name', 'slug', 'nit', 'phone', 'email', 'address', 'city',
            'status', 'plan', 'billing_email'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre de la empresa'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'slug-unico'
            }),
            'nit': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Número de identificación tributaria'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '+57 300 123 4567'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'contacto@empresa.com'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ciudad'
            }),
            'billing_email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'facturacion@empresa.com'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'plan': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }

    def clean_slug(self):
        """Validar que el slug sea único."""
        slug = self.cleaned_data.get('slug')
        if slug:
            # Convertir a lowercase y reemplazar espacios
            slug = slug.lower().replace(' ', '-')
            # Verificar unicidad
            queryset = Company.objects.filter(slug=slug)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('Este slug ya está en uso.')
        return slug

    def clean_nit(self):
        """Validar que el NIT sea único."""
        nit = self.cleaned_data.get('nit')
        if nit:
            queryset = Company.objects.filter(nit=nit)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('Este NIT ya está registrado.')
        return nit


class UserForm(forms.ModelForm):
    """
    Formulario personalizado para usuarios con validación de email único.
    """
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Contraseña'
        }),
        required=False
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Confirmar contraseña'
        }),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'company', 'phone', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre de usuario'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombres'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Apellidos'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'usuario@empresa.com'
            }),
            'role': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'company': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '+57 300 123 4567'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
        }

    def clean_email(self):
        """Validar que el email sea único."""
        email = self.cleaned_data.get('email')
        if email:
            queryset = User.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('Este email ya está registrado.')
        return email

    def clean(self):
        """Validar contraseñas si se proporcionan."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 or password2:
            if password1 != password2:
                raise ValidationError('Las contraseñas no coinciden.')

        return cleaned_data

    def save(self, commit=True):
        """Guardar usuario con contraseña si se proporciona."""
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class ClienteForm(forms.ModelForm):
    """
    Formulario para clientes con validaciones y estilos Tailwind.
    Campos obligatorios: nombre completo, teléfono, dirección, email.
    """
    class Meta:
        model = Client
        fields = [
            'first_name', 'last_name', 'document_type', 'document_number',
            'phone', 'email', 'address', 'city', 'client_type', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombres',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Apellidos',
                'required': True
            }),
            'document_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'document_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Número de documento',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '+57 300 123 4567',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'cliente@email.com',
                'required': True
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Dirección completa',
                'required': True
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ciudad'
            }),
            'client_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 2,
                'placeholder': 'Notas adicionales'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Hacer campos obligatorios explícitamente
        required_fields = ['first_name', 'last_name', 'document_number', 'phone', 'email', 'address']
        for field_name in required_fields:
            self.fields[field_name].required = True

    def clean_document_number(self):
        """Validar que el documento sea único por empresa."""
        document_number = self.cleaned_data.get('document_number')
        if document_number:
            queryset = Client.objects.filter(document_number=document_number)
            # Excluir el cliente actual si estamos editando
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('Este número de documento ya está registrado.')
        return document_number

    def save(self, commit=True):
        # Asignar empresa del usuario ANTES de llamar a super().save()
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.instance.company = self.user.company

        client = super().save(commit=False)

        # Asegurar que la empresa esté asignada
        if not client.company and self.user and hasattr(self.user, 'company'):
            client.company = self.user.company

        if commit:
            client.save()
        return client


class PedidoForm(forms.ModelForm):
    """
    Formulario para pedidos con selección de cliente existente.
    Los clientes deben crearse previamente desde el módulo de gestión de clientes.
    """
    # Campo para seleccionar cliente existente (requerido)
    client = forms.ModelChoiceField(
        queryset=Client.objects.none(),
        required=True,
        empty_label="Seleccionar cliente",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )

    class Meta:
        model = Order
        fields = [
            'quantity_kg', 'coffee_type', 'price_per_kg', 'packaging_type',
            'packaging_details', 'delivery_method', 'delivery_address', 'committed_date'
        ]
        # El campo 'client' se define fuera del Meta porque es un ModelChoiceField personalizado
        widgets = {
            'quantity_kg': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'coffee_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'price_per_kg': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'packaging_type': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Tipo de empaque'
            }),
            'packaging_details': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 2,
                'placeholder': 'Detalles del empaque'
            }),
            'delivery_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 2,
                'placeholder': 'Dirección de entrega'
            }),
            'committed_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filtrar clientes por empresa del usuario
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['client'].queryset = Client.objects.filter(
                company=self.user.company,
                is_active=True  # Solo clientes activos
            ).order_by('first_name', 'last_name')

    def clean(self):
        cleaned_data = super().clean()

        # Validar que la fecha comprometida no sea en el pasado
        committed_date = cleaned_data.get('committed_date')
        if committed_date and committed_date < timezone.now().date():
            raise ValidationError('La fecha comprometida no puede ser en el pasado.')

        return cleaned_data

    def clean_client(self):
        """Validar que el cliente seleccionado pertenezca a la empresa del usuario."""
        client = self.cleaned_data.get('client')
        if client:
            # Verificar que el cliente pertenezca a la empresa del usuario
            if self.user and hasattr(self.user, 'company') and self.user.company:
                if client.company != self.user.company:
                    raise ValidationError('El cliente seleccionado no pertenece a tu empresa.')
            else:
                raise ValidationError('No tienes una empresa asignada.')
        return client

    def save(self, commit=True):
        order = super().save(commit=False)

        # Asignar empresa del usuario
        if self.user and hasattr(self.user, 'company'):
            order.company = self.user.company

        # Asignar cliente desde el campo del formulario
        if 'client' in self.cleaned_data:
            order.client = self.cleaned_data['client']

        # Asignar usuario creador
        order.created_by = self.user

        if commit:
            order.save()
        return order


class ProcesoTostionForm(forms.ModelForm):
    """
    Formulario para proceso de tostión paso a paso con validaciones técnicas.
    """

    # Campos para recepción
    received_quantity_kg = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )

    # Campos para configuración inicial
    toasting_equipment = forms.ChoiceField(
        choices=ToastingProcess.TOASTING_EQUIPMENT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )

    initial_temperature_celsius = forms.DecimalField(
        max_digits=5,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '150',
            'min': '100',
            'max': '200'
        })
    )

    target_temperature_celsius = forms.DecimalField(
        max_digits=5,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '200',
            'min': '150',
            'max': '250'
        })
    )

    estimated_time_minutes = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '15',
            'min': '5',
            'max': '60'
        })
    )

    roast_type = forms.ChoiceField(
        choices=[
            ('light', 'Claro'),
            ('medium', 'Medio'),
            ('dark', 'Oscuro'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )

    # Campos para monitoreo
    current_temperature_celsius = forms.DecimalField(
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '200',
            'min': '100',
            'max': '300',
            'step': '0.1'
        })
    )

    current_humidity_percentage = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '5.00',
            'min': '0',
            'max': '20',
            'step': '0.01'
        })
    )

    # Campos para finalización
    processed_quantity_kg = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )

    final_grain_quality = forms.ChoiceField(
        choices=[
            ('excellent', 'Excelente'),
            ('good', 'Buena'),
            ('regular', 'Regular'),
            ('poor', 'Deficiente'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )

    final_quality_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 3,
            'placeholder': 'Observaciones finales sobre la calidad del grano'
        })
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 2,
            'placeholder': 'Notas adicionales del proceso'
        })
    )

    class Meta:
        model = ToastingProcess
        fields = [
            'received_quantity_kg', 'toasting_equipment', 'initial_temperature_celsius',
            'target_temperature_celsius', 'estimated_time_minutes', 'roast_type',
            'current_temperature_celsius', 'current_humidity_percentage',
            'processed_quantity_kg', 'final_grain_quality', 'final_quality_notes', 'notes'
        ]

    def __init__(self, *args, **kwargs):
        self.step = kwargs.pop('step', 'reception')
        super().__init__(*args, **kwargs)

        # Configurar campos requeridos según el paso
        if self.step == 'reception':
            self.fields['received_quantity_kg'].required = True
        elif self.step == 'setup':
            for field in ['toasting_equipment', 'initial_temperature_celsius', 'target_temperature_celsius', 'estimated_time_minutes', 'roast_type']:
                self.fields[field].required = True
        elif self.step == 'monitoring':
            # Campos opcionales para actualizaciones
            pass
        elif self.step == 'completion':
            for field in ['processed_quantity_kg', 'final_grain_quality']:
                self.fields[field].required = True

    def clean_initial_temperature_celsius(self):
        """Validar temperatura inicial."""
        temperature = self.cleaned_data.get('initial_temperature_celsius')
        if temperature and (temperature < 100 or temperature > 200):
            raise ValidationError('La temperatura inicial debe estar entre 100°C y 200°C.')
        return temperature

    def clean_target_temperature_celsius(self):
        """Validar temperatura objetivo."""
        temperature = self.cleaned_data.get('target_temperature_celsius')
        if temperature and (temperature < 150 or temperature > 250):
            raise ValidationError('La temperatura objetivo debe estar entre 150°C y 250°C.')
        return temperature

    def clean_estimated_time_minutes(self):
        """Validar tiempo estimado."""
        time_minutes = self.cleaned_data.get('estimated_time_minutes')
        if time_minutes and (time_minutes < 5 or time_minutes > 60):
            raise ValidationError('El tiempo estimado debe estar entre 5 y 60 minutos.')
        return time_minutes

    def clean_current_temperature_celsius(self):
        """Validar temperatura actual."""
        temperature = self.cleaned_data.get('current_temperature_celsius')
        if temperature and (temperature < 100 or temperature > 300):
            raise ValidationError('La temperatura actual debe estar entre 100°C y 300°C.')
        return temperature

    def clean_current_humidity_percentage(self):
        """Validar humedad."""
        humidity = self.cleaned_data.get('current_humidity_percentage')
        if humidity and (humidity < 0 or humidity > 20):
            raise ValidationError('La humedad debe estar entre 0% y 20%.')
        return humidity


class ProcesoProduccionForm(forms.ModelForm):
    """
    Formulario para proceso de producción con controles de calidad.
    """
    class Meta:
        model = ProductionProcess
        fields = [
            'process_type', 'grinding_type', 'packaging_details',
            'final_weight_kg', 'units_produced', 'weight_check',
            'packaging_check', 'labeling_check', 'notes'
        ]
        widgets = {
            'process_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'grinding_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'packaging_details': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Detalles del empaque final'
            }),
            'final_weight_kg': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'units_produced': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0',
                'min': '1'
            }),
            'weight_check': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'packaging_check': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'labeling_check': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 2,
                'placeholder': 'Notas del proceso'
            }),
        }


class FacturaForm(forms.ModelForm):
    """
    Formulario para facturas con cálculos automáticos de totales.
    """
    class Meta:
        model = Invoice
        fields = [
            'subtotal', 'tax_rate', 'issue_date', 'due_date',
            'delivery_person', 'recipient_person', 'delivery_notes', 'notes'
        ]
        widgets = {
            'subtotal': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01',
                'readonly': True
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '19.00',
                'step': '0.01',
                'value': '19.00'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'delivery_person': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre de quien entrega'
            }),
            'recipient_person': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nombre de quien recibe'
            }),
            'delivery_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 2,
                'placeholder': 'Notas de entrega'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 2,
                'placeholder': 'Notas adicionales'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si hay una instancia, poblar el subtotal
        if self.instance and self.instance.pk:
            self.fields['subtotal'].initial = self.instance.order.total_amount

    def clean_due_date(self):
        """Validar que la fecha de vencimiento sea posterior a la de emisión."""
        due_date = self.cleaned_data.get('due_date')
        issue_date = self.cleaned_data.get('issue_date')

        if due_date and issue_date and due_date <= issue_date:
            raise ValidationError('La fecha de vencimiento debe ser posterior a la fecha de emisión.')
        return due_date