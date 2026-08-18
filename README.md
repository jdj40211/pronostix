# Pronostix

Plataforma de **proyecciones estadísticas para apuestas deportivas** de cualquier deporte y liga. Es análisis de entretenimiento: muestra probabilidades; **nunca recibe apuestas**. Los cobros (suscripción y pase premium) pasan por una **pasarela de pago propia**.

Autores: Juan David Sierra, Juan José Palacio, Camilo Soto.

## Taller 01 — flujo crítico

**Comprar pase premium de un Evento**, refactorizado a capas: CBV delgada, `CompraService`, `OrdenBuilder` y `PasarelaFactory` (`ENV_TYPE=MOCK` / `REAL`).

Documentación: Wiki del repo, página **[Implementación del Patrón Creacional](https://github.com/jdj40211/pronostix/wiki)**.

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
  views.py              Capa de interfaz (CBV delgada)
  services.py           CompraService y PrediccionService
  domain/builders.py    Patron Builder (Fluent Interface)
  domain/acceso.py      Derecho de uso (pase o suscripcion)
  domain/modelo.py      Calculo de probabilidades por deporte
  domain/interfaces.py  Abstraccion PasarelaPago (DIP)
  infra/factories.py    Patron Factory (ENV_TYPE)
  infra/gateways.py     MOCK (consola) y REAL (pasarela propia)
```

## Tests

```powershell
python manage.py test
```

## Contenido de dominio

- `Pronostix-Actividad1.pdf` — Actividad 1: diseño del núcleo de negocio (15 entidades, 3 módulos).
