# Alcalde Digital — Civitas

**Alcalde Digital** es una novela visual de investigación sobre desinformación, hecha en **Ren'Py 8.5**. Eres el alcalde de Ciudad Nova durante la semana anterior a las elecciones. Un lunes a las 6 de la mañana, un rumor dice que el agua de la ciudad está envenenada. Cada publicación que compartes, verificas o ignoras cambia la ciudad.

> Los me gusta no son evidencia.

Proyecto para la **Feria Gamer 2026**.

---

## Características

- **Historia con decisiones**: prólogo, tres actos y un domingo de elecciones. Las elecciones tienen consecuencias inmediatas y diferidas.
- **CivitasNet**: una red social ficticia que reacciona a lo que haces. Puedes inspeccionar cada publicación (fuente, contexto, estado de verificación) y guardar pistas.
- **Expediente**: un cuaderno de investigación con hechos observados, hipótesis, conclusiones comprobadas e hipótesis refutadas.
- **Cinco retos** integrados en la historia:
  - **Moderación Express**: limpia los comentarios de Martina; borra bots y aprueba a las personas reales.
  - **Caza-Rumores**: frena un rumor que se propaga en tiempo real por la red de la ciudad.
  - **Rastreador**: un tablero de evidencias donde reconstruyes la cadena de difusión de un rumor hasta su origen.
  - **Ruta de la Verdad** (plataformas): en la Gran Viralización, dos horas antes de abrir las urnas, entras al sistema de NOVA a rescatar la evidencia original. Sustituye al antiguo arcade, que repetía el de Caza-Rumores.
  - **Duelo de Frecuencias** (nuevo): un duelo rítmico contra NOVA durante la transmisión del domingo. Cuatro carriles, ritmo original a 120 BPM, dificultad Normal, Fácil o Asistido.
- **NOVA**: la red de cuentas automáticas detrás de los rumores, con un giro que depende de lo que hiciste.
- **Personajes:** Claudia, Martina, Rodrigo, Tomás y NOVA usan los sprites oficiales en el estilo del equipo (ver [docs/SPRITES.md](docs/SPRITES.md)).
- **Eventos variables**: cada partida es un poco distinta, sin bloquear el avance.
- **Cinco finales** con escenas propias: Ciudad Informada, Ciudad Dividida, Caos Informativo, Mandato Prestado y el final secreto Fuente Abierta. Se coleccionan en el **Archivo de Destinos**.
- **Rutas con consecuencias**: la oferta a Martina, el audio falso de Tomás y a quién visitas el sábado cambian quién te ayuda el domingo y qué final es posible.
- **Voces y música**: diálogos doblados para Claudia, Martina, Rodrigo, Tomás y NOVA, y banda sonora original por estado de ánimo.
- **Puntuación Cívica y clasificación online**: hasta 1000 puntos por verificar, decidir, investigar y cuidar la ciudad. Clasificación compartida entre PC y teléfono.
- **PC, mando y teléfono**: control con ratón, teclado o gamepad, y versión web jugable en el móvil.
- **Modo Feria** (unos 12 minutos): versión condensada con los cinco retos, pensada para exhibición.
- **Arena Civitas (2–4 jugadores, red local)**: multijugador cliente-servidor por sockets TCP.
  - Roles: Ciudadano, Periodista, Influencer y Candidato a alcalde.
  - Rondas con tiempo límite; propagación de cada publicación por el grafo social.
  - Puntuación individual, resultado de la ciudad y elección entre cuatro candidatos.
- **AYUDA**: objetivo, reglas, roles, indicadores, botones y accesibilidad. Desde el menú principal, el menú del juego (Esc) y la Arena.
- **Arte**: personajes con sprites transparentes y seis expresiones cada uno, fondos ilustrados y luz de escena según el lugar.
- **Accesibilidad**:
  - subtítulos siempre visibles y **avisos visuales de sonido**;
  - reducir movimiento y velocidad de texto;
  - volumen separado de voz, música y efectos, y música que baja cuando hablan;
  - controles táctiles en el mapa;
  - formas además de colores en el Duelo.

---

## Cómo ejecutarlo

1. Descarga el **SDK de Ren'Py 8.5.x** desde <https://www.renpy.org/latest.html>.
2. Clona este repositorio:
   ```bash
   git clone https://github.com/AC020907/pruebaslaboratorio.git
   ```
   Este es el repositorio de desarrollo y despliegue: la web, Render y las versiones de Windows salen de aquí. El repositorio académico del equipo es `AC020907/alcalde_digital`, donde cada integrante sube sus commits.
