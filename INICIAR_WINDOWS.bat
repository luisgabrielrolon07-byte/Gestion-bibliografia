@echo off
cd /d "%~dp0"
python app.py
if errorlevel 1 (
 echo No se pudo iniciar. Verifique Python, las dependencias ^(pip install -r requirements.txt^) y PostgreSQL.
 pause
)
