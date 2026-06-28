 Maipú Ahorra 

 Maipú Ahorra es una aplicación web de comparación de precios diseñada con estética Neón desarrollada para el Seminario Final de Informática. Esta app permite a los ciudadanos encontrar los supermercados locales con los precios más baratos para sus listas de compras, generando códigos de descuento y brindando métricas de *Business Intelligence* a los dueños de los locales.

Características Principales

Para Compradores (Clientes)
**Catálogo Global:** Búsqueda rápida de productos por nombre o categoría.
**Carrito Inteligente:** Agrega productos a tu lista (ajustando las cantidades) y el sistema calculará automáticamente qué supermercado local ofrece el total más barato.
**Códigos de Descuento:** Al confirmar la lista, se autogenera un código único que puedes presentar en la caja del local ganador.
**Verificación de Seguridad:** Sistema de registro con validación por correo electrónico.

Para Dueños de Locales (Mercados)
**Gestión de Precios:** Actualización rápida de los precios del catálogo para competir de manera directa.
**Dashboard de Business Intelligence (BI):** Tarjetas de métricas en tiempo real que muestran cuántas listas han ganado en el mes, ingresos potenciales generados y número de clientes únicos atraídos por sus ofertas.

Tecnologías

| Componente | Versión | Justificación |
| :--- | :--- | :--- |
| **Python** | 3.10+ | Lenguaje principal del proyecto para el desarrollo del backend. |
| **Flask** | 3.0.2 | Framework web minimalista y veloz utilizado para el enrutamiento. |
| **SQLite** | 3+ | Base de datos relacional nativa y ligera, ideal para desarrollo local. |
| **SQLAlchemy**| 3.1.1 | ORM utilizado para interactuar con la base de datos mediante clases de Python, evitando inyecciones SQL. |
| **HTML / CSS**| 5 / 3 | Construcción del frontend utilizando variables CSS puras para el tema Neón, sin requerir frameworks externos pesados. |

Arquitectura

El sistema sigue una adaptación del patrón **Model-View-Controller (MVC)**:

```text
proyecto-final-seminario/
├── models.py             # Capa de Modelos (Entidades y ORM con SQLAlchemy)
├── app.py                # Controlador principal (Rutas de negocio, cliente y mercado)
├── auth.py               # Controlador de Autenticación (Login, Registro, Verificación)
├── seed.py               # Script de inicialización (Población de base de datos)
├── requirements.txt      # Gestión de dependencias
├── instance/
│   └── market.db         # Base de datos local (SQLite)
├── static/               # Recursos estáticos
│   ├── styles.css        # Hoja de estilos principal (Diseño Neón)
│   └── images/
│       └── logo.png      # Identidad visual
└── templates/            # Capa de Vistas (Plantillas HTML renderizadas con Jinja2)
    ├── base.html         # Plantilla abstracta base (herencia)
    ├── cliente_inicio.html
    ├── panel_mercado.html
    ├── iniciar_sesion.html
    └── ...
```

Instalación y Ejecución Local

Pasos para correr el proyecto loclamente:

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/TU_USUARIO_GITHUB/maipu-ahorra.git
   cd maipu-ahorra
   ```

2. **Crear y activar entorno virtual**
   ```bash
   # En Windows:
   python -m venv venv
   .\venv\Scripts\activate
   ```
   *(Si usas Mac/Linux: `source venv/bin/activate`)*

3. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicializa la Base de Datos (primera vez)**
   Para poblar la base de datos inicial con productos de muestra y usuarios de prueba, ejecuta:
   ```bash
   python seed.py
   ```

5. **Inicia el servidor**
   ```bash
   python app.py
   ```
   *(Nota para usuarios Windows: alternativamente, puedes hacer doble clic en el archivo `run.bat` de la carpeta raíz).*

6. **Accede la App**
   Abre tu navegador y entra a: [http://127.0.0.1:5000](http://127.0.0.1:5000)

Datos de Prueba

Si ejecutaste el archivo `seed.py`, el sistema generará automáticamente los siguientes usuarios para que pruebes los diferentes roles (la contraseña para todos es **`12345`**):

- **Cliente:** `cliente1@prueba.com`
- **Mercado 1:** `mercadoeco+@prueba.com`
- **Mercado 2:** `mercadototo@prueba.com`

> **Nota sobre los correos:** Durante el desarrollo local, el envío de correos electrónicos de validación de nuevas cuentas se encuentra en *Modo Simulado* para evitar errores sin credenciales SMTP. Si registras un usuario nuevo, busca el enlace de validación impreso directamente en la consola de tu terminal.

Estructura del Proyecto
- `app.py`: Controlador principal, rutas y lógica del servidor Flask.
- `auth.py`: Blueprint encargado de la seguridad, registro, login y validación de tokens.
- `models.py`: Estructura del modelo relacional para la base de datos.
- `templates/`: Plantillas HTML (vistas).
- `static/`: Hojas de estilo CSS e imágenes.
