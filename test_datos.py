"""Pruebas de la capa de datos contra PostgreSQL.

Usa la misma conexión que el programa (config.ini o variables PG*), pero trabaja
en un esquema temporal que se elimina al terminar: no toca los datos reales.
"""
import unittest
import uuid

import psycopg
from psycopg import sql

from app import Repository, conectar, leer_config


class DatosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = leer_config()
        try:
            conectar(cls.params).close()
        except psycopg.OperationalError as exc:
            raise unittest.SkipTest(f'PostgreSQL no disponible: {exc}')

    def setUp(self):
        self.schema = 'test_' + uuid.uuid4().hex[:8]
        self.repo = Repository(self.params, schema=self.schema)

    def tearDown(self):
        if hasattr(self, 'repo'):
            self.repo.db.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(self.schema)))
            self.repo.close()

    def test_ciclo_y_persistencia(self):
        r = self.repo
        r.guardar('fac01', 'Ciencias')
        ident = r.facultades()[0][0]
        with self.assertRaises(ValueError): r.guardar('FAC01', 'Otro')
        with self.assertRaises(ValueError): r.guardar('', 'Nombre')
        r.guardar('FAC01', 'Tecnología', ident)
        self.assertEqual(len(r.facultades('tecno')), 1)
        self.assertEqual(len(r.facultades('fac0')), 1)
        r.carrera('CAR01', 'Informática')
        career = r.carreras()[0][0]
        r.asociar(career, ident)
        r.estado(ident, False)
        self.assertEqual(r.facultades(), [])
        self.assertEqual(len(r.facultades(inactive=True)), 1)
        self.assertEqual(r.carreras()[0][3], 'Tecnología')
        with self.assertRaises(ValueError): r.asociar(career, ident)
        with self.assertRaises(ValueError): r.asociar(999, None)
        r.estado(ident, True)
        r.asociar(career, None)
        self.assertIsNone(r.carreras()[0][3])
        r.close()
        # Persistencia: una conexión nueva ve los datos guardados.
        self.repo = r = Repository(self.params, schema=self.schema)
        self.assertEqual(r.facultades()[0][2], 'Tecnología')

    def test_duplicados_sin_distinguir_mayusculas(self):
        self.repo.guardar('FAC01', 'Ciencias')
        self.repo.estado(self.repo.facultades()[0][0], False)
        with self.assertRaises(ValueError): self.repo.guardar('fac01', 'Otra')
        self.repo.carrera('car01', 'Informática')
        with self.assertRaises(ValueError): self.repo.carrera('CAR01', 'Otra')

    def test_limites_de_longitud(self):
        with self.assertRaises(ValueError): self.repo.guardar('X' * 21, 'Nombre')
        with self.assertRaises(ValueError): self.repo.carrera('C', 'N' * 121)


if __name__ == '__main__':
    unittest.main()
