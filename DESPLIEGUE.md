# Despliegue: clasificación online, versión web y QR

Orden obligatorio: **1** (servidor) → **2** (URL en el juego) → **3** (build web) → **4** (GitHub Pages) → **5** (QR) → **6** (stand).
Nada de esto está publicado todavía: cada paso necesita tu cuenta.

## 0. Subir la rama (tú, desde tu terminal)

Render despliega desde la rama `feria/remaster`: **no hace falta tocar `main`**. Los comandos de commit y push están al final de este documento.

## 1. Clasificación online (Render + Neon, gratis)

El backend está en `leaderboard/` (FastAPI). Se probó con 142 pruebas sobre SQLite **y sobre PostgreSQL 18**, y de extremo a extremo con el juego real. Contrato de la API y seguridad: `leaderboard/README.md`.

### 1.1 Neon (base de datos)

1. En neon.tech: *New Project* → nombre `civitas` → región **AWS US East 1 (N. Virginia)**, la misma que Render.
2. *Connect* → copia la *connection string* (`postgresql://...neon.tech/neondb?sslmode=require...`).
3. **No la pegues en el chat ni en ningún archivo del repositorio.** Solo va en la variable `DATABASE_URL` de Render.

### 1.2 Render (backend)

*New → Web Service* → conecta GitHub → repositorio `AC020907/pruebaslaboratorio` (el que se despliega):

| Campo | Valor |
|---|---|
| Name | `civitas-leaderboard` |
| Language | Python 3 |
| Branch | `feria/remaster` |
| Region | Virginia (US East) |
| Root Directory | `leaderboard` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |
| Health Check Path (Advanced) | `/api/health` |

**Environment Variables:**

| Variable | Valor |
|---|---|
| `DATABASE_URL` | la connection string de Neon (secreta) |
| `ENV` | `production` |
| `ALLOWED_ORIGINS` | `https://ac020907.github.io` |
| `TRUST_PROXY` | `1` |
| `PYTHON_VERSION` | `3.12.8` |
| `RATE_SCORES_PER_HOUR`, `RATE_START_PER_HOUR`, `RATE_GET_PER_MIN` | `300`, `600`, `600`: en la feria muchos teléfonos comparten la IP del WiFi |
| `ADMIN_TOKEN` | opcional: 32 caracteres aleatorios, solo si vas a moderar alias |

Cuando termine el despliegue, la URL será parecida a `https://civitas-leaderboard.onrender.com`. Esa URL es pública y sí puedes compartirla para verificarla.

**Verificación** (sin escribir puntuaciones en producción):

```bash
curl https://TU-SERVICIO.onrender.com/api/health?db=1
```

Debe responder `{"ok":true,"db":"ok"}`. Si responde 503, revisa `DATABASE_URL`.

> **Solo las partidas verificadas entran en la tabla pública**: el juego debe poder registrar el inicio de la partida en el servidor. Por eso hay que despertar el servidor antes de abrir el stand.
>
> El plan gratis de Render se duerme tras 15 minutos sin uso: la primera petición tarda unos 50 s. El juego no se bloquea; si no responde, guarda el resultado y lo reenvía en la siguiente partida. Antes de la feria, abre la tabla una vez para despertarlo.

## 2. Conectar el juego con el servidor

Crea `game/leaderboard_url.txt` con una sola línea:

```
https://TU-SERVICIO.onrender.com
```

Sin ese archivo el juego funciona igual, pero guarda los récords solo en el equipo.

## 3. Build web

```bash
"C:/Users/ALEJANDRO/Downloads/renpy-8.5.3-sdk/renpy.exe" "C:/Users/ALEJANDRO/Downloads/renpy-8.5.3-sdk/launcher" web_build "C:/Users/ALEJANDRO/Documents/pruebaslaboratorio" --destination "C:/Users/ALEJANDRO/Documents/pruebaslaboratorio-web"
```

```bash
python tools/web/postbuild.py "C:/Users/ALEJANDRO/Documents/pruebaslaboratorio-web"
```

`postbuild.py` agrega el aviso "gira el teléfono" y el archivo `.nojekyll` que necesita GitHub Pages.

### 3b. Build de Windows

```bash
"C:/Users/ALEJANDRO/Downloads/renpy-8.5.3-sdk/renpy.exe" "C:/Users/ALEJANDRO/Downloads/renpy-8.5.3-sdk/launcher" distribute "C:/Users/ALEJANDRO/Documents/pruebaslaboratorio" --package pc --destination "C:/Users/ALEJANDRO/Documents/civitas-dist"
```

