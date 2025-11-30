from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import User, Order, Invoice, Client, Company, ToastingProcess, ProductionProcess

class Command(BaseCommand):
    help = 'Configura grupos de permisos y asigna usuarios a ellos según sus roles.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando configuración de permisos...'))

        # Definición de roles y sus permisos asociados
        # Los nombres de los permisos son 'app_label.can_do_something'
        permission_map = {
            'admin_company': {
                'group_name': 'Administradores de Empresa',
                'permissions': [
                    # Permisos generales de la app core
                    'add_client', 'change_client', 'delete_client', 'view_client',
                    'add_order', 'change_order', 'delete_order', 'view_order',
                    'add_toastingprocess', 'change_toastingprocess', 'delete_toastingprocess', 'view_toastingprocess',
                    'add_productionprocess', 'change_productionprocess', 'delete_productionprocess', 'view_productionprocess',
                    'add_invoice', 'change_invoice', 'delete_invoice', 'view_invoice',
                    'can_manage_orders', 'can_view_all_orders',
                    'can_manage_invoices', 'can_view_invoices',
                ]
            },
            'aux_registro': {
                'group_name': 'Auxiliares de Registro',
                'permissions': [
                    'add_client', 'change_client', 'view_client',
                    'add_order', 'change_order', 'view_order',
                    'can_manage_orders', # Para que puedan gestionar sus propias maquilas
                ]
            },
            'aux_tostion': {
                'group_name': 'Auxiliares de Tostión',
                'permissions': [
                    'view_order', # Necesita ver la maquila
                    'add_toastingprocess', 'change_toastingprocess', 'view_toastingprocess',
                ]
            },
            'aux_produccion': {
                'group_name': 'Auxiliares de Producción',
                'permissions': [
                    'view_order', # Necesita ver la maquila
                    'add_productionprocess', 'change_productionprocess', 'view_productionprocess',
                ]
            },
            'aux_facturacion': {
                'group_name': 'Auxiliares de Facturación',
                'permissions': [
                    'view_order', # Necesita ver la maquila para facturar
                    'add_invoice', 'change_invoice', 'view_invoice',
                    'can_manage_invoices', 'can_view_invoices',
                ]
            },
        }

        # Obtener ContentTypes una sola vez
        content_types = {
            'client': ContentType.objects.get_for_model(Client),
            'order': ContentType.objects.get_for_model(Order),
            'toastingprocess': ContentType.objects.get_for_model(ToastingProcess),
            'productionprocess': ContentType.objects.get_for_model(ProductionProcess),
            'invoice': ContentType.objects.get_for_model(Invoice),
        }

        # 1. Crear/Actualizar grupos y asignar permisos
        for role_key, role_data in permission_map.items():
            group_name = role_data['group_name']
            permissions_codenames = role_data['permissions']

            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group_name}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'Grupo "{group_name}" ya existe.'))

            # Limpiar permisos existentes del grupo para evitar duplicados o permisos antiguos
            group.permissions.clear()

            for perm_codename in permissions_codenames:
                # Los permisos personalizados se crean con la app_label directamente
                # Los permisos por defecto (add, change, delete, view) necesitan el ContentType
                if '_' in perm_codename: # Asume que es 'accion_modelo' o 'custom_perm_name'
                    app_label = 'core' # Todos nuestros modelos están en 'core'
                    model_name = None
                    for ct_name, ct_obj in content_types.items():
                        if perm_codename.endswith(ct_name): # check if codename ends with model_name (e.g. 'add_client')
                            model_name = ct_name
                            break
                    
                    if model_name:
                        perm_codename_full = f'{perm_codename}'
                    else: # Es un permiso personalizado como 'can_manage_orders'
                        perm_codename_full = f'{perm_codename}'

                    try:
                        # Intentar obtener el permiso por su codename completo (app_label.codename)
                        permission = Permission.objects.get(codename=perm_codename, content_type__app_label=app_label)
                        group.permissions.add(permission)
                        self.stdout.write(self.style.HTTP_INFO(f'  Permiso "{perm_codename}" asignado al grupo "{group_name}".'))
                    except Permission.DoesNotExist:
                        self.stderr.write(self.style.ERROR(f'  ERROR: Permiso "{perm_codename}" no encontrado para {app_label}. Ignorando.'))
                else:
                    self.stderr.write(self.style.ERROR(f'  ERROR: Formato de codename inesperado: {perm_codename}. Ignorando.'))


        # 2. Asignar usuarios a los grupos
        for user in User.objects.all():
            if user.role in permission_map:
                group_name = permission_map[user.role]['group_name']
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.clear()  # Limpiar grupos existentes para evitar duplicados
                    user.groups.add(group)
                    self.stdout.write(self.style.SUCCESS(f'Usuario "{user.username}" asignado al grupo "{group_name}".'))
                except Group.DoesNotExist:
                    self.stderr.write(self.style.ERROR(f'ERROR: El grupo "{group_name}" no existe para asignar al usuario {user.username}.'))
            elif user.role == 'super_admin':
                self.stdout.write(self.style.WARNING(f'Usuario "{user.username}" es super_admin y no se le asignan grupos de permisos.'))
            else:
                self.stdout.write(self.style.WARNING(f'Usuario "{user.username}" tiene un rol "{user.role}" sin configuración de permisos.'))

        self.stdout.write(self.style.SUCCESS('Configuración de permisos finalizada.'))
