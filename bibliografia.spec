# Especificación de PyInstaller. Generar con: build.bat
# Produce dist\GestionBibliografia.exe (un solo archivo, sin consola).
a = Analysis(
    ['app.py'],
    datas=[('MANUAL.txt', '.')],
    hiddenimports=['psycopg_binary'],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name='GestionBibliografia',
    console=False,
    upx=False,
)
