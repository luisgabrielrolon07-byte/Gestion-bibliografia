# Gestion-bibliografia
Proyecto grupal UAA - Sistema de gestión de bibliografía.

Aplicación de escritorio en **Python + Tkinter** con base de datos **PostgreSQL**,
según el Acta de Constitución del Proyecto (sección VII).

## Puesta en marcha (desarrollo)

1. Instalar [Python 3.10+](https://www.python.org/) (marcar *Add Python to PATH*) y
   [PostgreSQL](https://www.postgresql.org/download/windows/) con pgAdmin.
2. Instalar dependencias:
   ```
   python -m pip install -r requirements-dev.txt
   ```
3. Copiar `config.example.ini` como `config.ini` y completar la contraseña de `postgres`.
   `config.ini` no se sube a GitHub. La base `bibliografia` y sus tablas se crean solas.
4. Abrir `GestionBibliografia.sln` en **Visual Studio Community** (workload *Desarrollo de Python*)
   y ejecutar con F5, o usar VS Code / `python app.py`.

## Pruebas

```
python -m unittest -v
```

Las pruebas usan la conexión de `config.ini`, pero trabajan en un esquema temporal que se
borra al terminar. Si PostgreSQL no está disponible, se omiten. En Visual Studio aparecen en el
Explorador de pruebas.

## Ejecutable (Definición de Hecho)

```
build.bat
```

Genera `dist\GestionBibliografia.exe` con Python y todas las bibliotecas incluidas (PyInstaller).
`dist/` no se versiona: el `.exe` se publica como **Release** en GitHub. Para usarlo solo hace
falta PostgreSQL en ejecución y un `config.ini` junto al `.exe`.

## Estructura

| Archivo | Contenido |
|---|---|
| `app.py` | Interfaz (`App`) y capa de datos (`Repository`) |
| `test_datos.py` | Pruebas unitarias de la capa de datos |
| `MANUAL.txt` | Manual de usuario (se abre con F1) |
| `bibliografia.spec`, `build.bat` | Empaquetado con PyInstaller |
| `GestionBibliografia.sln`, `.pyproj` | Solución de Visual Studio |
