# Sistema de Maquilas de Café

Sistema SaaS para gestión de maquilas de café con multi-tenancy, roles de usuario y flujo completo de pedidos.

## Arquitectura del Sistema

```mermaid
graph TB
    subgraph "Capa de Presentación (Frontend)"
        A[Usuario Web] --> B[Django Templates]
        B --> C[CSS/JS - Tailwind CSS]
    end

    subgraph "Capa de Aplicación (Backend)"
        D[Django Views/Controllers] --> E[Django Models]
        D --> F[Django Auth & Guardian]
        D --> G[FSM para Estados de Pedido]
        D --> H[Sistema de Notificaciones Email]
    end

    subgraph "Capa de Datos"
        I[PostgreSQL/SQLite]
        I --> J[Tablas: Empresa, Usuario, Cliente, Pedido, Factura]
    end

    subgraph "Capa de Infraestructura"
        L[Docker Containers]
        L --> M[Kubernetes Orchestration]
        M --> N[Load Balancer]
        N --> O[CDN para Assets]
    end

    subgraph "Integraciones Externas"
        P[Email Provider - SendGrid]
        Q[Pagos - Stripe/MercadoPago]
    end

    A --> D
    D --> I
    H --> P
    F --> Q

    subgraph "Roles de Usuario"
        R[Auxiliar Registro]
        S[Auxiliar Tostión]
        T[Auxiliar Producción]
        U[Auxiliar Facturación]
        V[Admin Empresa]
        W[Super Admin]
    end

    R --> F
    S --> F
    T --> F
    U --> F
    V --> F
    W --> F
```

## Características Principales

- **Multi-Tenancy**: Aislamiento completo entre empresas maquiladoras
- **Roles de Usuario**: Auxiliar Registro, Tostión, Producción, Facturación, Admin Empresa, Super Admin
- **Flujo de Pedidos**: Estados FSM con transiciones controladas
- **Notificaciones**: Automáticas por email
- **Reportes**: Dashboards específicos por rol

## Tecnologías

- **Backend**: Django 4.2.16
- **Base de Datos**: PostgreSQL (producción) / SQLite (desarrollo)
- **Frontend**: Django Templates + Crispy Forms + Tailwind CSS + Font Awesome
- **Autenticación**: Django Auth + Django Guardian
- **Estados**: Django FSM
- **Email**: Django Email Backend
- **UI/UX**: Diseño moderno con glass effects, animaciones y tema coffee personalizado

## Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <url-del-repo>
cd maquila_system
```

### 2. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 5. Ejecutar migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear empresa de prueba y superusuario
```bash
# Crear empresa de prueba
python manage.py shell -c "from core.models import Company; Company.objects.create(name='Test Company', slug='test-company', nit='123456789', email='test@test.com', address='Test Address')"

# Crear superusuario
python manage.py createsuperuser --username admin --email admin@test.com
```

### 7. Ejecutar servidor de desarrollo
```bash
python manage.py runserver
```

**Nota**: El servidor se ejecutará en `http://127.0.0.1:8000` por defecto. Si el puerto 8000 está ocupado, usa `python manage.py runserver 8001` para el puerto 8001.

Acceder al admin en: http://localhost:8000/admin/

## Configuración de Base de Datos

### Desarrollo (SQLite)
En `.env`:
```
DATABASE_URL=sqlite:///db.sqlite3
```

### Producción (PostgreSQL)
En `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/maquila_system
```

Instalar PostgreSQL y crear la base de datos:
```bash
createdb maquila_system
```

## Configuración Multi-Tenant

Para implementar multi-tenancy completa con django-tenants:

1. Cambiar a PostgreSQL
2. Agregar django-tenants a INSTALLED_APPS
3. Configurar TENANT_MODEL y TENANT_DOMAIN_MODEL
4. Ejecutar migraciones de tenants

## Estructura del Proyecto

```
maquila_system/
├── maquila_system/          # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                    # App principal
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Vistas
│   ├── urls.py             # URLs de la app
│   └── migrations/         # Migraciones
├── templates/              # Plantillas HTML
├── static/                 # Archivos estáticos
├── media/                  # Archivos media
├── requirements.txt        # Dependencias
├── .env.example           # Variables de entorno ejemplo
└── README.md              # Este archivo
```

## Modelos Principales

- **Company**: Empresas maquiladoras
- **User**: Usuarios con roles específicos
- **Client**: Clientes (productores)
- **Order**: Pedidos con estados FSM
- **Invoice**: Facturas

