#!/usr/bin/env python
"""
Script para crear datos de prueba en el sistema de maquilas de café.
Ejecutar después de las migraciones: python crear_datos_prueba.py
"""

import os
import sys
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maquila_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Company, Client, Order, Invoice

User = get_user_model()

def crear_datos_prueba():
    print("🚀 Creando datos de prueba...")

    # 1. Crear empresas de prueba
    print("🏢 Creando empresas...")
    empresa1, created1 = Company.objects.get_or_create(
        nit="901234567",
        defaults={
            'name': "Tostadora El Cafetal",
            'slug': "tostadora-el-cafetal",
            'address': "Calle 123 #45-67, Bogotá",
            'phone': "+57 123 456 7890",
            'email': "info@elcafetal.com",
            'plan': "premium"
        }
    )

    empresa2, created2 = Company.objects.get_or_create(
        nit="902345678",
        defaults={
            'name': "Café Don Pedro",
            'slug': "cafe-don-pedro",
            'address': "Carrera 89 #12-34, Medellín",
            'phone': "+57 234 567 8901",
            'email': "contacto@donpedro.com",
            'plan': "basic"
        }
    )

    print(f"✅ Empresas creadas: {empresa1.name}, {empresa2.name}")

    # 2. Crear usuarios para cada empresa y rol
    print("👥 Creando usuarios...")

    # Super Admin
    super_admin = User.objects.create_superuser(
        username="superadmin",
        email="superadmin@test.com",
        password="admin123",
        first_name="Super",
        last_name="Administrador"
    )
    # Set the role for our custom role system
    super_admin.role = "super_admin"
    super_admin.is_staff = True  # Ensure staff status for admin access
    super_admin.save()
    print(f"✅ Super Admin creado: {super_admin.username}")

    # Usuarios para Empresa 1
    admin_empresa1 = User.objects.create_user(
        username="admin_cafetal",
        email="admin@elcafetal.com",
        password="admin123",
        first_name="Juan",
        last_name="Pérez",
        role="admin_company",
        company=empresa1
    )

    registro_empresa1 = User.objects.create_user(
        username="registro_cafetal",
        email="registro@elcafetal.com",
        password="user123",
        first_name="María",
        last_name="García",
        role="aux_registro",
        company=empresa1
    )

    tostion_empresa1 = User.objects.create_user(
        username="tostion_cafetal",
        email="tostion@elcafetal.com",
        password="user123",
        first_name="Carlos",
        last_name="Rodríguez",
        role="aux_tostion",
        company=empresa1
    )

    produccion_empresa1 = User.objects.create_user(
        username="produccion_cafetal",
        email="produccion@elcafetal.com",
        password="user123",
        first_name="Ana",
        last_name="Martínez",
        role="aux_produccion",
        company=empresa1
    )

    facturacion_empresa1 = User.objects.create_user(
        username="facturacion_cafetal",
        email="facturacion@elcafetal.com",
        password="user123",
        first_name="Luis",
        last_name="Sánchez",
        role="aux_facturacion",
        company=empresa1
    )

    print(f"✅ Usuarios creados para {empresa1.name}")

    # Usuarios para Empresa 2
    admin_empresa2 = User.objects.create_user(
        username="admin_donpedro",
        email="admin@donpedro.com",
        password="admin123",
        first_name="Pedro",
        last_name="López",
        role="admin_company",
        company=empresa2
    )

    print(f"✅ Usuarios creados para {empresa2.name}")

    # 3. Crear clientes de prueba
    print("👥 Creando clientes...")

    cliente1 = Client.objects.create(
        company=empresa1,
        first_name="Don",
        last_name="Juan",
        document_type="cc",
        document_number="12345678",
        phone="+57 300 123 4567",
        email="donjuan@email.com",
        address="Finca El Roble, Municipio X"
    )

    cliente2 = Client.objects.create(
        company=empresa1,
        first_name="Doña",
        last_name="María",
        document_type="cc",
        document_number="87654321",
        phone="+57 301 987 6543",
        email="dona maria@email.com",
        address="Hacienda La Esperanza, Municipio Y"
    )

    cliente3 = Client.objects.create(
        company=empresa2,
        first_name="Señor",
        last_name="Carlos",
        document_type="nit",
        document_number="9012345678",
        phone="+57 302 456 7890",
        email="carlos@email.com",
        address="Finca Los Andes, Municipio Z"
    )

    print(f"✅ Clientes creados: {cliente1.full_name}, {cliente2.full_name}, {cliente3.full_name}")

    # 4. Crear pedidos de prueba en diferentes estados
    print("📦 Creando pedidos de prueba...")

    # Pedido registrado (recién creado)
    pedido1 = Order.objects.create(
        company=empresa1,
        client=cliente1,
        order_number="PED-CAFETAL-001",
        quantity_kg=Decimal("500.00"),
        coffee_type="excelso",
        price_per_kg=Decimal("15000.00"),
        packaging_type="Bolsas de 500g",
        packaging_details="Empaque al vacío, 20 bolsas por caja",
        delivery_method="retiro",
        delivery_address="Bodega principal El Cafetal",
        committed_date=timezone.now().date() + timedelta(days=5),
        created_by=registro_empresa1
    )

    # Pedido en tostión
    pedido2 = Order.objects.create(
        company=empresa1,
        client=cliente2,
        order_number="PED-CAFETAL-002",
        quantity_kg=Decimal("300.00"),
        coffee_type="supremo",
        price_per_kg=Decimal("18000.00"),
        packaging_type="Bolsas de 250g",
        packaging_details="Empaque tradicional, 12 bolsas por caja",
        delivery_method="envio",
        delivery_address="Tienda Don Juan, Centro",
        committed_date=timezone.now().date() + timedelta(days=3),
        state="in_toasting",
        created_by=registro_empresa1
    )

    # Pedido tostión completa
    pedido3 = Order.objects.create(
        company=empresa1,
        client=cliente1,
        order_number="PED-CAFETAL-003",
        quantity_kg=Decimal("200.00"),
        coffee_type="extra",
        price_per_kg=Decimal("22000.00"),
        packaging_type="Latas de 500g",
        packaging_details="Latas decorativas, 10 unidades por caja",
        delivery_method="retiro",
        delivery_address="Bodega principal El Cafetal",
        committed_date=timezone.now().date() + timedelta(days=7),
        state="toasting_complete",
        final_quantity_kg=Decimal("190.00"),
        yield_percentage=Decimal("95.00"),
        created_by=registro_empresa1
    )

    # Pedido listo para facturar
    pedido4 = Order.objects.create(
        company=empresa1,
        client=cliente2,
        order_number="PED-CAFETAL-004",
        quantity_kg=Decimal("400.00"),
        coffee_type="excelso",
        price_per_kg=Decimal("16000.00"),
        packaging_type="Bolsas de 1kg",
        packaging_details="Empaque premium, 8 bolsas por caja",
        delivery_method="envio",
        delivery_address="Supermercado La Esperanza",
        committed_date=timezone.now().date() + timedelta(days=2),
        state="ready_for_billing",
        final_quantity_kg=Decimal("380.00"),
        yield_percentage=Decimal("95.00"),
        created_by=registro_empresa1
    )

    print(f"✅ Pedidos creados: {pedido1.order_number}, {pedido2.order_number}, {pedido3.order_number}, {pedido4.order_number}")

    # 5. Crear factura de prueba
    print("💰 Creando factura de prueba...")

    factura1 = Invoice.objects.create(
        company=empresa1,
        order=pedido4,
        invoice_number="FAC-CAFETAL-001",
        issue_date=timezone.now().date(),
        due_date=timezone.now().date() + timedelta(days=30),
        total_amount=pedido4.total_amount,
        status="pending",
        created_by=facturacion_empresa1
    )

    print(f"✅ Factura creada: {factura1.invoice_number}")

    # 6. Resumen final
    print("\n" + "="*60)
    print("🎉 DATOS DE PRUEBA CREADOS EXITOSAMENTE")
    print("="*60)
    print("\n📊 RESUMEN:")
    print(f"🏢 Empresas: {Company.objects.count()}")
    print(f"👥 Usuarios: {User.objects.count()}")
    print(f"👨‍🌾 Clientes: {Client.objects.count()}")
    print(f"📦 Pedidos: {Order.objects.count()}")
    print(f"💰 Facturas: {Invoice.objects.count()}")

    print("\n🔑 USUARIOS DE PRUEBA:")
    print("Super Admin: superadmin / admin123")
    print("Admin El Cafetal: admin_cafetal / admin123")
    print("Registro El Cafetal: registro_cafetal / user123")
    print("Tostión El Cafetal: tostion_cafetal / user123")
    print("Producción El Cafetal: produccion_cafetal / user123")
    print("Facturación El Cafetal: facturacion_cafetal / user123")
    print("Admin Don Pedro: admin_donpedro / admin123")

    print("\n🌐 ACCESO AL SISTEMA:")
    print("http://localhost:8000")
    print("Panel de administración: http://localhost:8000/admin/")

    print("\n📖 DOCUMENTACIÓN:")
    print("Ver DOCUMENTACION_USUARIO.md para guía completa")

    print("="*60)

if __name__ == "__main__":
    try:
        crear_datos_prueba()
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        sys.exit(1)