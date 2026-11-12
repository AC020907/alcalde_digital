# Alcalde Digital · Civitas

**Una ciudad al borde de las elecciones. Una red social llena de rumores. Tus decisiones deciden qué información llega a quién.**

> **«Los me gusta no son evidencia».**

**Alcalde Digital / Civitas** es un videojuego educativo desarrollado principalmente en **Python y Ren’Py 8.5** para la asignatura **Estructura de Datos II** de la Universidad del Norte, con proyección a la **VI Feria Gamer 2026**. Combina novela visual ramificada, investigación, simulación de desinformación, cinco minijuegos distintos y partidas multijugador de **2 a 4 personas**.

[![Repositorio](https://img.shields.io/badge/GitHub-AC020907%2Falcalde__digital-181717?logo=github)](https://github.com/AC020907/alcalde_digital)
![Python](https://img.shields.io/badge/lógica-Python-3776AB?logo=python&logoColor=white)
![Ren'Py](https://img.shields.io/badge/motor-Ren'Py_8.5-FF7F8A)

## La premisa

En **Ciudad Nova**, cuatro candidaturas compiten por la alcaldía mientras la red ficticia **CivitasNet** amplifica noticias verdaderas, opiniones y desinformación. Una sospecha sobre el agua de la ciudad desencadena una investigación en la que aparecen **Claudia**, **Martina**, **Rodrigo**, **Tomás** y **NOVA**, una red de cuentas automatizadas.

El jugador no responde un cuestionario tradicional: **comparte, verifica, ignora, reporta, investiga y actúa**, y ve cómo la información afecta la confianza, la convivencia, el bienestar, la participación, los rumores y los resultados electorales.

## Modos de juego

| Modo | Experiencia | Estado en el código |
| --- | --- | --- |
| **Historia** | Novela visual con decisiones, investigación, cinco retos y **cinco finales** | Implementado; recorridos automáticos documentados |
| **Modo Feria** | Recorrido condensado de la historia y sus cinco retos | Implementado; duración con visitantes por medir |
| **Arena Local (LAN)** | **2–4 jugadores**, roles diferenciados, servidor TCP autoritativo, Consejo Cívico y torneo de cinco pruebas | Implementado y probado en procesos locales; falta prueba con varios PC físicos |
| **Arena Online** | Historia compartida con cuatro perspectivas, cinco minijuegos competitivos y decisiones posteriores a cada reto | Implementado y probado en navegadores locales; despliegue y pruebas físicas deben confirmarse |

### Los cinco minijuegos

| Desafío | Mecánica | Objetivo |
| --- | --- | --- |
| **Moderación Express** | Clasificación bajo presión | Frenar bots y contenido dañino sin censurar críticas legítimas |
| **Rastreador** | Tablero de evidencias; búsqueda y recorridos en grafos | Reconstruir la cadena de difusión hasta el origen |
| **Caza-Rumores** | Arcade de precisión y contención | Interceptar focos de desinformación en la red |
| **Ruta de la Verdad** | Plataformero 2D | Esquivar defensas de NOVA y recuperar documentos originales |
| **Duelo de Frecuencias** | Juego rítmico original de cuatro carriles | Recuperar una transmisión alterada por NOVA |

La antigua **Gran Viralización** se conserva como acontecimiento narrativo, pero su reto jugable se transformó en **Ruta de la Verdad**, eliminando la redundancia con Caza-Rumores.

### Cinco desenlaces

**Ciudad Informada**, **Ciudad Dividida**, **Caos Informativo**, **Mandato Prestado** y **Fuente Abierta** (secreto). Las decisiones de la historia, la investigación, las relaciones entre personajes y las actuaciones en los desafíos condicionan el desenlace. El juego incluye un **Archivo de Destinos**.

## Arena Civitas: una ciudad, cuatro perspectivas

En Arena, cada participante asume un rol: **Ciudadano, Periodista, Influencer o Candidato a alcalde**. Cada rol tiene habilidades y acceso a información diferentes. Los participantes viven **una misma crisis** desde perspectivas parciales, pero **todos juegan los cinco minijuegos**.

**Arena Online** sigue este ciclo:

`Escena compartida → pista privada del rol → minijuego competitivo → clasificación → decisión cívica → propagación y consecuencias → siguiente ronda → elecciones`.

Rondas narrativas: Ciudadano / Moderación; Periodista / Rastreador; Candidato / Caza-Rumores; Influencer / Ruta de la Verdad; y **gran final de Duelo de Frecuencias** contra NOVA.

**Arena Local** conserva un flujo propio: Consejo Cívico de decisiones con árbol y grafo → torneo de cinco pruebas → elección y resultados. Ofrece versiones **Completo**, **Feria** y **Solo Consejo**.

**Dos resultados diferentes:** campeón individual por puntos y estado colectivo de Ciudad Nova. Ganar la competencia no significa necesariamente que la ciudad haya quedado bien informada.

## Estructuras de datos — no son decorativas

| Estructura / algoritmo | Uso real en Civitas | Referencia |
| --- | --- | --- |
| **Árbol n-ario de decisiones** | Define opciones encadenadas y consecuencias; cambia por rol; el servidor valida la ruta elegida | `game/clases/Tree.py`, `game/clases/arena/reglas.py` |
| **Árbol AVL** | Ordena publicaciones por nivel de riesgo y permite extraer y eliminar manteniendo el balance | `game/clases/ArbolAVL.py`, `game/clases/Publicacion.py` |
| **Grafo social dirigido y ponderado** | Modela seguidores, intensidad de conexiones y difusión de publicaciones | `game/clases/GrafoSocial.py` |
| **BFS / BFS multifuente** | Calcula quién recibe la información, en qué saltos y qué nodos se protegen | `game/clases/GrafoSocial.py`, `game/clases/arena/reglas.py` |
| **DFS** | Reconstruye y comprueba cadenas de evidencias | `game/clases/PuzzleEvidencias.py` |
| **Grafo de Ciudad Nova** | Conecta Colegio, Barrio, Parque, Plaza y Alcaldía para simular distancias e influencia entre zonas | `game/clases/arena/reglas.py` |
| **Cola FIFO** | Administra el flujo de comentarios de Moderación Express | `game/clases/Moderador.py` |

El servidor aplica los efectos de la ruta del árbol a un grafo social. Esa propagación modifica los indicadores públicos y la confianza ciudadana, lo que influye en los resultados electorales. Consulta [Estructuras de datos](docs/ESTRUCTURAS_DATOS.md).

## Cómo ejecutar la versión de escritorio

**Requisitos:** SDK de **Ren’Py 8.5.x** y una copia del repositorio.

```bash
git clone https://github.com/AC020907/alcalde_digital.git
```

1. Descarga el SDK desde [renpy.org](https://www.renpy.org/).
2. En el lanzador, selecciona como directorio de proyectos la carpeta que contiene `alcalde_digital`.
3. Abre **Alcalde Digital** y pulsa **Launch Project**.
4. Elige **Nueva partida**, **Modo Feria** o **Arena** en el menú.

### Arena Local por TCP

- Todos los clientes deben ejecutar la **versión de escritorio** y estar en la misma red privada.
- El anfitrión elige **Arena → Crear sala**. El juego muestra una dirección IP y utiliza, por defecto, el puerto TCP **50777**.
- Los demás seleccionan **Unirse**, escriben esa IP, escogen un rol disponible y marcan **Estoy listo**.
- El anfitrión inicia la partida. El servidor sincroniza estado, tiempo, decisiones, indicadores, resultados y elecciones.

También se puede ejecutar un servidor dedicado:

```bash
python servidor_arena.py --rondas 5 --segundos 25
```

> La prueba de varios procesos en `localhost` **no reemplaza** la validación entre 2–4 PC reales; consulta [Pruebas físicas](docs/PRUEBAS_FISICAS.md).

### Arena Online y clasificación

El código de Arena Online está bajo `leaderboard/app/arena_online.py` y `leaderboard/app/static/arena.html`; el backend comparte la aplicación **FastAPI** de la clasificación. Para probarlo **localmente**:

```bash
cd leaderboard
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8791
```

Abrir **http://127.0.0.1:8791/arena**. La disponibilidad pública de `/arena` depende del despliegue efectivo del servicio correspondiente; no se presupone que el último commit ya esté en producción. Consulta [Despliegue](DESPLIEGUE.md) y [Arquitectura multijugador](docs/ARQUITECTURA_MULTIJUGADOR.md).

## Controles principales

| Acción | Controles habituales |
| --- | --- |
| Historia y decisiones | Ratón, Enter, espacio; Esc para menú |
| Moderación | Flechas izquierda/derecha o A/D; mando donde esté disponible |
| Rastreador | Arrastrar/seleccionar evidencias, conectar y comprobar; ayuda dentro del juego |
| Caza-Rumores | Clic/toque sobre amenazas, controles de mando en escritorio |
| Ruta de la Verdad | A/D o flechas para moverse; Espacio/W/arriba para saltar; botones táctiles en web |
| Duelo de Frecuencias | Cuatro carriles; D/F/J/K u opciones configuradas; controles táctiles en web |

El menú **AYUDA** explica reglas, roles, indicadores, objetivos y accesibilidad. Incluye subtítulos, avisos visuales de sonidos, reducción de movimiento y opciones separadas de audio.

## Verificación técnica

```bash
python -m pytest -q tests
cd leaderboard && python -m pytest -q
```

Otros controles disponibles:

```bash
python tests/qa_recorridos.py
python tests/qa_visual.py galeria --salida capturas
python tests/qa_visual.py arena --salida capturas
python tests/e2e_arena_online.py --jugadores 2,3,4
```

Ejecutar **Check Script (Lint)** desde el lanzador de Ren’Py.

**Estado documentado (11 de noviembre de 2026):** `docs/RELEASE_READINESS.md` registra 180 pruebas del juego, 165 del backend, lint sin errores, recorridos de 5 finales en Historia y Feria y pruebas E2E locales de Arena Online para 2, 3 y 4 navegadores. Un informe posterior de corrección local registra 182 pruebas del juego. **Estos resultados son registros del proyecto; deben volver a ejecutarse en el commit de entrega.** Aún están pendientes la LAN entre PC reales, sesiones con personas, pruebas de audio/mando/teléfonos y la confirmación del despliegue público vigente.

## Mapa del repositorio

```text
game/
  clases/            # Python: AVL, árboles, grafos, simulación, física y ritmo
  clases/arena/      # Reglas, servidor TCP, cliente, campaña y torneo
  arena/             # Pantallas Ren'Py para Arena Local y torneo
  minijuegos/        # Moderación, Rastreador, Caza-Rumores, plataformas y ritmo
  story/             # Historia, personajes, eventos, escrutinio y cinco finales
  images/            # Ilustraciones y sprites de personajes
  assets/            # Audio y recursos
leaderboard/
  app/               # FastAPI, leaderboard y Arena Online
  app/static/        # Interfaz web y motores visuales de retos
  tests/             # Tests del servicio
  render.yaml        # Configuración de Render
tests/               # Tests de motor, red, retos y recorridos
docs/                # Sustentación, rúbrica, arquitectura y evidencias
servidor_arena.py    # Servidor LAN independiente
DESPLIEGUE.md        # Proceso de publicación (revisar rama/servicio antes de usar)
```

## Para la sustentación y la feria

- [Guía de sustentación técnica](docs/GUIA_SUSTENTACION.md)
- [Matriz de cumplimiento de la rúbrica](docs/RUBRICA_CUMPLIMIENTO.md)
- [Árboles, AVL y grafos](docs/ESTRUCTURAS_DATOS.md)
- [Arquitectura cliente-servidor](docs/ARQUITECTURA_MULTIJUGADOR.md)
- [Historia online con perspectivas por rol](docs/ARENA_NARRATIVA_MULTIPERSPECTIVA.md)
- [Torneo y sistema de puntuación](docs/ARENA_TORNEO.md)
- [Plataformero: mecánicas y determinismo](docs/PLATAFORMERO_RUTA_VERDAD.md)
- [Audio y sincronización del Duelo](docs/ARENA_RITMO_MULTIJUGADOR.md)
- [Pruebas físicas pendientes](docs/PRUEBAS_FISICAS.md)
- [Estado de release](docs/RELEASE_READINESS.md)

## Equipo y créditos

Proyecto académico de **Estructura de Datos II, Universidad del Norte (2026)**.

**Integrantes del equipo:**

- Alejandro Cotes
- Juan Castillo
- Gabriela Campo
- Camilo Padilla

Las responsabilidades y contribuciones específicas pueden documentarse conforme al trabajo realizado y al historial de Git; no se asignan roles sin confirmación.

Arte y música: recursos del proyecto; los sprites oficiales de personajes se documentan en [docs/SPRITES.md](docs/SPRITES.md). **Duelo de Frecuencias** utiliza mecánicas del género de ritmo con recursos originales, sin afiliación con otros juegos.

---

**Civitas propone aprender a reconocer desinformación experimentando sus consecuencias: una decisión individual puede modificar toda una ciudad.**
