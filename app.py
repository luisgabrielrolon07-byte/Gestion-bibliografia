"""Incremento 1: Facultad. Python 3 + Tkinter + PostgreSQL (psycopg)."""
import configparser
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import psycopg
from psycopg import sql

# Carpeta del programa (junto al .exe cuando está empaquetado) y carpeta de recursos.
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
RES_DIR = Path(getattr(sys, '_MEIPASS', APP_DIR))

ESQUEMA = '''
CREATE TABLE IF NOT EXISTS facultades (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE);
CREATE UNIQUE INDEX IF NOT EXISTS facultades_codigo_uk ON facultades (upper(codigo));
CREATE TABLE IF NOT EXISTS carreras (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    facultad_id INTEGER REFERENCES facultades(id));
CREATE UNIQUE INDEX IF NOT EXISTS carreras_codigo_uk ON carreras (upper(codigo));
'''


def leer_config(path=None):
    """Lee config.ini (sección [postgresql]). Los valores vacíos se omiten para que
    libpq use sus variables de entorno (PGHOST, PGPASSWORD, ...) o sus valores por defecto."""
    params = {'host': 'localhost', 'port': '5432', 'dbname': 'bibliografia', 'user': 'postgres',
              'connect_timeout': '5'}
    parser = configparser.ConfigParser()
    parser.read(path or APP_DIR / 'config.ini', encoding='utf-8')
    if parser.has_section('postgresql'):
        params.update(parser['postgresql'])
    return {k: v for k, v in params.items() if v.strip()}


def conectar(params):
    """Conecta a la base; si no existe, la crea desde la base de mantenimiento 'postgres'."""
    try:
        return psycopg.connect(**params, autocommit=True)
    except psycopg.OperationalError as original:
        if isinstance(original, psycopg.errors.ConnectionTimeout):
            raise  # el servidor no responde: no tiene sentido intentar crear la base
        admin = {**params, 'dbname': 'postgres'}
        try:
            with psycopg.connect(**admin, autocommit=True) as conn:
                if conn.execute('SELECT 1 FROM pg_database WHERE datname=%s', (params['dbname'],)).fetchone():
                    raise original
                conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(params['dbname'])))
        except psycopg.Error:
            raise original from None
        return psycopg.connect(**params, autocommit=True)


class Repository:
    def __init__(self, params, schema=None):
        self.db = conectar(params)
        if schema:  # usado por las pruebas para trabajar en un esquema aislado
            self.db.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(schema)))
            self.db.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        with self.db.transaction():
            self.db.execute(ESQUEMA)

    def close(self):
        self.db.close()

    def facultades(self, query='', inactive=False):
        return self.db.execute(
            'SELECT id,codigo,nombre,activo FROM facultades '
            'WHERE (%s OR activo) AND (strpos(lower(nombre),lower(%s))>0 OR strpos(lower(codigo),lower(%s))>0) '
            'ORDER BY nombre', (inactive, query, query)).fetchall()

    def carreras(self):
        return self.db.execute(
            'SELECT c.id,c.codigo,c.nombre,f.nombre,f.activo FROM carreras c '
            'LEFT JOIN facultades f ON f.id=c.facultad_id ORDER BY c.nombre').fetchall()

    def guardar(self, codigo, nombre, ident=None):
        codigo, nombre = codigo.strip().upper(), nombre.strip()
        if not codigo or not nombre:
            raise ValueError('Completá código y nombre.')
        if len(codigo) > 20 or len(nombre) > 120:
            raise ValueError('Código: máximo 20 caracteres. Nombre: máximo 120.')
        try:
            with self.db.transaction():
                if ident is None:
                    self.db.execute('INSERT INTO facultades(codigo,nombre) VALUES (%s,%s)', (codigo, nombre))
                else:
                    self.db.execute('UPDATE facultades SET codigo=%s,nombre=%s WHERE id=%s', (codigo, nombre, ident))
        except psycopg.errors.UniqueViolation:
            raise ValueError('Ese código ya existe, incluso entre las facultades inactivas.') from None

    def estado(self, ident, active):
        with self.db.transaction():
            self.db.execute('UPDATE facultades SET activo=%s WHERE id=%s', (bool(active), ident))

    def carrera(self, codigo, nombre):
        codigo, nombre = codigo.strip().upper(), nombre.strip()
        if not codigo or not nombre:
            raise ValueError('Completá código y nombre de la carrera.')
        if len(codigo) > 20 or len(nombre) > 120:
            raise ValueError('Código: máximo 20 caracteres. Nombre: máximo 120.')
        try:
            with self.db.transaction():
                self.db.execute('INSERT INTO carreras(codigo,nombre) VALUES (%s,%s)', (codigo, nombre))
        except psycopg.errors.UniqueViolation:
            raise ValueError('El código de carrera ya existe.') from None

    def asociar(self, carrera, facultad):
        if facultad is not None and not self.db.execute('SELECT 1 FROM facultades WHERE id=%s AND activo', (facultad,)).fetchone():
            raise ValueError('Seleccioná una facultad activa.')
        if not self.db.execute('SELECT 1 FROM carreras WHERE id=%s', (carrera,)).fetchone():
            raise ValueError('Seleccioná una carrera existente.')
        with self.db.transaction():
            self.db.execute('UPDATE carreras SET facultad_id=%s WHERE id=%s', (facultad, carrera))


