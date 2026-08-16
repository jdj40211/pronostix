class MotorPronostico:
    """
    SRP: solo calcula probabilidades.
    El modelo se calibra por deporte para no reescribir el nucleo (OCP).
    """

    @staticmethod
    def calcular_probabilidades(deporte, tipo):
        deporte = (deporte or '').lower()
        if tipo == 'moneyline':
            if deporte == 'basquetbol':
                return {'local': 0.54, 'visitante': 0.46}
            return {'local': 0.42, 'empate': 0.30, 'visitante': 0.28}
        if tipo == 'totales':
            return {'over': 0.51, 'under': 0.49}
        if tipo == 'handicap':
            return {'local': 0.47, 'visitante': 0.53}
        return {'si': 0.33, 'no': 0.67}

    @classmethod
    def valor_esperado(cls, probabilidades):
        if not probabilidades:
            return 0.0
        top = max(probabilidades.values())
        return round(top, 4)
