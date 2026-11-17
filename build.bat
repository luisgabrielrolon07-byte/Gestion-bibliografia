@echo off
rem Genera dist\GestionBibliografia.exe con PyInstaller.
cd /d "%~dp0"
python -m pip install -r requirements-dev.txt || goto :error
python -m PyInstaller --noconfirm --clean bibliografia.spec || goto :error
copy /y config.example.ini dist\config.example.ini >nul
copy /y MANUAL.txt dist\MANUAL.txt >nul
echo.
echo Listo: dist\GestionBibliografia.exe
echo Copie config.example.ini como config.ini junto al .exe y complete la contrasena.
exit /b 0
:error
echo Fallo la generacion del ejecutable.
pause
exit /b 1
