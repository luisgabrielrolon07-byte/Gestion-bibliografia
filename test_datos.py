import tempfile
import unittest
from pathlib import Path
from app import Repository


class DatosTest(unittest.TestCase):
    def test_ciclo_y_persistencia(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.sqlite3'
            r=Repository(path)
            r.guardar('fac01','Ciencias')
            ident=r.facultades()[0][0]
            with self.assertRaises(ValueError): r.guardar('FAC01','Otro')
            with self.assertRaises(ValueError): r.guardar('','Nombre')
            r.guardar('FAC01','Tecnología',ident)
            self.assertEqual(len(r.facultades('Tecnología')),1)
            r.carrera('CAR01','Informática')
            career=r.db.execute('SELECT id FROM carreras').fetchone()[0]
            r.asociar(career,ident)
            r.estado(ident,False)
            self.assertEqual(r.facultades(),[])
            self.assertEqual(r.db.execute('SELECT facultad_id FROM carreras').fetchone()[0],ident)
            with self.assertRaises(ValueError): r.asociar(career,ident)
            with self.assertRaises(ValueError): r.asociar(999,None)
            r.estado(ident,True)
            r.asociar(career,None)
            self.assertIsNone(r.db.execute('SELECT facultad_id FROM carreras').fetchone()[0])
            r.db.close()
            r=Repository(path)
            self.assertEqual(r.facultades()[0][2],'Tecnología')
            r.db.close()

if __name__=='__main__': unittest.main()
