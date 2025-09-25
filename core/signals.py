from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.apps import apps


@receiver(post_save, sender='core.Order')
def order_status_changed(sender, instance, created, **kwargs):
    """
    Maneja cambios de estado en pedidos y envía notificaciones.
    """
    ActivityLog = apps.get_model('core', 'ActivityLog')

    if created:
        # Nuevo pedido creado
        ActivityLog.objects.create(
            user=instance.created_by,
            company=instance.company,
            action='order_create',
            description=f'Nuevo pedido creado: {instance.order_number}',
            ip_address='system',
            related_order=instance
        )

        # Notificar al cliente
        send_order_confirmation_email(instance)

    else:
        # Verificar si el estado cambió
        if hasattr(instance, '_original_state') and instance._original_state != instance.state:
            # Estado cambió
            action_map = {
                'in_toasting': 'toasting_start',
                'toasting_complete': 'toasting_complete',
                'in_production': 'production_start',
                'ready_for_billing': 'production_complete',
                'billed': 'invoice_create',
                'delivered': 'order_delivered',
            }

            action = action_map.get(instance.state, 'order_update')

            # Determinar usuario responsable
            user_field_map = {
                'in_toasting': 'toasted_by',
                'toasting_complete': 'toasted_by',
                'in_production': 'produced_by',
                'ready_for_billing': 'produced_by',
                'billed': 'billed_by',
                'delivered': 'delivered_by',
            }

            responsible_user = getattr(instance, user_field_map.get(instance.state, 'created_by'), None)

            ActivityLog.objects.create(
                user=responsible_user,
                company=instance.company,
                action=action,
                description=f'Pedido {instance.order_number} cambió a estado: {instance.get_state_display()}',
                ip_address='system',
                related_order=instance
            )

            # Notificaciones específicas por estado
            if instance.state == 'ready_for_billing':
                notify_billing_team(instance)
            elif instance.state == 'billed':
                send_invoice_ready_email(instance)
            elif instance.state == 'delivered':
                send_delivery_confirmation_email(instance)


@receiver(pre_save, sender='core.Order')
def track_order_state_change(sender, instance, **kwargs):
    """
    Rastrea el estado anterior del pedido para detectar cambios.
    """
    Order = apps.get_model('core', 'Order')
    if instance.pk:
        try:
            original = Order.objects.get(pk=instance.pk)
            instance._original_state = original.state
        except Order.DoesNotExist:
            instance._original_state = None
    else:
        instance._original_state = None


@receiver(post_save, sender='core.Invoice')
def invoice_created_or_updated(sender, instance, created, **kwargs):
    """
    Maneja creación y actualizaciones de facturas.
    """
    ActivityLog = apps.get_model('core', 'ActivityLog')

    if created:
        ActivityLog.objects.create(
            user=instance.created_by,
            company=instance.company,
            action='invoice_create',
            description=f'Factura creada: {instance.invoice_number}',
            ip_address='system',
            related_invoice=instance
        )

        # Notificar al cliente sobre la factura
        send_invoice_created_email(instance)

    else:
        # Verificar cambios de estado
        if hasattr(instance, '_original_status') and instance._original_status != instance.status:
            if instance.status == 'paid':
                ActivityLog.objects.create(
                    user=instance.created_by,
                    company=instance.company,
                    action='invoice_payment',
                    description=f'Factura pagada: {instance.invoice_number}',
                    ip_address='system',
                    related_invoice=instance
                )
                send_payment_confirmation_email(instance)


@receiver(pre_save, sender='core.Invoice')
def track_invoice_status_change(sender, instance, **kwargs):
    """
    Rastrea el estado anterior de la factura.
    """
    Invoice = apps.get_model('core', 'Invoice')
    if instance.pk:
        try:
            original = Invoice.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Invoice.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None


@receiver(post_save, sender='core.ToastingProcess')
def toasting_process_events(sender, instance, created, **kwargs):
    """
    Maneja eventos del proceso de tostión.
    """
    ActivityLog = apps.get_model('core', 'ActivityLog')
    if created:
        ActivityLog.objects.create(
            user=instance.processed_by,
            company=instance.order.company,
            action='toasting_start',
            description=f'Proceso de tostión iniciado para pedido {instance.order.order_number}',
            ip_address='system',
            related_order=instance.order
        )


