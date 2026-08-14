from django.shortcuts import render
from django.views import View

from .infra.factories import PasarelaFactory
from .models import Evento
from .services import CompraService


class CatalogoView(View):
    def get(self, request):
        return render(request, 'ventas/catalogo.html', {
            'eventos': Evento.objects.select_related('local', 'visitante', 'competicion'),
        })


class ComprarPaseView(View):
    template_name = 'ventas/comprar.html'

    def setup_service(self):
        return CompraService(pasarela=PasarelaFactory.get_pasarela())

    def get(self, request, evento_id):
        return render(request, self.template_name, self.setup_service().preparar(evento_id))

    def post(self, request, evento_id):
        ctx = self.setup_service().crear(request, evento_id)
        return render(request, self.template_name, ctx, status=400 if ctx.get('error') else 200)
