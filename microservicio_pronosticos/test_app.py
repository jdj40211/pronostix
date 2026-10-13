import unittest

from app import app
from motor import calcular

URL = '/api/v2/pronosticos/'


class MotorTests(unittest.TestCase):
    def test_sin_ranking_conserva_la_linea_base_del_monolito(self):
        r = calcular('futbol', 'moneyline')
        self.assertEqual(r['probabilidades'], {'local': 0.42, 'empate': 0.3, 'visitante': 0.28})
        self.assertEqual(r['mas_probable'], 'local')
        self.assertEqual(r['valor_esperado'], 0.42)

    def test_basquetbol_no_tiene_empate(self):
        r = calcular('basquetbol', 'moneyline')
        self.assertNotIn('empate', r['probabilidades'])

    def test_mejor_ranking_visitante_lo_favorece(self):
        r = calcular('futbol', 'moneyline', ranking_local=20, ranking_visitante=2)
        self.assertEqual(r['mas_probable'], 'visitante')

    def test_probabilidades_suman_uno(self):
        r = calcular('futbol', 'moneyline', ranking_local=1, ranking_visitante=99)
        self.assertAlmostEqual(sum(r['probabilidades'].values()), 1.0, places=3)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_salud(self):
        r = self.client.get('/api/v2/pronosticos/salud')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['estado'], 'ok')

    def test_calcula_varios_mercados(self):
        r = self.client.post(URL, json={'deporte': 'Futbol', 'mercados': ['moneyline', 'totales']})
        self.assertEqual(r.status_code, 200)
        cuerpo = r.get_json()
        self.assertEqual(cuerpo['servicio'], 'pronosticos-flask')
        self.assertEqual(cuerpo['deporte'], 'futbol')
        self.assertEqual([p['mercado'] for p in cuerpo['pronosticos']], ['moneyline', 'totales'])

    def test_acepta_url_sin_barra_final(self):
        r = self.client.post('/api/v2/pronosticos', json={'deporte': 'futbol', 'mercados': ['totales']})
        self.assertEqual(r.status_code, 200)

    def test_400_si_falta_deporte(self):
        r = self.client.post(URL, json={'mercados': ['moneyline']})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()['error']['campo'], 'deporte')

    def test_400_si_mercado_no_existe(self):
        r = self.client.post(URL, json={'deporte': 'futbol', 'mercados': ['corners']})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()['error']['campo'], 'mercados')

    def test_400_si_ranking_no_es_entero(self):
        r = self.client.post(URL, json={'deporte': 'futbol', 'mercados': ['moneyline'], 'ranking_local': 'uno'})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()['error']['campo'], 'ranking_local')

    def test_400_si_json_esta_roto(self):
        r = self.client.post(URL, data='{deporte:', content_type='application/json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()['error']['codigo'], 'json_invalido')

    def test_400_si_no_es_json(self):
        r = self.client.post(URL, data='deporte=futbol')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()['error']['codigo'], 'contenido_invalido')

    def test_405_estructurado(self):
        r = self.client.get(URL)
        self.assertEqual(r.status_code, 405)
        self.assertIn('error', r.get_json())

    def test_500_estructurado(self):
        import app as modulo
        original = modulo.pronosticar
        modulo.pronosticar = lambda datos: 1 / 0
        try:
            r = self.client.post(URL, json={'deporte': 'futbol', 'mercados': ['moneyline']})
        finally:
            modulo.pronosticar = original
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.get_json()['error']['codigo'], 'error_interno')


if __name__ == '__main__':
    unittest.main()
