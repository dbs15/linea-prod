# 📋 Documentación de Usuario - Sistema de Maquilas de Café

## 🚀 Inicio Rápido

### 1. Acceso al Sistema
- **URL**: http://localhost:8000
- **Usuario de prueba**: admin
- **Contraseña**: admin123 (o la que configuraste)

### 2. Primeros Pasos
1. Accede al sistema con tus credenciales
2. Si eres Super Admin, crea una empresa primero
3. Crea usuarios para cada rol según necesites
4. Comienza a registrar pedidos

---

## 👥 Roles de Usuario y Funcionalidades

### 🔑 Super Administrador
**Acceso**: Control total del sistema
- ✅ Crear y gestionar empresas
- ✅ Ver todas las empresas del sistema
- ✅ Suspender/reactivar empresas
- ✅ Acceso al panel de administración Django

### 🏢 Administrador de Empresa
**Acceso**: Gestión completa de su empresa
- ✅ Ver métricas generales de la empresa
- ✅ Gestionar usuarios de la empresa
- ✅ Acceso a todos los módulos
- ✅ Ver reportes completos

### 📝 Auxiliar de Registro
**Acceso**: Solo módulo de registro
- ✅ Registrar nuevos clientes
- ✅ Crear pedidos de maquila
- ✅ Ver lista de pedidos registrados
- ✅ Buscar y gestionar clientes existentes

### 🔥 Auxiliar de Tostión
**Acceso**: Solo módulo de tostión
- ✅ Ver pedidos listos para tostar
- ✅ Registrar proceso de tostión
- ✅ Controlar parámetros técnicos
- ✅ Marcar tostión como completa

### 📦 Auxiliar de Producción
**Acceso**: Solo módulo de producción
- ✅ Ver pedidos terminados de tostar
- ✅ Registrar proceso de empaque
- ✅ Controlar calidad del producto
- ✅ Marcar producción como completa

### 💰 Auxiliar de Facturación
**Acceso**: Solo módulo de facturación
- ✅ Ver pedidos listos para facturar
- ✅ Generar facturas automáticamente
- ✅ Gestionar entregas
- ✅ Ver estado de pagos

---

## 📋 Guía de Uso por Módulo

### 🏢 Gestión de Empresas (Super Admin)

#### Crear Nueva Empresa
1. Ve al Dashboard
2. Haz clic en "Crear Empresa"
3. Completa el formulario:
   - **Nombre**: Nombre de la empresa
   - **NIT**: Número de identificación tributaria
   - **Dirección**: Dirección física
   - **Teléfono**: Número de contacto
   - **Email**: Correo electrónico
   - **Plan**: Básico, Premium o Enterprise
4. Haz clic en "Crear Empresa"

#### Gestionar Empresas Existentes
- En el Dashboard verás todas las empresas
- Usa los botones de acción para:
  - **Ver detalles**: Información completa
  - **Editar**: Modificar datos
  - **Suspender**: Desactivar temporalmente
  - **Reactivar**: Volver a activar

### 📝 Módulo de Registro

#### Crear un Nuevo Pedido
1. Ve a "Pedidos" → "Crear Pedido"
2. **Selecciona el tipo de cliente**:
   - **Cliente Existente**: Busca por nombre o documento
   - **Cliente Nuevo**: Completa todos los campos requeridos

3. **Información del Producto**:
   - Cantidad en KG
   - Tipo de café (Excelso, Supremo, Extra)
   - Precio por KG
   - Tipo de empaque
   - Detalles del empaque

4. **Información de Entrega**:
   - Método de entrega
   - Dirección de entrega
   - Fecha comprometida

5. **Cálculos Automáticos**:
   - El sistema calcula automáticamente el total
   - Verifica fechas válidas
   - Valida montos y cantidades

#### Gestionar Clientes
- **Buscar clientes**: Usa la barra de búsqueda
- **Ver detalles**: Historial de pedidos
- **Editar información**: Datos de contacto y dirección

### 🔥 Módulo de Tostión

#### Ver Pedidos Pendientes
- Lista de pedidos esperando tostión
- **Indicadores visuales**:
  - 🟢 Verde: Pedidos con proceso iniciado
  - 🔴 Rojo: Pedidos sin proceso
  - 📊 Estadísticas: Total, con proceso, sin proceso

#### Registrar Proceso de Tostión
1. Selecciona "Iniciar Tostión" en un pedido
2. **Recepción de Materia Prima**:
   - Cantidad recibida (se compara con pedido)
   - Diferencia automática

3. **Parámetros Técnicos**:
   - Temperatura (°C): 150-250°C
   - Tiempo (minutos): 5-30 min
   - Tipo de tueste: Claro, Medio, Oscuro

4. **Control de Calidad**:
   - Calidad del grano
   - Rendimiento estimado automático
   - Observaciones

5. **Completar**: El pedido pasa automáticamente al siguiente estado

### 📦 Módulo de Producción

#### Ver Pedidos para Producción
- Lista de pedidos terminados de tostar
- **Indicadores**:
  - Con proceso de producción
  - Sin proceso de producción
  - Estadísticas de progreso

#### Registrar Proceso de Producción
1. Selecciona "Iniciar Producción"
2. **Tipo de Proceso**:
   - Tipo de molienda
   - Detalles de empaque

3. **Resultados de Producción**:
   - Peso final en KG
   - Unidades producidas
   - Cálculos automáticos

4. **Control de Calidad**:
   - ✅ Verificación de peso
   - ✅ Empaque en buen estado
   - ✅ Etiquetado correcto
   - 📝 Notas adicionales

