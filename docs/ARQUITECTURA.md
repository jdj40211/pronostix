# Arquitectura de Pronostix (Entregable 2)

Ecosistema híbrido desplegado en **una instancia EC2 de AWS Academy** con Docker
Compose. Nginx es la única puerta pública; Django queda como orquestador del
monolito y la lógica de negocio migrada vive en cuatro microservicios Flask.

## 1. Despliegue en AWS

```mermaid
flowchart TB
    U([Usuario / equipo aliado]) -->|HTTP :80| EIP[IP elástica de AWS]

    subgraph AWS["AWS Academy · us-east-1"]
        EIP --> SG{{"Security Group<br/>22 SSH · 80 HTTP · 443"}}
        subgraph EC2["EC2 t3.medium · Amazon Linux 2023 · Docker Compose"]
            NG["Nginx 1.25<br/>API Gateway"]

            subgraph MONO["Monolito (Strangler en curso)"]
                DJ["Django + Gunicorn<br/>HTML · /api/v1/*<br/>i18n ES/EN"]
                WK["Celery worker<br/>tareas de fondo"]
            end

            subgraph MS["Microservicios Flask (/api/v2/*)"]
                F1["pronosticos :5000<br/>motor de probabilidades"]
                F2["pagos :5001<br/>pasarela MOCK / REAL"]
                F3["catalogo :5002<br/>eventos · mercados · IVA"]
                F4["estadisticas :5003<br/>Adapter a terceros"]
            end

            PG[("PostgreSQL 15")]
            RD[("Redis 7<br/>Message Broker")]
        end
    end

    NG -->|"/ , /admin , /api/v1/*"| DJ
    NG -->|"/api/v2/pronosticos"| F1
    NG -->|"/api/v2/pagos"| F2
    NG -->|"/api/v2/catalogo"| F3
    NG -->|"/api/v2/estadisticas"| F4

    DJ -->|HTTP| F1
    DJ -->|HTTP| F2
    DJ -->|HTTP| F3
    DJ -->|HTTP| F4
    DJ --> PG
    DJ -->|"publica tarea"| RD
    RD -->|"consume tarea"| WK
    WK --> PG

    F4 -.->|"Adapter (DIP)"| TS[(TheSportsDB<br/>API de terceros)]
    DJ -.->|"ClienteAliado"| AL[(API del equipo aliado)]

    classDef pub fill:#fff3cd,stroke:#b8860b;
    class NG,EIP,SG pub;
```

Solo el puerto 80 (Nginx) está publicado. Django (8000) y los Flask
(5000 a 5003) quedan en la red interna de Compose y no se alcanzan desde afuera.

## 2. Flujo de una compra (síncrono + asíncrono)

```mermaid
sequenceDiagram
    autonumber
    actor C as Cliente
    participant N as Nginx
    participant D as Django
    participant P as pagos (Flask)
    participant K as catalogo (Flask)
    participant R as Redis
    participant W as Celery worker

    C->>N: POST /api/v1/comprar/
    N->>D: proxy
    D->>P: procesar pago
    P-->>D: aprobada + referencia
    D->>K: sincronizar pase
    D-)R: encola notificar_compra_pase
    D-->>C: 201 orden pagada
    R-)W: entrega la tarea
    W->>W: registra la notificación
    Note over D,R: Si Redis no responde, la orden ya pagada<br/>sigue en 201: el fallo del broker no la tumba.
```

## 3. Estrategia Strangler

| Capacidad | Antes (Entregable 1) | Ahora | Ruta pública |
|---|---|---|---|
| Motor de pronósticos | `domain/modelo.py` en Django | `microservicio_pronosticos` | `/api/v2/pronosticos` |
| Pasarela de pago | `infra/gateways.py` en Django | `microservicio_pagos` | `/api/v2/pagos` |
| Catálogo, mercados, IVA | `services.py` en Django | `microservicio_catalogo` | `/api/v2/catalogo` |
| Estadísticas externas | llamada directa | `microservicio_estadisticas` | `/api/v2/estadisticas` |
| HTML, admin, compra v1 | Django | Django (orquestador) | `/`, `/admin`, `/api/v1/*` |

## 4. Resiliencia

- **Compra sin broker:** si Redis cae, la orden pagada responde 201 y se registra
  el aviso de que la notificación no se encoló.
- **Estadísticas externas caídas:** el Adapter degrada a "no disponible" y el
  detalle del evento sigue respondiendo 200.
- **Aliado caído o sin URL:** `ClienteAliado` muestra el contrato de respaldo.
- **Reinicio de la instancia:** los 9 servicios usan `restart: unless-stopped`.
