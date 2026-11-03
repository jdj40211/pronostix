import unittest

from adapter import MockEstadisticas
from app import app


class AdapterTest(unittest.TestCase):
    def test_mock(self):
        r = MockEstadisticas().forma_reciente('Nacional', 'Millonarios', 'futbol')
        self.assertTrue(r['disponible'])
        self.assertEqual(r['fuente'], 'mock-interno')


class EstadisticasAPITest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_salud(self):
        r = self.client.get('/api/v2/estadisticas/salud')
        self.assertEqual(r.status_code, 200)

    def test_forma(self):
        r = self.client.post(
            '/api/v2/estadisticas/forma/',
            json={'local': 'Nacional', 'visitante': 'Millonarios', 'deporte': 'futbol'},
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn('resumen', r.get_json())

    def test_400(self):
        r = self.client.post('/api/v2/estadisticas/forma/', json={'local': 'Nacional'})
        self.assertEqual(r.status_code, 400)


if __name__ == '__main__':
    unittest.main()
