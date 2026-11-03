import unittest

from app import app
from pasarela import procesar


class PasarelaLogicaTest(unittest.TestCase):
    def test_mock_aprueba(self):
        r = procesar({'orden_id': 1, 'monto': '1000', 'modo': 'MOCK'})
        self.assertTrue(r['aprobado'])
        self.assertEqual(r['referencia'], 'MOCK-OK')

    def test_real_aprueba_con_referencia(self):
        r = procesar({'orden_id': 2, 'monto': '14280.00', 'modo': 'REAL'})
        self.assertTrue(r['aprobado'])
        self.assertTrue(str(r['referencia']).startswith('PX-'))


class PagosAPITest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_salud(self):
        r = self.client.get('/api/v2/pagos/salud')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['servicio'], 'pagos-flask')

    def test_cobro_ok(self):
        r = self.client.post(
            '/api/v2/pagos/',
            json={'orden_id': 1, 'monto': '14280', 'modo': 'MOCK'},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()['aprobado'])

    def test_400_sin_orden(self):
        r = self.client.post('/api/v2/pagos/', json={'monto': '100'})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()['error']['codigo'], 'validacion')


if __name__ == '__main__':
    unittest.main()
