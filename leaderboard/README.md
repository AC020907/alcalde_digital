# Civitas Leaderboard

API de clasificacion en linea para *Alcalde Digital / Civitas* (FastAPI + SQLAlchemy Core) y pagina publica `GET /` pensada para una TV en el stand y para moviles.

- Local: SQLite, sin configuracion.
- Produccion gratuita: Render (web service free) + Postgres gratuito (Neon o Supabase) via `DATABASE_URL`.

## Ejecutar en local

```bash
cd leaderboard
pip install -r requirements-dev.txt
uvicorn app.main:app --port 8000
```

Abre http://localhost:8000/ . La base se crea en `leaderboard.db` (ignorada por git). En local `ENV=development`, asi que CORS permite `*`.

## Pruebas

```bash
cd leaderboard
python -m pytest -q
```

Cada prueba usa una base SQLite temporal.

## Variables de entorno

| Variable | Descripcion | Por defecto | Produccion (Render) |
|---|---|---|---|
| `DATABASE_URL` | Cadena de conexion Postgres (`postgresql://...?sslmode=require`) o SQLite | `sqlite:///./leaderboard.db` | cadena de Neon |
| `ENV` | `production` desactiva el CORS `*` (incluso si se escribe en `ALLOWED_ORIGINS`) | `development` | `production` |
| `ALLOWED_ORIGINS` | Origenes permitidos, separados por coma | `*` si no es produccion; vacio en produccion | `https://ac020907.github.io` |
| `TRUST_PROXY` | `1` para leer la IP real de `True-Client-IP`/`CF-Connecting-IP` (Cloudflare) o, si faltan, de `X-Forwarded-For` | `0` | `1` |
| `ADMIN_TOKEN` | Activa `DELETE /api/admin/scores/{run_id}`; con menos de 16 caracteres queda desactivado | vacio | secreto aleatorio largo (`generateValue` en `render.yaml`) |
| `RATE_SCORES_PER_HOUR` | Envios `POST /api/scores` por IP y hora | 60 | **300 durante la feria** |
| `RATE_START_PER_HOUR` | `POST /api/runs/start` por IP y hora | 120 | **600 durante la feria** |
| `RATE_GET_PER_MIN` | Lecturas (GET) por IP y minuto | 120 | **600 durante la feria** |
| `RATE_ADMIN_PER_HOUR` | Intentos `DELETE /api/admin/...` por IP y hora | 30 | 30 |
| `RATE_PLAYER_SCORES_PER_HOUR` | Envios nuevos por `player_id` y hora (los reenvios duplicados no cuentan) | 20 | 20 |
| `RATE_PLAYER_START_PER_HOUR` | Partidas iniciadas por `player_id` y hora | 20 | 20 |
| `VERIFY_MIN_S_FERIA` / `VERIFY_MIN_S_FERIA_HIGH` | Segundos minimos medidos por el servidor para verificar una partida feria (cualquier puntuacion / puntuacion alta) | 180 / 300 | igual |
| `VERIFY_MIN_S_HISTORIA` / `VERIFY_MIN_S_HISTORIA_HIGH` | Lo mismo para historia | 600 / 900 | igual |
| `VERIFY_HIGH_SCORE` | Desde que puntuacion se aplica el minimo "alto" | 700 | igual |

Nota para la feria: los limites `RATE_*` sin `PLAYER` son por IP. En la WiFi del recinto todos los moviles salen por **una sola IP publica**, asi que comparten ese cupo: sube `RATE_SCORES_PER_HOUR`, `RATE_START_PER_HOUR` y `RATE_GET_PER_MIN` en Render durante el evento (valores de la tabla). El freno real por persona son los limites por `player_id`.

## Despliegue gratuito (Render + Neon)

1. **Neon**: crea una cuenta en https://neon.tech, pulsa *New Project*, elige region cercana y crea el proyecto. En el *Dashboard* pulsa *Connect* y copia la *connection string* (`postgresql://usuario:clave@host/neondb?sslmode=require`).
2. Sube el repositorio a GitHub (la carpeta `leaderboard/` debe estar en el repo).
3. **Render**: en https://render.com pulsa *New +* > *Web Service* > conecta el repo de GitHub.
   - *Root Directory*: `leaderboard`
   - *Runtime*: Python 3 | *Instance Type*: Free
   - *Build Command*: `pip install -r requirements.txt`
   - *Start Command*: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - *Health Check Path*: `/api/health`
   (Alternativa: *New +* > *Blueprint* usando `render.yaml`.)
4. En *Environment* define:
   - `DATABASE_URL` = la cadena de Neon
   - `ENV` = `production`
   - `TRUST_PROXY` = `1`
   - `ALLOWED_ORIGINS` = `https://ac020907.github.io`
   - `ADMIN_TOKEN` = un secreto aleatorio de 32+ caracteres (opcional, para moderar; nunca en el cliente)
   - Durante la feria: `RATE_SCORES_PER_HOUR=300`, `RATE_START_PER_HOUR=600`, `RATE_GET_PER_MIN=600`
