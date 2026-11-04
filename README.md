# Pronostix

Plataforma de **proyecciones estadísticas para apuestas deportivas** de cualquier deporte y liga. Es análisis de entretenimiento: muestra probabilidades; **nunca recibe apuestas**. Los cobros (suscripción y pase premium) pasan por una **pasarela de pago propia**.

Autores: Juan David Sierra, Juan José Palacio, Camilo Soto.

## Taller 01 / Entregable 1 (avance)

Flujo critico **comprar pase premium**: CBV y APIView delgadas, logica en `CompraService`, `OrdenBuilder` y `PasarelaFactory`. Los modelos Django solo persisten; las reglas viven en `domain/`.

Documentacion del patron creacional: Wiki **[Implementación del Patrón Creacional](https://github.com/jdj40211/pronostix/wiki)**.

## Cómo ejecutar (local, sin Docker)

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_pronostix
python manage.py runserver
```

Abra http://127.0.0.1:8000/ para ver eventos. El **moneyline** es free; totales y handicap se desbloquean con el pase del evento o un plan Premium/Pro vigente. Selector de idioma ES/EN en el encabezado.

Para Celery en local (opcional): levante Redis y un worker:

```powershell
docker run -d -p 6379:6379 redis:7-alpine
$env:CELERY_BROKER_URL="redis://localhost:6379/0"
celery -A config worker -l info
```

## Factory: MOCK vs REAL

```powershell
# Consola (sin log real)
$env:ENV_TYPE="MOCK"; python manage.py runserver

# Log de auditoria pasarela_CAMILO_SOTO.log
$env:ENV_TYPE="REAL"; python manage.py runserver

# Estadisticas externas (TheSportsDB) via Adapter
$env:STATS_PROVIDER="REAL"; python manage.py runserver
```

## Estructura

```
ventas/
  views.py              Capa de interfaz (CBV delgada, sin ORM)
  api/views.py          APIView + serializers (sin logica de negocio)
  services.py           CompraService, CatalogoService, PrediccionService
  tasks.py              Celery: notificacion asincrona post-compra
  domain/logic.py       IVA, reglas de plan y evento
  domain/builders.py    Patron Builder (Fluent Interface)
  domain/acceso.py      Derecho de uso (pase o suscripcion)
  domain/modelo.py      Calculo de probabilidades por deporte
  domain/interfaces.py  PasarelaPago + ProveedorEstadisticas (DIP)
  infra/factories.py    PasarelaFactory + EstadisticasFactory
  infra/gateways.py     MOCK (consola) y REAL (pasarela propia)
  infra/estadisticas.py Adapter TheSportsDB / Mock
  infra/aliado.py       Cliente HTTP del equipo aliado
locale/                 gettext ES/EN
```

## API

```powershell
# Listar eventos
curl http://127.0.0.1:8000/api/v1/eventos/

# Integracion (JSON para el equipo aliado)
curl http://127.0.0.1:8000/api/v1/integracion/

# Comprar pase (201). Si el evento no existe: 404. Si ya hay pase o esta finalizado: 409.
curl -X POST http://127.0.0.1:8000/api/v1/comprar/ -H "Content-Type: application/json" -d "{\"evento_id\": 1}"
```

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

## Entregable 2: Integracion y resiliencia (+ bono >70%)

Arquitectura hibrida: Django queda como orquestador HTML/compra v1; **mas del 70%**
de la logica de negocio vive en microservicios Flask independientes.

| Microservicio | Ruta Nginx | Logica |
|---|---|---|
| `pronosticos_flask` | `/api/v2/pronosticos/` | Motor de probabilidades |
| `pagos_flask` | `/api/v2/pagos/` | Pasarela MOCK/REAL |
| `catalogo_flask` | `/api/v2/catalogo/` | Eventos, mercados, IVA, integracion |
| `estadisticas_flask` | `/api/v2/estadisticas/` | Adapter TheSportsDB / Mock |

```
Cliente → Nginx → Django (HTML + /api/v1/compra)
                → Flask x4 (/api/v2/*)
                → Redis ← Celery worker
Django --HTTP--> pagos / catalogo / estadisticas / pronosticos
```

```powershell
docker compose up -d --build
docker compose ps
# db + redis + worker + web_django + 4 flask + nginx

curl http://localhost/api/v2/catalogo/eventos/
curl http://localhost/api/v2/pagos/salud
curl http://localhost/api/v2/estadisticas/salud
curl -X POST http://localhost/api/v2/pronosticos/ -H "Content-Type: application/json" -d "{\"deporte\":\"futbol\",\"mercados\":[\"moneyline\"]}"

# Tras comprar un pase, el worker registra la notificacion:
docker compose logs worker
```

Variables utiles:

| Variable | Default | Uso |
|---|---|---|
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Broker Celery |
| `ALIADO_API_URL` | vacio | URL JSON del equipo aliado |
| `STATS_PROVIDER` | `MOCK` | `MOCK` o `REAL` (TheSportsDB) |
| `PAGOS_URL` | (compose) `http://pagos_flask:5001` | MS pasarela |
| `CATALOGO_URL` | (compose) `http://catalogo_flask:5002` | MS catalogo |
| `ESTADISTICAS_URL` | (compose) `http://estadisticas_flask:5003` | MS stats |
| `NGINX_PORT` | `80` | Puerto publicado del gateway |

### Despliegue en AWS Academy (EC2 + Docker Compose)

Arquitectura completa con diagramas (AWS, Nginx, Flask, Redis): [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md).

En una EC2 Amazon Linux 2023 (t3.medium, 20 GB, Security Group con 22 y 80 abiertos) el
ecosistema completo se levanta con un solo comando, que instala Docker y el plugin de
Compose, crea 2 GB de swap, clona el repo y corre `docker compose up -d --build`:

```bash
curl -fsSL https://raw.githubusercontent.com/jdj40211/pronostix/main/deploy/ec2-bootstrap.sh | bash
```

Variables del script: `RAMA` (default `main`), `STATS_PROVIDER` (default `REAL`, usa
TheSportsDB) y `ALIADO_API_URL` (opcional, endpoint JSON del equipo aliado).

Tras apagar y volver a iniciar el laboratorio, los 9 servicios se recuperan solos
(`restart: unless-stopped`); la IP elástica no cambia.

### CI/CD y Swarm (AWS Academy)

1. En GitHub → Settings → Secrets: `DOCKERHUB_USER`, `DOCKERHUB_PASS`.
2. Push a `main` dispara `.github/workflows/main.yml` y publica imagenes en Docker Hub.
3. En EC2 (manager): `docker swarm init` y en el worker: `docker swarm join ...`.
4. Despliegue: `DOCKERHUB_USER=tu_usuario docker stack deploy -c docker-stack.yml pronostix`.

Security Group: 22, 80, 2377/tcp, 7946/tcp+udp, 4789/udp.

Wiki: **[Entregable 2 - Integración y Resiliencia](https://github.com/jdj40211/pronostix/wiki/Entregable-2-Integraci%C3%B3n-y-Resiliencia)**.

## Tests

```powershell
$env:CELERY_TASK_ALWAYS_EAGER="1"
python manage.py test
cd microservicio_pronosticos; python -m unittest -v
cd ..\microservicio_pagos; python -m unittest -v
cd ..\microservicio_catalogo; python -m unittest -v
cd ..\microservicio_estadisticas; python -m unittest -v
```

## Contenido de dominio

- `Pronostix-Actividad1.pdf` — Actividad 1: diseño del núcleo de negocio (15 entidades, 3 módulos).