class App(tk.Tk):
    def __init__(self, repo):
        super().__init__()
        self.title('Bibliografía universitaria · Módulo Facultad')
        self.geometry('1000x680')
        self.minsize(800,580)
        self.repo = repo
        self.selected = None
        style=ttk.Style(self)
        style.theme_use('clam')
        style.configure('TButton',padding=7)
        style.configure('Treeview',rowheight=28)
        menu=tk.Menu(self)
        modules=tk.Menu(menu,tearoff=False)
        modules.add_command(label='Facultades',command=lambda:self.tabs.select(0))
        modules.add_command(label='Asociación Facultad–Carrera',command=lambda:self.tabs.select(1))
        modules.add_separator()
        modules.add_command(label='Salir',command=self.close)
        menu.add_cascade(label='Menú principal',menu=modules)
        menu.add_command(label='Manual de usuario (F1)',command=self.help)
        self.config(menu=menu)
        self.bind('<F1>',lambda e:self.help())
        ttk.Label(self,text='Gestión de bibliografía de las materias',font=('Arial',20,'bold')).pack(anchor='w',padx=22,pady=(20,4))
        ttk.Label(self,text='Incremento 1 · Luis Rolón · Facultad').pack(anchor='w',padx=22,pady=(0,16))
        self.tabs=ttk.Notebook(self)
        self.tabs.pack(fill='both',expand=True,padx=20,pady=8)
        self.fac=ttk.Frame(self.tabs,padding=16)
        self.links=ttk.Frame(self.tabs,padding=16)
        self.tabs.add(self.fac,text='Facultades')
        self.tabs.add(self.links,text='Facultad y carreras')
        self.build_fac()
        self.build_links()
        self.status=tk.StringVar(value='Listo. F1 abre la ayuda de la pantalla actual.')
        ttk.Label(self,textvariable=self.status,padding=12).pack(fill='x')
        self.refresh()
        self.protocol('WM_DELETE_WINDOW',self.close)

    def close(self):
        self.repo.close()
        self.destroy()

    def run(self, action):
        try:
            action()
            self.refresh()
            self.status.set('Operación realizada. Los cambios están guardados.')
        except (ValueError,psycopg.Error) as exc:
            messagebox.showerror('Revisá los datos',str(exc),parent=self)

    def build_fac(self):
        bar=ttk.Frame(self.fac); bar.pack(fill='x')
        self.search=tk.StringVar()
        ttk.Label(bar,text='Buscar por nombre o código:').pack(side='left')
        entry=ttk.Entry(bar,textvariable=self.search,width=30); entry.pack(side='left',padx=8)
        self.search.trace_add('write',lambda *args:self.refresh())
        self.inactive=tk.BooleanVar()
        ttk.Checkbutton(bar,text='Mostrar inactivas',variable=self.inactive,command=self.refresh).pack(side='left')
        self.tree=self.table(self.fac,('Código','Nombre','Estado'))
        self.tree.bind('<<TreeviewSelect>>',self.choose)
        form=ttk.Frame(self.fac); form.pack(fill='x',pady=12)
        self.code=tk.StringVar(); self.name=tk.StringVar()
        ttk.Label(form,text='Código *').grid(row=0,column=0,sticky='w')
        ttk.Label(form,text='Nombre *').grid(row=0,column=1,sticky='w',padx=10)
        ttk.Entry(form,textvariable=self.code,width=20).grid(row=1,column=0)
        ttk.Entry(form,textvariable=self.name,width=60).grid(row=1,column=1,padx=10)
        buttons=ttk.Frame(self.fac); buttons.pack(fill='x')
        ttk.Button(buttons,text='Nuevo / limpiar',command=self.clear).pack(side='left')
        ttk.Button(buttons,text='Guardar',command=lambda:self.run(self.save)).pack(side='left',padx=6)
        ttk.Button(buttons,text='Desactivar',command=lambda:self.change_state(False)).pack(side='left')
        ttk.Button(buttons,text='Reactivar',command=lambda:self.change_state(True)).pack(side='left',padx=6)
        ttk.Label(self.fac,text='La baja lógica conserva la facultad y sus vínculos con carreras.').pack(anchor='w',pady=10)

    def table(self,parent,columns):
        frame=ttk.Frame(parent); frame.pack(fill='both',expand=True,pady=12)
        tree=ttk.Treeview(frame,columns=columns,show='headings',selectmode='browse')
        for c in columns:
            tree.heading(c,text=c); tree.column(c,width=150,stretch=True)
        scroll=ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side='left',fill='both',expand=True); scroll.pack(side='right',fill='y')
        return tree

    def choose(self,event=None):
        ids=self.tree.selection()
        if ids:
            self.selected=int(ids[0])
            values=self.tree.item(ids[0],'values')
            self.code.set(values[0]); self.name.set(values[1])

    def clear(self):
        self.selected=None; self.code.set(''); self.name.set('')
        self.tree.selection_remove(self.tree.selection())

    def save(self):
        self.repo.guardar(self.code.get(),self.name.get(),self.selected)
        self.clear()

    def change_state(self,active):
        if self.selected is None:
            messagebox.showinfo('Seleccioná una facultad','Primero seleccioná una fila.'); return
        if messagebox.askyesno('Confirmación',('¿Reactivar' if active else '¿Desactivar')+' la facultad seleccionada?'):
            self.run(lambda:self.repo.estado(self.selected,active))
            self.clear()

    def build_links(self):
        ttk.Label(self.links,text='Cada carrera puede pertenecer a una sola facultad.').pack(anchor='w')
        self.career_tree=self.table(self.links,('Código','Carrera','Facultad','Estado facultad'))
        row=ttk.Frame(self.links); row.pack(fill='x')
        self.faculty_box=ttk.Combobox(row,state='readonly',width=55)
        self.faculty_box.pack(side='left')
        ttk.Button(row,text='Asociar / cambiar',command=lambda:self.run(lambda:self.link(False))).pack(side='left',padx=8)
        ttk.Button(row,text='Quitar vínculo',command=lambda:self.run(lambda:self.link(True))).pack(side='left')
        seed=ttk.LabelFrame(self.links,text='Registro mínimo de carreras para probar la asociación',padding=10)
        seed.pack(fill='x',pady=15)
        self.cc=tk.StringVar(); self.cn=tk.StringVar()
        ttk.Label(seed,text='Código').grid(row=0,column=0)
        ttk.Entry(seed,textvariable=self.cc,width=15).grid(row=0,column=1,padx=5)
        ttk.Label(seed,text='Nombre').grid(row=0,column=2)
        ttk.Entry(seed,textvariable=self.cn,width=35).grid(row=0,column=3,padx=5)
        ttk.Button(seed,text='Registrar carrera',command=lambda:self.run(self.add_career)).grid(row=0,column=4)

    def add_career(self):
        self.repo.carrera(self.cc.get(),self.cn.get())
        self.cc.set(''); self.cn.set('')

    def link(self,remove):
        ids=self.career_tree.selection()
        if not ids: raise ValueError('Seleccioná una carrera en la tabla.')
        idx=self.faculty_box.current()
        if not remove and idx<0: raise ValueError('Elegí una facultad activa.')
        self.repo.asociar(int(ids[0]),None if remove else self.faculty_ids[idx])

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for ident,code,name,active in self.repo.facultades(self.search.get(),self.inactive.get()):
            self.tree.insert('', 'end',iid=str(ident),values=(code,name,'Activa' if active else 'Inactiva'))
        self.selected=None
        self.code.set(''); self.name.set('')
        faculties=self.repo.facultades()
        self.faculty_ids=[f[0] for f in faculties]
        self.faculty_box['values']=[f'{f[1]} · {f[2]}' for f in faculties]
        self.faculty_box.set('')
        self.career_tree.delete(*self.career_tree.get_children())
        for ident,code,name,faculty,active in self.repo.carreras():
            self.career_tree.insert('','end',iid=str(ident),values=(code,name,faculty or 'Sin vínculo',('Activa' if active else 'Inactiva') if faculty else '—'))

    def help(self):
        win=tk.Toplevel(self); win.title('Manual de usuario · F1'); win.geometry('720x520')
        text=tk.Text(win,wrap='word',padx=20,pady=20,font=('Arial',12))
        text.pack(fill='both',expand=True)
        section='FACULTADES' if self.tabs.index(self.tabs.select())==0 else 'ASOCIACIONES'
        text.insert('1.0',f'AYUDA DE {section}\n\n'+(RES_DIR/'MANUAL.txt').read_text(encoding='utf-8'))
        text.config(state='disabled')


def main():
    params = leer_config()
    try:
        repo = Repository(params)
    except psycopg.Error as exc:
        root = tk.Tk(); root.withdraw()
        messagebox.showerror(
            'No se pudo conectar a PostgreSQL',
            f'Servidor: {params.get("host")}:{params.get("port")} · Base: {params.get("dbname")} · Usuario: {params.get("user")}\n\n'
            f'{exc}\n\nVerificá que PostgreSQL esté en ejecución y revisá config.ini '
            f'(copiá config.example.ini como config.ini junto al programa).')
        root.destroy()
        return 1
    App(repo).mainloop()
    return 0


if __name__=='__main__':
    sys.exit(main())