Genera `civitas-dist/<nombre>-pc.zip`. Antes de publicarlo, comprueba que no contenga `.kra`, `personajes/lateral/` ni los `*_base.png` de los cuatro personajes sustituidos (`options.rpy` los excluye).

## 4. Publicar en GitHub Pages

La build se publica en una rama aparte, `gh-pages`, sin mezclarla con el código.

```bash
cd "C:/Users/ALEJANDRO/Documents/pruebaslaboratorio-web"
```

```bash
git init -b gh-pages
```

```bash
git add -A
```

```bash
git commit -m "Version web de Alcalde Digital"
```

```bash
git remote add origin https://github.com/AC020907/pruebaslaboratorio.git
```

```bash
git push -u origin gh-pages
```

En GitHub: *Settings → Pages → Branch:* `gh-pages` / `(root)`. La URL será `https://ac020907.github.io/pruebaslaboratorio/`; ábrela y confirma que el juego carga.

Para publicar una build nueva más adelante, repite el paso 3 y, desde la carpeta de la build, `git add -A`, `git commit` y `git push` (ya sin `git init` ni `remote add`).

## 5. Código QR (solo con la URL ya funcionando)

```bash
python tools/web/generar_qr.py https://ac020907.github.io/pruebaslaboratorio/
```

El script comprueba que la URL responde y que es el juego antes de generar `game/gui/qr_web.png` (pantalla final del Modo Feria) y `leaderboard/app/static/qr.png` (tabla del stand). Después repite los pasos 3 y 4, y vuelve a desplegar el servicio de Render para que la tabla muestre el QR.

## 6. Stand de la feria

- **PC del juego:** pantalla completa (F) → *Modo Feria (10 min)*. Al terminar, *Volver al menú* deja todo listo para el siguiente visitante.
- **Pantalla secundaria:** `https://TU-SERVICIO.onrender.com/` (se actualiza cada 15 s y muestra el QR).
- **Antes de abrir:** borra el progreso de prueba desde el lanzador de Ren'Py (*Delete Persistent*) para que el Archivo de Destinos empiece vacío.
- **Mando:** conéctalo antes de abrir el juego. Controles en *Opciones*.

## Comprobaciones antes de la feria (no se pudieron hacer aquí)

- [ ] Jugar con un **mando físico** las cuatro pruebas y el mapa (la compatibilidad se verificó con eventos de mando simulados).
- [ ] Abrir la web en un **iPhone (Safari)** y un **Android (Chrome)**, en horizontal, y probar el sonido después del primer toque.
- [ ] **Escuchar** voces y música completas (solo se verificaron numéricamente).
- [ ] Una partida completa contra el servidor de Render, con la URL real.


## 6. Arena Online (mejora para la feria)

La Arena Online vive en el **mismo servicio de Render** que el leaderboard (`leaderboard/app/arena_online.py`). No necesita base de datos, variables nuevas ni otro servicio.

1. Haz merge a `main` en `AC020907/pruebaslaboratorio` y `git push`.
2. En Render, abre el servicio `civitas-leaderboard` y pulsa **Manual Deploy → Deploy latest commit**. El auto-deploy está desactivado.
3. Comprueba:
   - `https://civitas-leaderboard.onrender.com/api/health?db=1` responde `{"ok":true,"db":"ok"}`;
   - `https://civitas-leaderboard.onrender.com/arena` muestra «Arena Civitas».
4. Crea una sala en un teléfono y únete desde otro (`docs/PRUEBAS_FISICAS.md` §B).

**Notas:**
- Render clona el repositorio completo. El servicio arranca en `leaderboard/` e importa el motor desde `../game/clases/arena`. Si se desplegara solo `leaderboard/`, las rutas `/api/arena` responderían 503 sin afectar al leaderboard.
- Plan gratuito: tras 15 min sin uso el servicio duerme, y la primera visita tarda unos 50 s. En la feria, abre `/arena` unos minutos antes.
- Las salas están en memoria: si el servicio se reinicia, se pierden las partidas en curso, pero no la clasificación.

**Repositorios:**
- `AC020907/pruebaslaboratorio`: desarrollo y despliegue. Su `main` despliega Render y su `gh-pages` sirve la web.
- `AC020907/alcalde_digital`: repositorio académico del equipo. Cada integrante sube ahí sus commits desde su propia cuenta.