3. Abre el lanzador de Ren'Py, en «Preferencias → Directorio de proyectos» elige la carpeta que contiene el proyecto y selecciónalo.
4. Pulsa **Launch Project**.

En el menú principal:
- **Nueva partida**: la historia completa.
- **Modo Feria (12 min)**: la versión corta para exhibición.
- **Arena (2-4 jugadores)**: el multijugador local.

### Arena Civitas en la red local (sin internet)

Cada jugador usa la versión de **escritorio**: los navegadores no permiten sockets TCP. Todos deben estar en la misma red (wifi o cable).

1. **Anfitrión:** «Arena (2-4 jugadores)» → nombre y rol → **Crear sala**. La sala muestra la IP del equipo y el puerto (50777). Si Windows pregunta por el firewall, permite el acceso en redes privadas.
2. **Resto de jugadores:** «Arena (2-4 jugadores)» → nombre y un rol libre → escribe la IP → **Unirse a esa sala** → **Estoy listo**.
3. **Inicio:** el anfitrión pulsa **Empezar**. Si falta gente, puede **Añadir jugador automático**.

Servidor dedicado sin interfaz (opcional; necesita Python 3):

```bash
python servidor_arena.py --rondas 5 --segundos 25
```

Demostración en un solo PC, con 4 procesos independientes: dos Ren'Py y dos bots.

```bash
python tests/qa_visual.py arena --salida demo_arena
```

### Arena Online (teléfonos o redes distintas)

Abre `https://civitas-leaderboard.onrender.com/arena` cuando esté desplegada (ver `DESPLIEGUE.md` §6). Una persona crea la sala y comparte el código o el enlace, y las demás se unen desde su teléfono o computador. Es una historia compartida de 5 rondas con cuatro perspectivas: cada rol recibe pistas propias, todos juegan los cinco retos y después de cada uno se decide qué hacer en Civitas. Usa el mismo motor de reglas que la Arena local. Detalle: [docs/ARENA_NARRATIVA_MULTIPERSPECTIVA.md](docs/ARENA_NARRATIVA_MULTIPERSPECTIVA.md).

Para probarla en local:

```bash
cd leaderboard && python -m uvicorn app.main:app --port 8791
```

Después abre `http://localhost:8791/arena`.

La arquitectura y el protocolo están en [docs/ARQUITECTURA_MULTIJUGADOR.md](docs/ARQUITECTURA_MULTIJUGADOR.md). Las pruebas con equipos reales, en [docs/PRUEBAS_FISICAS.md](docs/PRUEBAS_FISICAS.md).

Para publicar la versión web, la clasificación online y el QR, sigue **[DESPLIEGUE.md](DESPLIEGUE.md)**.

### Controles

| Acción | Cómo |
|---|---|
| Avanzar el diálogo | Clic, Enter o espacio |
| Elegir una opción | Clic, o flechas + Enter |
| CivitasNet / Expediente | Botones bajo los indicadores, arriba a la derecha |
| Historial, guardar, cargar, opciones | Barra inferior o Esc |
| Moderación Express | Flecha izquierda / A / cruceta izq.: borrar · flecha derecha / D / cruceta der.: aprobar |
| Rastreador | Arrastrar fichas, o teclas 1–6 + Z X C · H pista · Enter comprobar · Mando: cruceta mueve, A elige y coloca, Y pista |
| Caza-Rumores | Clic sobre los rumores · Mando o flechas: mover la mira, A disparar, X onda |
| Ruta de la Verdad (plataformas) | A/D o flechas: moverse · Espacio, W o flecha arriba: saltar (mantén para más altura) · Mando: cruceta y A · Táctil: botones en pantalla |
| Mapa | Flechas, WASD o cruceta · Enter o A para entrar · En el teléfono, flechas táctiles |
| Mando (general) | A aceptar · B menú · Start pausa |
| Arena | Clic, o flechas + Enter / A, sobre las opciones del árbol · «« Volver» regresa · Esc: salir de la sala |
| Ayuda | Botón «Ayuda» del menú principal, del menú del juego (Esc) o de la Arena |

---

## Estructura del proyecto

