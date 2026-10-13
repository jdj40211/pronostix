"""
Motor de pronosticos extraido del monolito (antes ventas/domain/modelo.py).
No conoce Django ni la base de datos: recibe datos planos y devuelve
probabilidades, por eso se puede desplegar y escalar por separado.
"""

VERSION_MODELO = 'v1-forma-reciente'

MERCADOS = ('moneyline', 'totales', 'handicap', 'anotadores')

AJUSTE_POR_PUESTO = 0.01
AJUSTE_MAXIMO = 0.15
PROBABILIDAD_MINIMA = 0.05


class ErrorValidacion(Exception):
    def __init__(self, mensaje, campo=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


def base(deporte, mercado):
    if mercado == 'moneyline':
        if deporte == 'basquetbol':
            return {'local': 0.54, 'visitante': 0.46}
        return {'local': 0.42, 'empate': 0.30, 'visitante': 0.28}
    if mercado == 'totales':
        return {'over': 0.51, 'under': 0.49}
    if mercado == 'handicap':
        return {'local': 0.47, 'visitante': 0.53}
    return {'si': 0.33, 'no': 0.67}


def ventaja_local(ranking_local, ranking_visitante):
    """Ranking 1 es el mejor; 0 significa sin ranking y no ajusta."""
    if not ranking_local or not ranking_visitante:
        return 0.0
    ventaja = (ranking_visitante - ranking_local) * AJUSTE_POR_PUESTO
    return max(-AJUSTE_MAXIMO, min(AJUSTE_MAXIMO, ventaja))


def normalizar(probabilidades):
    acotadas = {k: max(PROBABILIDAD_MINIMA, v) for k, v in probabilidades.items()}
    total = sum(acotadas.values())
    return {k: round(v / total, 4) for k, v in acotadas.items()}


def calcular(deporte, mercado, ranking_local=0, ranking_visitante=0):
    probabilidades = base(deporte, mercado)
    ventaja = ventaja_local(ranking_local, ranking_visitante)

    if mercado == 'moneyline':
        probabilidades['local'] += ventaja
        probabilidades['visitante'] -= ventaja
    elif mercado == 'handicap':
        probabilidades['local'] += ventaja / 2
        probabilidades['visitante'] -= ventaja / 2

    probabilidades = normalizar(probabilidades)
    mas_probable = max(probabilidades, key=probabilidades.get)
    return {
        'mercado': mercado,
        'probabilidades': probabilidades,
        'mas_probable': mas_probable,
        'valor_esperado': probabilidades[mas_probable],
        'version_modelo': VERSION_MODELO,
    }


def _ranking(datos, campo):
    valor = datos.get(campo, 0)
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise ErrorValidacion(f'"{campo}" debe ser un entero mayor o igual a 0.', campo)
    return valor


def validar(datos):
    if not isinstance(datos, dict):
        raise ErrorValidacion('El cuerpo debe ser un objeto JSON.')

    deporte = datos.get('deporte')
    if not isinstance(deporte, str) or not deporte.strip():
        raise ErrorValidacion('"deporte" es obligatorio.', 'deporte')

    mercados = datos.get('mercados')
    if not isinstance(mercados, list) or not mercados:
        raise ErrorValidacion('"mercados" debe ser una lista no vacia.', 'mercados')
    invalidos = [m for m in mercados if m not in MERCADOS]
    if invalidos:
        raise ErrorValidacion(
            f'Mercados no soportados: {", ".join(map(str, invalidos))}. '
            f'Use: {", ".join(MERCADOS)}.',
            'mercados',
        )

    return {
        'deporte': deporte.strip().lower(),
        'mercados': list(dict.fromkeys(mercados)),
        'ranking_local': _ranking(datos, 'ranking_local'),
        'ranking_visitante': _ranking(datos, 'ranking_visitante'),
    }


def pronosticar(datos):
    entrada = validar(datos)
    return {
        'deporte': entrada['deporte'],
        'pronosticos': [
            calcular(
                entrada['deporte'],
                mercado,
                entrada['ranking_local'],
                entrada['ranking_visitante'],
            )
            for mercado in entrada['mercados']
        ],
    }
