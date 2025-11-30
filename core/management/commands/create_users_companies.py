from django.core.management.base import BaseCommand
from core.models import Company, User
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError


class Command(BaseCommand):
    help = 'Crea empresas y usuarios de prueba con roles y permisos específicos.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando creación de empresas y usuarios...'))

        # Crear empresas
        try:
            cafetal, created = Company.objects.get_or_create(
                name='Tostadora El Cafetal',
                defaults={
                    'slug': 'tostadora-el-cafetal',
                    'nit': '900000001-1',
                    'phone': '123456789',
                    'email': 'info@cafetal.com',
                    'address': 'Calle Falsa 123',
                    'city': 'Bogotá'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Empresa "Tostadora El Cafetal" creada.'))
            else:
                self.stdout.write(self.style.WARNING('Empresa "Tostadora El Cafetal" ya existe.'))

            donpedro, created = Company.objects.get_or_create(
                name='Café Don Pedro',
                defaults={
                    'slug': 'cafe-don-pedro',
                    'nit': '900000002-2',
                    'phone': '987654321',
                    'email': 'contacto@donpedro.com',
                    'address': 'Avenida Siempre Viva 456',
                    'city': 'Medellín'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Empresa "Café Don Pedro" creada.'))
            else:
                self.stdout.write(self.style.WARNING('Empresa "Café Don Pedro" ya existe.'))

        except IntegrityError as e:
            self.stderr.write(self.style.ERROR(f'Error al crear empresas: {e}'))
            return

        # Crear usuarios para Tostadora El Cafetal
        users_to_create = [
            ('admin_cafetal', 'Admin', 'Cafetal', 'admin@cafetal.com', 'admin123', 'admin_company', cafetal),
            ('registro_cafetal', 'Registro', 'Cafetal', 'registro@cafetal.com', 'user123', 'aux_registro', cafetal),
            ('tostion_cafetal', 'Tostion', 'Cafetal', 'tostion@cafetal.com', 'user123', 'aux_tostion', cafetal),
            ('produccion_cafetal', 'Produccion', 'Cafetal', 'produccion@cafetal.com', 'user123', 'aux_produccion', cafetal),
            ('facturacion_cafetal', 'Facturacion', 'Cafetal', 'facturacion@cafetal.com', 'user123', 'aux_facturacion', cafetal),
            ('admin_donpedro', 'Admin', 'Don Pedro', 'admin@donpedro.com', 'admin123', 'admin_company', donpedro),
        ]

        for username, first_name, last_name, email, password, role, company in users_to_create:
            try:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'password': make_password(password),
                        'role': role,
                        'company': company
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Usuario "{username}" creado con rol {role}.'))
                else:
                    # Si el usuario ya existe, actualizamos la contraseña y el rol por si acaso.
                    if user.role != role or not user.check_password(password):
                        user.role = role
                        user.password = make_password(password)
                        user.save()
                        self.stdout.write(self.style.WARNING(f'Usuario "{username}" ya existe. Rol y contraseña actualizados.'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Usuario "{username}" ya existe y está actualizado.'))

            except IntegrityError as e:
                self.stderr.write(self.style.ERROR(f'Error al crear o actualizar el usuario {username}: {e}'))

        self.stdout.write(self.style.SUCCESS('Proceso de creación de empresas y usuarios finalizado.'))
