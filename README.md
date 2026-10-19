# Alcalde Digital — Civitas

**Alcalde Digital** es una novela visual de investigación sobre desinformación, hecha en **Ren'Py 8.5**. Eres el alcalde de Ciudad Nova durante la semana anterior a las elecciones. Un lunes a las 6 de la mañana, un rumor dice que el agua de la ciudad está envenenada. Cada publicación que compartes, verificas o ignoras cambia la ciudad.

> Los me gusta no son evidencia.

Proyecto para la **Feria Gamer 2026**.

---

## Características

- **Historia con decisiones**: prólogo, tres actos y un domingo de elecciones. Las elecciones tienen consecuencias inmediatas y diferidas.
- **CivitasNet**: una red social ficticia que reacciona a lo que haces. Puedes inspeccionar cada publicación (fuente, contexto, estado de verificación) y guardar pistas.
- **Expediente**: un cuaderno de investigación con hechos observados, hipótesis, conclusiones comprobadas e hipótesis refutadas.
- **Cuatro minijuegos** integrados en la historia:
  - **Moderación Express**: limpia los comentarios de Martina; borra bots y aprueba a las personas reales.
  - **Caza-Rumores**: frena un rumor que se propaga en tiempo real por la red de la ciudad.
  - **Rastreador**: un tablero de evidencias donde reconstruyes la cadena de difusión de un rumor hasta su origen.
  - **La Gran Viralización**: el ataque final, dos horas antes de abrir las urnas.
- **NOVA**: la red de cuentas automáticas detrás de los rumores, con un giro que depende de lo que hiciste.
- **Eventos variables**: cada partida es un poco distinta, sin bloquear el avance.
- **Cuatro finales**: Ciudad Informada, Ciudad Dividida, Caos Informativo y un final secreto que se obtiene investigando.
- **Modo Feria** (unos 8 minutos): versión condensada con los cuatro minijuegos, pensada para exhibición.
- **Arte**: personajes con sprites transparentes y seis expresiones cada uno, fondos ilustrados y luz de escena según el lugar.
- **Accesibilidad**: opción de reducir movimiento, velocidad de texto ajustable y control con ratón o teclado.

---

## Cómo ejecutarlo

1. Descarga el **SDK de Ren'Py 8.5.x** desde <https://www.renpy.org/latest.html>.
2. Clona este repositorio:
   ```bash
   git clone https://github.com/AC020907/alcalde_digital.git
   ```
3. Abre el lanzador de Ren'Py, en «Preferencias → Directorio de proyectos» elige la carpeta que contiene el proyecto y selecciónalo.
4. Pulsa **Launch Project**.

En el menú principal:
- **Nueva partida**: la historia completa.
- **Modo Feria (8 min)**: la versión corta para exhibición.

### Controles

| Acción | Cómo |
|---|---|
| Avanzar el diálogo | Clic, Enter o espacio |
| Elegir una opción | Clic, o flechas + Enter |
| CivitasNet / Expediente | Botones bajo los indicadores, arriba a la derecha |
| Historial, guardar, cargar, opciones | Barra inferior o Esc |
| Moderación Express | ← / A borrar · → / D aprobar |
| Rastreador | Arrastrar fichas, o teclas 1–6 + Z X C · H pista · Enter comprobar |

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
| **BFS por niveles** | La propagación de rumores en Caza-Rumores y en la Gran Viralización; las horas del Rastreador. |
| **DFS inverso** | La validación de la cadena del Rastreador y el cálculo de las pistas. |
| **Árbol AVL** | El banco de publicaciones del teléfono, que se entregan de menor a mayor riesgo. |
| **Pila** | Los recorridos iterativos del AVL (`Clase_pila`). |
| **Árbol N-ario** | Las opciones de cada publicación: Compartir / Verificar (Sí, No) / Ignorar. |
| **Cola FIFO** | Los comentarios de Moderación Express. |

### Modo sustentación y laboratorio

Al ejecutar desde el lanzador de Ren'Py, pulsa **Shift+L** en el menú principal para abrir el laboratorio. Desde ahí puedes:
- lanzar cada minijuego por separado;
- activar el modo sustentación, que muestra los recorridos BFS y DFS;
- revisar CivitasNet, el expediente y los sprites.

---

## Pruebas

Las pruebas de lógica pura cubren los catálogos, CivitasNet, el expediente, los eventos variables, el final secreto y el puzzle. No necesitan Ren'Py:

```bash
python tests/test_civitas_logica.py
```

Para revisar los scripts: en el lanzador de Ren'Py, **Check Script (Lint)**.

---

## Documentación

- `Guia_Alcalde_Digital.pdf` / `.docx`: guía completa del juego. Incluye una sección marcada como spoiler sobre el final secreto.
- `GAME_AUDIT.md`: decisiones de diseño, sistemas y pendientes técnicos.
- `PROTOCOLO_PRUEBAS_JUGADORES.md`: plantilla para probar el juego con jugadores.

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