5. Despliega. La URL sera `https://<nombre>.onrender.com`. Las tablas se crean solas al arrancar.

El plan free de Render duerme el servicio tras ~15 min sin trafico (el primer request tarda ~30-60 s). Antes de la feria, abre la pagina o llama a `/api/health` para despertarlo. Con Supabase el procedimiento es igual: usa la cadena del *Session pooler* en `DATABASE_URL`.

### ALLOWED_ORIGINS para el juego web

Es el origen (esquema + host + puerto, sin ruta ni barra final) desde el que se sirve el export HTML5 de Ren'Py, p. ej.:

```
ALLOWED_ORIGINS=https://ac020907.github.io
```

El cliente de escritorio no envia `Origin`, asi que funciona siempre. Si sirves el juego web desde el mismo servicio no necesitas CORS.

La pagina `/static/qr.png`: guarda tu QR en `app/static/qr.png`; si el archivo no existe, el recuadro se oculta.

## Ejemplos curl

```bash
BASE=http://localhost:8000
curl $BASE/api/health

# 1) Iniciar partida (opcional; permite marcar la puntuacion como verificada)
curl -X POST $BASE/api/runs/start -H "Content-Type: application/json" \
  -d '{"player_id":"3f2b8c1e-5d4a-4b7e-9c1a-2e6f8a0b1c3d","mode":"historia","platform":"pc","version":"2.0"}'

# 2) Enviar puntuacion
curl -X POST $BASE/api/scores -H "Content-Type: application/json" -d '{
  "run_id":"<run_id de /runs/start o un uuid4 propio>",
  "player_id":"3f2b8c1e-5d4a-4b7e-9c1a-2e6f8a0b1c3d",
  "alias":"Ciudadano-4821","platform":"pc","mode":"historia","final":"informada","score":742,
  "components":{"verificacion":240,"decisiones":190,"minijuegos":150,"investigacion":90,"ciudad":72},
  "evidencias":2,"duration_s":1650,"finales_desbloqueados":["dividida","informada"],"version":"2.0"}'

curl "$BASE/api/leaderboard?mode=feria&limit=10"
curl "$BASE/api/leaderboard?mode=feria&include_unverified=1"
curl $BASE/api/players/3f2b8c1e-5d4a-4b7e-9c1a-2e6f8a0b1c3d

# Moderacion (solo si ADMIN_TOKEN esta definido)
curl -X DELETE $BASE/api/admin/scores/<run_id> -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Contrato de la API

Todo JSON bajo `/api`. Errores: `{"error": "codigo", "detail": "mensaje en espanol"}`.

**Finales**: `informada` Ciudad Informada, `dividida` Ciudad Dividida, `caos` Caos Informativo, `mandato` Mandato Prestado, `secreto` Fuente Abierta. **Modos**: `historia`, `feria`. **Plataformas**: `pc`, `web`.
**Componentes (maximo)**: `verificacion` 300, `decisiones` 250, `minijuegos` 200, `investigacion` 150, `ciudad` 100. Puntuacion Civica maxima 1000 y `score` = suma de componentes.

| Metodo y ruta | Descripcion |
|---|---|
| `GET /api/health` | `{"ok": true}` |
| `POST /api/runs/start` | Body `{player_id, mode, platform, version}` -> `{run_id, started_at}` |
| `POST /api/scores` | Body del ejemplo anterior -> `{accepted, verified, ranked, duplicate, rank, personal_best, top[10]}` |
| `GET /api/leaderboard?mode=historia\|feria\|all&limit=1..50&include_unverified=0\|1` | `{entries: [{rank, alias, score, final, final_title, mode, platform, verified, created_at}]}` |
| `GET /api/players/{player_id}` | `{best_score, best_final, runs, finales_desbloqueados, rank, ranked}` o 404 |
| `DELETE /api/admin/scores/{run_id}` | Solo con `ADMIN_TOKEN` (Bearer); 404 si esta desactivado |
| `GET /` | Pagina HTML de la tabla de honor |

Detalles:

- La tabla publica (`/api/leaderboard` y `top`) muestra solo partidas **verificadas**; `include_unverified=1` las incluye todas. `personal_best` y `/api/players` cuentan tambien las no verificadas del propio jugador.
- `rank` es la posicion del jugador en la tabla publica de ese modo. Si aun no tiene partidas verificadas (`ranked=false`), `rank` es el puesto que tendria su mejor partida.
- Una entrada por jugador y modo (su mejor); empates se resuelven por envio mas temprano.
- Reenviar el mismo `run_id` devuelve el resultado original con `"duplicate": true`, sin crear otra fila ni cambiar la puntuacion (409 si lo envia otro `player_id`).
- Ver la seccion *Seguridad* para las reglas de validacion y verificacion.
- No se guarda la IP; solo se usa un hash en memoria para los limites.

## Seguridad

### Modelo de amenazas

El cliente (Ren'Py, escritorio y web) es codigo del jugador: cualquiera puede leerlo, editarlo o llamar a la API con `curl`. No hay cuentas, captcha ni servidor autoritativo del juego, asi que **el servidor no puede saber si una puntuacion se jugo de verdad**. Objetivos realistas:

1. Que un jugador honesto **nunca** sea rechazado (peor que aceptar a un tramposo en una feria).
2. Que hacer trampa en la tabla publica cueste tiempo real y deje rastro, y que lo absurdo se rechace.
3. Que nadie pueda tumbar el servicio, borrar datos ni obtener secretos.

### Lo que se aplica

- **Validacion estricta (422)**: tipos estrictos, campos desconocidos prohibidos, ids uuid4, alias 3-20 caracteres permitidos y sin groserias, componentes dentro de su maximo y `score` = suma.
- **Invariantes derivados de `game/clases/Puntuacion.py`** (un cliente legitimo no puede violarlos; hay pruebas que generan 20 000 partidas con el codigo real del juego):
  - `investigacion = 30 * evidencias + 6 * k` con `0 <= k <= 10` (cada grupo clave vale 30, cada pista extra 6, extras hasta 60).
  - `secreto` exige `evidencias == 3` e `investigacion >= 96` (el final siempre agrega la pista `conclusion_resonancia`).
  - `caos` exige `ciudad <= 50`; `informada` exige `ciudad >= 50`; `finales_desbloqueados` sin duplicados e incluye el final.
- **Partidas verificadas**: `verified=true` solo si el `run_id` salio de `/runs/start` para ese mismo `player_id`, modo y plataforma; se envia una sola vez; han pasado como mucho 24 h; `duration_s` del cliente no supera el tiempo medido por el servidor + 120 s; y el tiempo medido por el servidor alcanza el minimo segun la puntuacion (feria 3 min, o 5 min si `score >= 700`; historia 10 min, o 15 min si `score >= 700`; tiempos reales: feria 6-10 min, historia 25-45 min). Lo que no cumple se **guarda igualmente** como no verificado (200): no se pierde, pero no entra en la tabla publica.
- **Ciclo de vida**: `run_id` de otro jugador -> 409; partida iniciada ya enviada -> 409; reenvio identico (cola offline del cliente) -> 200 idempotente. Una partida iniciada hace mas de 24 h se acepta como no verificada (antes 410). Las partidas iniciadas se borran a los 7 dias.
- **Limites**: por IP (token bucket en memoria, 429 con `Retry-After`) y por `player_id` (inicios y envios nuevos por hora). El cliente trata 429 como "reintentar luego" y, si falla `/runs/start`, sigue con un id local (partida no verificada).
- **Cuerpo maximo 4 KB** (413); sin `Content-Length` -> 411.
- **Admin**: desactivado salvo `ADMIN_TOKEN` de 16+ caracteres; comparacion en tiempo constante; intentos limitados por IP. El token solo vive en Render.
- **Sin documentacion publica** (`/docs`, `/redoc`, `/openapi.json` -> 404), errores siempre `{"error","detail"}` sin trazas, SQL solo con SQLAlchemy Core parametrizado, cabeceras `nosniff`, `no-referrer` y CSP en la pagina.
- **CORS**: en produccion solo `https://ac020907.github.io` (el `*` se ignora). El escritorio no envia `Origin` y no depende de CORS.
- **IP real**: Render agrega a un `X-Forwarded-For` enviado por el cliente en lugar de reemplazarlo; con `TRUST_PROXY=1` se usa primero `True-Client-IP`/`CF-Connecting-IP` que pone Cloudflare.
- `/api/players/{id}` exige uuid4 (122 bits aleatorios): no es enumerable y solo expone alias/puntuaciones.

### Riesgos residuales (aceptados)

- **Puntuaciones falsas pero coherentes**: quien edite el cliente puede iniciar una partida, esperar el tiempo minimo y enviar 1000 puntos validos. Queda verificada. Mitigacion: moderacion con `DELETE /api/admin/scores/{run_id}`; en la feria, mirar la tabla.
- **`player_id` es libre**: un tramposo puede generar ids nuevos y saltarse los limites por jugador; solo le frenan los limites por IP, que en la feria son altos a proposito.
- **Limites en memoria**: se reinician cuando Render duerme o redespliega; con varias instancias no se comparten.
- **Partidas legitimas no verificadas**: si `/runs/start` falla (red, o Render dormido: el primer request tarda 30-60 s y el cliente espera 3 s) la partida queda sin verificar. Manten la pagina `/` abierta en la TV del stand (refresca cada 15 s y evita que Render duerma) y abre `/api/health` antes de abrir el stand.
- **Equipo compartido**: el PC del stand guarda un unico `player_id`; todos los visitantes que jueguen ahi comparten una entrada en la tabla (solo cuenta su mejor partida).
- Un HMAC firmado en `/runs/start` no se implemento: el servidor ya guarda la fila de la partida y la valida; un token no anade nada frente a un cliente modificado.
