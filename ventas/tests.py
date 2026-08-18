from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from ventas.domain.acceso import AccesoMercado
from ventas.domain.builders import OrdenBuilder
from ventas.domain.modelo import MotorPronostico
from ventas.infra.factories import PasarelaFactory
from ventas.infra.gateways import MockPasarela, PasarelaPronostix
from ventas.models import Competicion, Equipo, Evento, Mercado, Orden, Plan, Suscripcion
from ventas.services import CompraService, PrediccionService


class _Fixtures:
    def crear_evento(self, precio=12000, estado='programado'):
        competicion = Competicion.objects.create(
            nombre='Liga BetPlay', deporte='futbol', temporada='2026-1', pais='Colombia',
        )
        local = Equipo.objects.create(nombre='Nacional', pais='Colombia', deporte='futbol')
        visitante = Equipo.objects.create(nombre='Millonarios', pais='Colombia', deporte='futbol')
        return Evento.objects.create(
            competicion=competicion,
            local=local,
            visitante=visitante,
            fecha=timezone.now() + timedelta(days=2),
            fase='Cuadrangulares',
            sede='Medellin',
            estado=estado,
            es_premium=True,
            precio_pase=precio,
        )


class OrdenBuilderTest(TestCase, _Fixtures):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user('camilo_soto', password='x')
        self.evento = self.crear_evento()

    def test_build_valida_y_calcula_total_con_iva(self):
        orden = (
            OrdenBuilder()
            .para_usuario(self.usuario)
            .con_pase_de(self.evento)
            .build()
        )
        self.assertEqual(orden.total, Decimal('14280.00'))
        self.assertEqual(orden.lineas.count(), 1)
        self.assertEqual(orden.lineas.first().evento, self.evento)

    def test_rechaza_datos_incompletos(self):
        with self.assertRaises(ValueError):
            OrdenBuilder().para_usuario(self.usuario).build()

    def test_rechaza_evento_finalizado(self):
        self.evento.estado = 'finalizado'
        self.evento.save()
        with self.assertRaises(ValueError):
            OrdenBuilder().para_usuario(self.usuario).con_pase_de(self.evento).build()

    def test_rechaza_plan_gratuito(self):
        plan = Plan.objects.create(
            nombre='Free', precio_mensual=0, mercados_incluidos='moneyline', limite_consultas_dia=5,
        )
        with self.assertRaises(ValueError):
            OrdenBuilder().para_usuario(self.usuario).con_plan(plan).build()


class PasarelaFactoryTest(TestCase):
    def test_mock_usa_consola(self):
        import os
        os.environ['ENV_TYPE'] = 'MOCK'
        try:
            self.assertIsInstance(PasarelaFactory.get_pasarela(), MockPasarela)
        finally:
            os.environ.pop('ENV_TYPE', None)

    def test_real_usa_pasarela_propia(self):
        import os
        os.environ['ENV_TYPE'] = 'REAL'
        try:
            self.assertIsInstance(PasarelaFactory.get_pasarela(), PasarelaPronostix)
        finally:
            os.environ.pop('ENV_TYPE', None)


class CompraServiceTest(TestCase, _Fixtures):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user('camilo_soto', password='x')
        self.evento = self.crear_evento()
        self.factory = RequestFactory()

    def test_orquesta_builder_y_pasarela(self):
        pasarela = MagicMock()
        pasarela.procesar.return_value = True
        servicio = CompraService(pasarela=pasarela)
        request = self.factory.post(f'/comprar/{self.evento.id}/')
        request.user = self.usuario
        ctx = servicio.crear(request, self.evento.id)
        self.assertIn('mensaje_exito', ctx)
        self.assertTrue(Orden.objects.filter(estado='pagada').exists())
        pasarela.procesar.assert_called_once()


class ComprarPaseViewTest(TestCase, _Fixtures):
    def setUp(self):
        self.evento = self.crear_evento()

    def test_get_muestra_formulario(self):
        response = self.client.get(reverse('comprar_pase', args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)

    def test_post_crea_orden_pagada(self):
        response = self.client.post(reverse('comprar_pase', args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Orden.objects.filter(estado='pagada').count(), 1)


class AccesoMercadoTest(TestCase, _Fixtures):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user('camilo_soto', password='x')
        self.evento = self.crear_evento()
        self.free = Mercado.objects.create(evento=self.evento, tipo='moneyline', es_premium=False)
        self.premium = Mercado.objects.create(evento=self.evento, tipo='totales', es_premium=True)

    def test_moneyline_free_siempre_visible(self):
        self.assertTrue(AccesoMercado.puede_ver(self.usuario, self.free))

    def test_premium_bloqueado_sin_pase(self):
        self.assertFalse(AccesoMercado.puede_ver(self.usuario, self.premium))

    def test_premium_se_abre_con_pase_pagado(self):
        OrdenBuilder().para_usuario(self.usuario).con_pase_de(self.evento).build()
        Orden.objects.filter(usuario=self.usuario).update(estado='pagada')
        self.assertTrue(AccesoMercado.puede_ver(self.usuario, self.premium))

    def test_premium_se_abre_con_plan_vigente(self):
        plan = Plan.objects.create(
            nombre='Premium',
            precio_mensual=39000,
            mercados_incluidos='moneyline, totales, handicap',
            limite_consultas_dia=50,
        )
        ahora = timezone.now()
        Suscripcion.objects.create(
            usuario=self.usuario,
            plan=plan,
            fecha_inicio=ahora,
            fecha_fin=ahora + timedelta(days=30),
            estado='activa',
        )
        self.assertTrue(AccesoMercado.puede_ver(self.usuario, self.premium))


class MotorPronosticoTest(TestCase):
    def test_futbol_moneyline_suma_uno(self):
        probs = MotorPronostico.calcular_probabilidades('futbol', 'moneyline')
        self.assertAlmostEqual(sum(probs.values()), 1.0)
        self.assertIn('empate', probs)


class EventoDetalleViewTest(TestCase, _Fixtures):
    def setUp(self):
        self.evento = self.crear_evento()
        Mercado.objects.create(evento=self.evento, tipo='moneyline', es_premium=False)
        Mercado.objects.create(evento=self.evento, tipo='totales', es_premium=True)
        PrediccionService().generar_para(self.evento)

    def test_get_muestra_mercados(self):
        response = self.client.get(reverse('evento_detalle', args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'moneyline')
        self.assertContains(response, 'bloqueado')