```
game/
├── clases/            Lógica en Python (sin dependencias de Ren'Py)
│   ├── GrafoSocial.py        Grafo dirigido ponderado, BFS y DFS
│   ├── RedCivitas.py         Las 28 cuentas de Ciudad Nova y sus conexiones
│   ├── ArbolAVL.py           Banco de publicaciones ordenado por riesgo
│   ├── Clase_pila.py         Pila para los recorridos iterativos del AVL
│   ├── Tree.py               Árbol N-ario de decisiones de cada publicación
│   ├── Moderador.py          Cola FIFO de comentarios
│   ├── CazaRumores.py        Motor de los minijuegos en tiempo real
│   ├── PuzzleEvidencias.py   Puzzle del Rastreador
│   └── Investigacion.py      CivitasNet, expediente, eventos y final secreto
├── minijuegos/        Pantallas y lógica de los cuatro minijuegos
├── story/             Historia, personajes, CivitasNet, expediente, finales y modo feria
├── images/            Fondos y sprites de personajes
├── assets/            Audio, fondos de minijuegos e íconos
├── gui/ · fonts/      Interfaz y tipografías
└── screens.rpy · options.rpy · script.rpy
tests/
└── test_civitas_logica.py   Pruebas de la lógica pura
```

---

## Estructuras de datos

| Estructura | Dónde se usa |
|---|---|
| **Grafo dirigido ponderado** | La red social de la ciudad: quién sigue a quién (`GrafoSocial`). |
| **BFS por niveles** | La propagación de rumores en Caza-Rumores (también en la versión online, rejugada en el servidor); las horas del Rastreador. |
| **DFS inverso** | La validación de la cadena del Rastreador y el cálculo de las pistas. |
| **Árbol AVL** | El banco de publicaciones del teléfono, que se entregan de menor a mayor riesgo. |
| **Pila** | Los recorridos iterativos del AVL (`Clase_pila`). |
| **Árbol N-ario** | Las opciones de cada publicación: Compartir / Verificar (Sí, No) / Ignorar / Reportar. En la Arena el rol inserta o elimina ramas, y el servidor valida la ruta recorriendo el árbol. |
| **Grafo social (Arena)** | Ciudadanos, candidatos y las cuentas de los jugadores. Un BFS multifuente decide quién recibe cada publicación, cuántos y en cuántos saltos. |
| **Grafo de la ciudad** | Colegio, Barrio, Parque, Plaza y Alcaldía. Un BFS de distancias decide dónde empieza el boca a boca. |
| **Cola FIFO** | Los comentarios de Moderación Express. |

### Modo sustentación y laboratorio

Al ejecutar desde el lanzador de Ren'Py, pulsa **Shift+L** en el menú principal para abrir el laboratorio. Desde ahí puedes:
- lanzar cada minijuego por separado;
- activar el modo sustentación, que muestra los recorridos BFS y DFS;
- revisar CivitasNet, el expediente y los sprites.

---

## Pruebas

Las pruebas no necesitan Ren'Py:

```bash
python -m pytest -q tests
cd leaderboard && python -m pytest -q
```

- **`tests`** (110 pruebas): lógica de la historia, finales, Duelo, y la Arena (motor y red con 2, 3 y 4 clientes reales en procesos independientes).
- **`leaderboard`** (142 pruebas): el backend.

Recorridos del guion real dentro de Ren'Py (5 perfiles y 5 finales) y capturas reales del motor:

```bash
python tests/qa_recorridos.py
python tests/qa_visual.py galeria --salida capturas
python tests/qa_visual.py arena --salida capturas
```

Para revisar los scripts: en el lanzador de Ren'Py, **Check Script (Lint)**.

---

## Documentación

- `Guia_Alcalde_Digital.pdf` / `.docx`: guía completa del juego. Incluye una sección marcada como spoiler sobre el final secreto.
- `GAME_AUDIT.md`: decisiones de diseño, sistemas y pendientes técnicos.
- `PROTOCOLO_PRUEBAS_JUGADORES.md`: plantilla para probar el juego con jugadores.
- `docs/RUBRICA_CUMPLIMIENTO.md`: cada requisito del PDF del laboratorio, con su estado y su evidencia.
- `docs/ESTRUCTURAS_DATOS.md`: árboles y grafos (justificación, operaciones y complejidad).
- `docs/ARQUITECTURA_MULTIJUGADOR.md`: cliente-servidor, protocolo y robustez.
- `docs/GUIA_SUSTENTACION.md`: preguntas probables y guion de demostración de 3 a 5 minutos.
- `docs/PLAN_DE_PRUEBAS_FERIA.md`: checklist del stand y contingencias.
- `docs/RELEASE_READINESS.md`: estado de la versión y pendientes.

---

## Equipo

| Integrante | Rol |
|---|---|
| _Nombre_ | _Rol_ |
| _Nombre_ | _Rol_ |
| _Nombre_ | _Rol_ |

---

## Contexto

Proyecto académico para el curso de Estructuras de Datos, presentado en la Feria Gamer 2026.