## Diseño de Interfaz

### Tema Visual
- **Paleta de colores**: Tema "coffee" personalizado con gradientes cálidos
- **Tipografía**: Fuentes modernas y legibles
- **Iconografía**: Font Awesome para iconos consistentes
- **Efectos**: Glass effects, animaciones sutiles y transiciones suaves

### Componentes Principales
- **Navbar responsive**: Con dropdown de usuario y navegación intuitiva
- **Sistema de mensajes**: Con iconos, auto-hide y animaciones
- **Cards modernas**: Con efectos hover y glass effects
- **Formularios**: Validación visual y estilos Tailwind consistentes
- **Estados visuales**: Indicadores coloreados para estados de empresa/usuario

### Templates Incluidos
- **base.html**: Template base con navbar, footer y sistema de mensajes
- **home.html**: Landing page atractiva + dashboard preview
- **login.html**: Formulario centrado con diseño moderno
- **dashboard.html**: Contenido diferenciado por rol de usuario
- **suspended.html**: Página informativa para empresas suspendidas
- **crear_empresa.html**: Formulario para crear nuevas empresas (Super Admin)
- **pedidos/crear.html**: Formulario avanzado para crear pedidos con toggle cliente
- **tostion/lista.html**: Lista de pedidos para tostión con filtros y estadísticas
- **tostion/crear.html**: Formulario técnico de tostión con validaciones
- **produccion/lista.html**: Lista de pedidos para producción con indicadores
- **produccion/crear.html**: Formulario de producción con controles de calidad
- **facturacion/lista.html**: Lista de pedidos para facturar con alertas
- **facturacion/crear.html**: Formulario de facturación con cálculos automáticos
- **custom.css**: Estilos personalizados con animaciones y efectos avanzados

## Flujo de Estados del Pedido

```
Registrado → En Tostión → Tostión Completa → En Producción → Listo para Facturar → Facturado → Entregado
```

## Roles de Usuario

- **Super Admin**: Control total del sistema
- **Admin Empresa**: Gestión de usuarios y reportes de su empresa
- **Auxiliar Registro**: Registrar clientes y pedidos
- **Auxiliar Tostión**: Gestionar proceso de tostión
- **Auxiliar Producción**: Gestionar empaque y producción
- **Auxiliar Facturación**: Generar facturas y gestionar entregas

## Funcionalidades Implementadas ✅

### 🎨 Frontend Completo
- **Templates Base**: Diseño moderno con Tailwind CSS
- **Dashboard Interactivo**: Métricas en tiempo real por rol
- **Formularios Avanzados**: Validaciones JavaScript y cálculos automáticos
- **Navegación Inteligente**: Breadcrumbs y menús contextuales
- **Modales y AJAX**: Interacciones dinámicas sin recargar página

### 📋 Módulos Operativos
- **🏢 Gestión de Empresas**: Creación y administración (Super Admin)
- **📝 Registro**: Crear pedidos con clientes existentes o nuevos
- **🔥 Tostión**: Control de procesos técnicos con validaciones
- **📦 Producción**: Empaque y controles de calidad
- **💰 Facturación**: Generación automática de facturas

### 🔐 Sistema de Seguridad
- **Control de Acceso**: Decoradores por rol específicos
- **Aislamiento Multi-tenant**: Datos completamente separados por empresa
- **Auditoría Completa**: Registro de todas las acciones
- **Estados FSM**: Transiciones controladas de pedidos

### 📊 Características Técnicas
- **Cálculos Automáticos**: Totales, rendimientos, IVA
- **Validaciones en Tiempo Real**: JavaScript + Django
- **Búsqueda y Filtros**: Autocompletado y filtros avanzados
- **Responsive Design**: Funciona en desktop y móvil
- **Gestión de Errores**: Mensajes informativos y manejo de excepciones

## Próximos Pasos Opcionales

1. Sistema de notificaciones por email automáticas
2. API REST para integraciones externas
3. Reportes avanzados con gráficos
4. Pruebas unitarias y de integración
5. Despliegue en producción con Docker/Kubernetes
6. Sistema de pagos integrado
7. App móvil complementaria

## Contribución

1. Crear rama para nueva funcionalidad
2. Implementar cambios
3. Crear pruebas
4. Hacer pull request

## Licencia

Este proyecto está bajo la licencia MIT.