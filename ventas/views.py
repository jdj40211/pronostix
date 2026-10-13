from django.http import Http404
from django.shortcuts import render
from django.views import View

from .domain.exceptions import EventoNoEncontrado
from .infra.factories import PasarelaFactory
from .services import CatalogoService, CompraService, PrediccionService


class CatalogoView(View):
    def get(self, request):
        return render(request, 'ventas/catalogo.html', CatalogoService().portada(request))


class ComprarPaseView(View):
    template_name = 'ventas/comprar.html'

    def setup_service(self):
        return CompraService(pasarela=PasarelaFactory.get_pasarela())

    def get(self, request, evento_id):
        try:
            ctx = self.setup_service().preparar(request, evento_id)
        except EventoNoEncontrado as exc:
            raise Http404(str(exc)) from exc
        return render(request, self.template_name, ctx)

    def post(self, request, evento_id):
        try:
            ctx = self.setup_service().crear(request, evento_id)
        except EventoNoEncontrado as exc:
            raise Http404(str(exc)) from exc
        if ctx.get('conflicto'):
            codigo = 409
        elif ctx.get('error'):
            codigo = 400
        else:
            codigo = 200
        return render(request, self.template_name, ctx, status=codigo)


class EventoDetalleView(View):
    def get(self, request, evento_id):
        try:
            ctx = PrediccionService().detalle(request, evento_id)
        except EventoNoEncontrado as exc:
            raise Http404(str(exc)) from exc
        return render(request, 'ventas/evento.html', ctx)
