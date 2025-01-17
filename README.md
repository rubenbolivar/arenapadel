# ArenaPadel.club - Sistema de Reservas

Sistema de gestión de reservas para canchas de pádel con interfaz moderna y experiencia de usuario optimizada.

## Características Principales

- Gestión de 12 canchas de pádel
- Sistema de reservas por hora
- Múltiples métodos de pago
- Notificaciones vía WhatsApp
- Panel administrativo completo
- API REST para futura expansión

## Requisitos

- Python 3.10+
- PostgreSQL 13+
- Node.js 18+ (para desarrollo frontend)

## Instalación

1. Clonar el repositorio
```bash
git clone https://github.com/your-repo/arenapadel.git
cd arenapadel
```

2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con las configuraciones necesarias
```

5. Ejecutar migraciones
```bash
python manage.py migrate
```

6. Iniciar servidor de desarrollo
```bash
python manage.py runserver
```

## Estructura del Proyecto

```
arenapadel/
├── apps/
│   ├── reservations/    # Gestión de reservas
│   ├── users/           # Gestión de usuarios
│   └── payments/        # Sistema de pagos
├── config/              # Configuraciones del proyecto
├── static/              # Archivos estáticos
└── templates/           # Plantillas HTML
```

## Documentación

Para más información, consultar:
- [Manual de Usuario](docs/user-manual.md)
- [Documentación API](docs/api.md)
- [Guía de Mantenimiento](docs/maintenance.md)

## Licencia

Todos los derechos reservados - ArenaPadel.club