### 💰 Módulo de Facturación

#### Ver Pedidos para Facturar
- Lista de pedidos terminados de producir
- **Alertas**:
  - 🔴 Facturas vencidas
  - 📊 Estadísticas de facturación

#### Generar Factura
1. Selecciona "Facturar" en un pedido
2. **Información de Factura**:
   - Subtotal (calculado automáticamente)
   - Tasa de IVA
   - Fechas de emisión y vencimiento

3. **Información de Entrega**:
   - Persona que entrega
   - Persona que recibe
   - Notas de entrega

4. **Cálculos Automáticos**:
   - Total con IVA
   - Validaciones de fechas

---

## 🔄 Flujo Completo de un Pedido

```
1. 📝 REGISTRO
   └── Auxiliar Registro crea pedido

2. 🔥 TOSTIÓN
   └── Auxiliar Tostión procesa café

3. 📦 PRODUCCIÓN
   └── Auxiliar Producción empaca

4. 💰 FACTURACIÓN
   └── Auxiliar Facturación genera factura

5. ✅ ENTREGA
   └── Pedido completado
```

### Estados del Pedido
- **Registrado**: Pedido creado, esperando tostión
- **En Tostión**: Proceso de tostión iniciado
- **Tostión Completa**: Café tostado, esperando producción
- **En Producción**: Proceso de empaque iniciado
- **Listo para Facturar**: Producto terminado, esperando factura
- **Facturado**: Factura generada
- **Entregado**: Pedido completado

---

## 📊 Dashboard y Reportes

### Dashboard por Rol

#### Super Admin
- 📈 Número total de empresas
- 👥 Usuarios activos por empresa
- 💰 Ingresos totales del sistema
- 📋 Pedidos activos globales

#### Admin Empresa
- 📊 Métricas de la empresa
- 👤 Usuarios activos
- 📦 Pedidos en proceso
- 💵 Facturas pendientes

#### Auxiliar Registro
- 📝 Pedidos registrados hoy
- 👥 Clientes activos
- ⏰ Pedidos próximos a vencer

#### Auxiliar Tostión
- 🔥 Pedidos en tostión
- 📊 Rendimiento promedio
- ⚡ Eficiencia del proceso

#### Auxiliar Producción
- 📦 Pedidos en producción
- ✅ Controles de calidad
- 📈 Unidades producidas

#### Auxiliar Facturación
- 💰 Facturas generadas
- ⏰ Facturas por vencer
- 💳 Pagos pendientes

---

## ⚙️ Configuración y Mantenimiento

### Variables de Entorno (.env)
```bash
# Base de datos
DATABASE_URL=sqlite:///db.sqlite3

# Django
SECRET_KEY=tu-clave-secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (opcional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

### Comandos Útiles

#### Crear Super Usuario
```bash
python manage.py createsuperuser
```

#### Crear Empresa de Prueba
```bash
python manage.py shell -c "
from core.models import Company
Company.objects.create(
    name='Empresa de Prueba',
    nit='123456789',
    email='empresa@test.com',
    address='Dirección de prueba'
)
"
```

#### Ejecutar Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Recopilar Archivos Estáticos
```bash
python manage.py collectstatic
```

---

## 🔧 Solución de Problemas

### Problemas Comunes

#### ❌ Error de Login
- Verifica que el usuario esté activo
- Confirma que la empresa no esté suspendida
- Revisa las credenciales

#### ❌ No puedo acceder a un módulo
- Verifica tu rol de usuario
- Confirma que tengas permisos para esa función
- Contacta al Admin de Empresa

#### ❌ Error al crear pedido
- Verifica que todos los campos requeridos estén completos
- Confirma que las fechas sean válidas
- Revisa que los cálculos sean correctos

#### ❌ Problemas con formularios
- Asegúrate de que JavaScript esté habilitado
- Verifica la conexión a internet para AJAX
- Limpia el caché del navegador

### Logs y Debugging
- Los errores se muestran en la consola del navegador (F12)
- Revisa los logs del servidor en la terminal
- Para debugging avanzado, activa `DEBUG=True` en settings

---

## 📞 Soporte y Contacto

### Recursos de Ayuda
- 📖 **Documentación**: Este archivo
- 🐛 **Reportar Bugs**: Crear issue en el repositorio
- 💡 **Sugerencias**: Usar la sección de discusiones

### Contacto de Soporte
- **Email**: soporte@maquilas-cafe.com
- **Teléfono**: +57 123 456 7890
- **Horario**: Lunes a Viernes, 8:00 AM - 6:00 PM

---

## 🎯 Consejos y Mejores Prácticas

### Para una Mejor Experiencia
1. **Mantén los datos actualizados**: Información de clientes y productos
2. **Revisa regularmente**: Pedidos próximos a vencer
3. **Usa filtros**: Para encontrar información rápidamente
4. **Verifica cálculos**: Antes de guardar formularios
5. **Documenta procesos**: Usa las notas en formularios

### Optimización del Flujo
- **Asigna roles específicos**: Cada usuario solo lo necesario
- **Revisa diariamente**: Pedidos en cada etapa
- **Coordina equipos**: Comunicación entre auxiliares
- **Mantén backups**: Datos importantes seguros

### Seguridad
- **Cambia contraseñas regularmente**
- **No compartas credenciales**
- **Cierra sesión al terminar**
- **Reporta actividades sospechosas**

---

*Esta documentación se actualiza continuamente. Última actualización: Diciembre 2024*