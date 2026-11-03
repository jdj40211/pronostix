import unittest

from app import app
from dominio import mercados_para, registrar_pase, total_con_iva


class DominioTest(unittest.TestCase):
    def test_iva(self):
        r = total_con_iva('12000')
        self.assertEqual(r['total'], '14280.00')

    def test_mercado_premium_bloqueado_sin_pase(self):
        r = mercados_para('demo', 1)
        premium = [m for m in r['mercados'] if m['es_premium']]
        self.assertTrue(all(m['bloqueado'] for m in premium))

    def test_pase_abre_premium(self):
        registrar_pase('demo', 1)
        r = mercados_para('demo', 1)
        self.assertTrue(r['tiene_pase'])
        self.assertTrue(all(not m['bloqueado'] for m in r['mercados']))


class CatalogoAPITest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_listar(self):
        r = self.client.get('/api/v2/catalogo/eventos/')
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.get_json()['eventos']), 2)

    def test_integracion(self):
        r = self.client.get('/api/v2/catalogo/integracion/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['proyecto'], 'Pronostix')

    def test_404(self):
        r = self.client.get('/api/v2/catalogo/eventos/999')
        self.assertEqual(r.status_code, 404)


if __name__ == '__main__':
    unittest.main()
