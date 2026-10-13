# Pronostix

Plataforma de **proyecciones estadísticas para apuestas deportivas** de cualquier deporte y liga. Es análisis de entretenimiento: muestra probabilidades; **nunca recibe apuestas**. Los cobros (suscripción y pase premium) pasan por una **pasarela de pago propia**.

Autores: Juan David Sierra, Juan José Palacio, Camilo Soto.

## Taller 01 / Entregable 1 (avance)

Flujo critico **comprar pase premium**: CBV y APIView delgadas, logica en `CompraService`, `OrdenBuilder` y `PasarelaFactory`. Los modelos Django solo persisten; las reglas viven en `domain/`.

Documentacion del patron creacional: Wiki **[Implementación del Patrón Creacional](https://github.com/jdj40211/pronostix/wiki)**.

## Cómo ejecutar

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_pronostix
python manage.py runserver
```

Abra http://127.0.0.1:8000/ para ver eventos. El **moneyline** es free; totales y handicap se desbloquean con el pase del evento o un plan Premium/Pro vigente.

## Factory: MOCK vs REAL

```powershell
# Consola (sin log real)
$env:ENV_TYPE="MOCK"; python manage.py runserver

# Log de auditoria pasarela_CAMILO_SOTO.log
$env:ENV_TYPE="REAL"; python manage.py runserver
```

## Estructura

```
ventas/
  views.py              Capa de interfaz (CBV delgada, sin ORM)
  api/views.py          APIView + serializers (sin logica de negocio)
  services.py           CompraService, CatalogoService, PrediccionService
  domain/logic.py       IVA, reglas de plan y evento
  domain/builders.py    Patron Builder (Fluent Interface)
  domain/acceso.py      Derecho de uso (pase o suscripcion)
  domain/modelo.py      Calculo de probabilidades por deporte
  domain/interfaces.py  Abstraccion PasarelaPago (DIP)
  infra/factories.py    Patron Factory (ENV_TYPE)
  infra/gateways.py     MOCK (consola) y REAL (pasarela propia)
```

## API (Entregable 1, avance)

```powershell
# Listar eventos
curl http://127.0.0.1:8000/api/v1/eventos/

# Comprar pase (201). Si el evento no existe: 404. Si ya hay pase o esta finalizado: 409.
curl -X POST http://127.0.0.1:8000/api/v1/comprar/ -H "Content-Type: application/json" -d "{\"evento_id\": 1}"
```

La vista API solo valida el serializer y llama a `CompraService`. Builder y Factory siguen en dominio/infra.

## Taller 02: Strangler Pattern (Django + Flask + Nginx)

El motor de pronosticos se extrajo del monolito a `microservicio_pronosticos/` (Flask). Nginx es la unica entrada: `/api/v1/` y las vistas HTML van a Django; `/api/v2/pronosticos/` va a Flask. Justificacion y matriz de decision: Wiki **[Migración a Microservicios (Strangler Pattern)](https://github.com/jdj40211/pronostix/wiki/Migraci%C3%B3n-a-Microservicios-(Strangler-Pattern))**.

```powershell
docker compose up -d --build
docker compose ps

# Django (v1)
curl http://localhost/api/v1/eventos/

# Flask (v2)
curl -X POST http://localhost/api/v2/pronosticos/ -H "Content-Type: application/json" -d "{\"deporte\": \"futbol\", \"mercados\": [\"moneyline\", \"totales\"], \"ranking_local\": 3, \"ranking_visitante\": 12}"
```

Si el puerto 80 esta ocupado: `$env:NGINX_PORT=8080; docker compose up -d`.

```
docker-compose.yml          db (PostgreSQL) + web_django + pronosticos_flask + nginx
Dockerfile                  Imagen del monolito (Gunicorn)
nginx/nginx.conf            Bifurcacion del trafico por URL
microservicio_pronosticos/  app.py (API), motor.py (logica), Dockerfile propio
```

## Tests

```powershell
python manage.py test
cd microservicio_pronosticos; python -m unittest -v
```

## Contenido de dominio

- `Pronostix-Actividad1.pdf` — Actividad 1: diseño del núcleo de negocio (15 entidades, 3 módulos).