@receiver(post_save, sender='core.ProductionProcess')
def production_process_events(sender, instance, created, **kwargs):
    """
    Maneja eventos del proceso de producción.
    """
    ActivityLog = apps.get_model('core', 'ActivityLog')
    if created:
        ActivityLog.objects.create(
            user=instance.processed_by,
            company=instance.order.company,
            action='production_start',
            description=f'Proceso de producción iniciado para pedido {instance.order.order_number}',
            ip_address='system',
            related_order=instance.order
        )


@receiver(post_save, sender='core.Company')
def company_events(sender, instance, created, **kwargs):
    """
    Maneja eventos de empresas.
    """
    ActivityLog = apps.get_model('core', 'ActivityLog')
    if created:
        ActivityLog.objects.create(
            user=None,  # Sistema
            company=instance,
            action='company_create',
            description=f'Empresa creada: {instance.name}',
            ip_address='system'
        )


@receiver(post_save, sender='core.User')
def user_events(sender, instance, created, **kwargs):
    """
    Maneja eventos de usuarios.
    """
    ActivityLog = apps.get_model('core', 'ActivityLog')
    if created:
        ActivityLog.objects.create(
            user=None,  # Sistema
            company=getattr(instance, 'company', None),
            action='user_create',
            description=f'Usuario creado: {instance.get_full_name()}',
            ip_address='system'
        )


# Funciones de envío de emails

def send_order_confirmation_email(order):
    """
    Envía email de confirmación de pedido al cliente.
    """
    if not order.client.email:
        return

    subject = f'Confirmación de Pedido - {order.order_number}'
    context = {
        'order': order,
        'client': order.client,
        'company': order.company,
    }

    html_message = render_to_string('emails/order_confirmation.html', context)
    plain_message = render_to_string('emails/order_confirmation.txt', context)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.client.email],
            html_message=html_message,
            fail_silently=True
        )
    except Exception as e:
        # Log error but don't break the flow
        print(f"Error sending order confirmation email: {e}")


def notify_billing_team(order):
    """
    Notifica al equipo de facturación que hay un pedido listo.
    """
    billing_users = User.objects.filter(
        company=order.company,
        role='aux_facturacion'
    )

    if billing_users.exists():
        subject = f'Pedido Listo para Facturar - {order.order_number}'
        context = {
            'order': order,
            'company': order.company,
        }

        html_message = render_to_string('emails/billing_notification.html', context)
        plain_message = render_to_string('emails/billing_notification.txt', context)

        recipient_list = [user.email for user in billing_users if user.email]

        if recipient_list:
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_list,
                    html_message=html_message,
                    fail_silently=True
                )
            except Exception as e:
                print(f"Error sending billing notification: {e}")


def send_invoice_created_email(invoice):
    """
    Envía email al cliente cuando se crea la factura.
    """
    if not invoice.order.client.email:
        return

    subject = f'Factura Disponible - {invoice.invoice_number}'
    context = {
        'invoice': invoice,
        'order': invoice.order,
        'client': invoice.order.client,
        'company': invoice.company,
    }

    html_message = render_to_string('emails/invoice_created.html', context)
    plain_message = render_to_string('emails/invoice_created.txt', context)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invoice.order.client.email],
            html_message=html_message,
            fail_silently=True
        )
    except Exception as e:
        print(f"Error sending invoice created email: {e}")


def send_delivery_confirmation_email(order):
    """
    Envía email de confirmación de entrega al cliente.
    """
    if not order.client.email:
        return

    subject = f'Pedido Entregado - {order.order_number}'
    context = {
        'order': order,
        'client': order.client,
        'company': order.company,
        'invoice': getattr(order, 'invoice', None),
    }

    html_message = render_to_string('emails/delivery_confirmation.html', context)
    plain_message = render_to_string('emails/delivery_confirmation.txt', context)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.client.email],
            html_message=html_message,
            fail_silently=True
        )
    except Exception as e:
        print(f"Error sending delivery confirmation email: {e}")


def send_payment_confirmation_email(invoice):
    """
    Envía email de confirmación de pago al cliente.
    """
    if not invoice.order.client.email:
        return

    subject = f'Pago Confirmado - Factura {invoice.invoice_number}'
    context = {
        'invoice': invoice,
        'order': invoice.order,
        'client': invoice.order.client,
        'company': invoice.company,
    }

    html_message = render_to_string('emails/payment_confirmation.html', context)
    plain_message = render_to_string('emails/payment_confirmation.txt', context)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invoice.order.client.email],
            html_message=html_message,
            fail_silently=True
        )
    except Exception as e:
        print(f"Error sending payment confirmation email: {e}")