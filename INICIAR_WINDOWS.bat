@echo off
cd /d "%~dp0"
python app.py
if errorlevel 1 (
 echo No se pudo iniciar. Verifique que Python y Tcl/Tk esten instalados.
 pause
)
