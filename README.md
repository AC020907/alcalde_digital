# Alcalde Digital

> Juego educativo de novela visual sobre gestión de desinformación en redes sociales, desarrollado en **Ren'Py + Python**.

[![Ren'Py](https://img.shields.io/badge/Ren'Py-8.5-blue.svg)](https://www.renpy.org/)
[![Python](https://img.shields.io/badge/Python-3.x-yellow.svg)](https://www.python.org/)
[![Estado](https://img.shields.io/badge/Estado-Entrega%201-orange.svg)]()
[![Uninorte](https://img.shields.io/badge/Uninorte-Estructuras%20de%20Datos%20II-purple.svg)]()
[![Documentación](https://img.shields.io/badge/Docs-Ver%20documentación-0e7490.svg)](https://claude.ai/artifact/RR6Giy5q9NNkm4wDwvMjJU)

---

## Sobre el juego

**Alcalde Digital** transcurre en **Ciudad Nova** durante una campaña electoral. La red social **Civitas** está inundada de publicaciones: algunas verdaderas, otras falsas, muchas sin verificar.

El jugador asume un rol público y debe decidir qué hacer con cada publicación que recibe. Sus decisiones no son neutrales: compartir sin verificar propaga la desinformación, ignorar puede ser igual de dañino, y reportar lo falso fortalece la confianza ciudadana. Al final de las 10 rondas, Ciudad Nova habrá prosperado o colapsado según las elecciones tomadas.

---

## Roles

| Rol | Amplificador | Descripción |
|---|---|---|
| Ciudadano | ×1.0 | Rol base — interactúa con la información cotidiana |
| Periodista | ×1.5 | Detecta noticias falsas con mayor precisión |
| Influencer | ×2.0 | Sus decisiones tienen el mayor alcance en Civitas |
| Candidato | ×1.2 | Construye confianza y enfrenta rumores directamente |

---

## Las 4 acciones

Ante cada publicación el jugador puede:

1. **Compartir** — difundirla de inmediato
2. **Verificar** — investigar si es verdadera o falsa, y luego compartir o reportar
3. **Ignorar** — no hacer nada
4. **Reportar** — denunciar contenido falso (disponible dentro del flujo de verificación)

Verificar antes de actuar siempre produce mejores resultados para Ciudad Nova.

---

## Indicadores de Ciudad Nova

| Indicador | Tipo | Inicial | Condición crítica |
|---|---|---|---|
| Información verificada | positivo | 50 | — |
| Confianza ciudadana | positivo | 60 | ≤ 20 → derrota inmediata |
| Convivencia | positivo | 70 | — |
| Bienestar | positivo | 65 | — |
| Desinformación | negativo | 30 | ≥ 80 → derrota inmediata |
| Conflictos | negativo | 20 | ≥ 80 → derrota inmediata |

---

## Estructuras de datos implementadas

- **Árbol AVL** (`ArbolAVL.py`) — almacena las publicaciones ordenadas por `nivel_riesgo`. Garantiza que el jugador enfrente primero las publicaciones de menor riesgo y las más peligrosas al final. Incluye rotaciones LL/RR/LR/RL, recorridos recursivos e iterativos, y métodos utilitarios (`hojas`, `gradoArbol`, `suma`, `esPerfecto`, `nodosEnNivel`, `buscarPadre`, `tio`).
- **Clase_pila** (`Clase_pila.py`) — stack genérico, equivalente de `Stack<>` de Java. Clase independiente igual que en los proyectos de referencia del profesor. Usada en los tres recorridos iterativos del AVL (`preorden`, `inorden`, `posorden` iterativos).
- **Árbol de decisiones N-ario** (`Tree.py` / `Node.py`) — cada publicación tiene su propio árbol que modela las 4 acciones del diagrama del laboratorio.
- **BancoPublicaciones** (`Publicacion.py`) — extrae siempre la publicación de menor riesgo del AVL con `minimo_nodo` + `borrar` en O(log n).

---

## Arquitectura

```
game/
├── clases/
│   ├── Clase_pila.py       ← stack genérico (equiv. Java Stack<>)
│   ├── NodoAVL.py          ← nodo del árbol AVL
│   ├── ArbolAVL.py         ← AVL completo con rotaciones y utilitarios
│   ├── Node.py             ← NodoDecision N-ario
│   ├── Tree.py             ← ArbolDecisiones con recorridos
│   ├── Publicacion.py      ← Publicacion, SesionPublicacion, BancoPublicaciones
│   ├── Ciudad.py           ← 6 indicadores + condiciones de victoria/derrota
│   └── Jugador.py          ← roles con amplificador de impacto
├── story/
│   └── intro.rpy           ← narración introductoria
├── objects.rpy             ← 10 publicaciones con 4 acciones cada una
├── script.rpy              ← flujo principal del juego
└── screens.rpy             ← HUD en tiempo real + sistema de notificaciones
```

---

## Cómo ejecutar el juego

### Requisitos

- [Ren'Py 8.5](https://www.renpy.org/latest.html) instalado

### Pasos

1. Clona el repositorio:
   ```bash
   git clone https://github.com/g4bblcs/Alcalde-Digital.git
   ```

2. Abre el **launcher de Ren'Py**.

3. Haz clic en **Add an Existing Project** y selecciona la carpeta `Alcalde-Digital`.

4. Selecciona el proyecto en la lista y presiona **Launch Project**.

> No se requiere instalar Python por separado — Ren'Py incluye su propio intérprete.

---

## Documentación técnica

Documentación completa con diagramas, código anotado y reporte de cumplimiento de la Entrega 1:

**[Ver documentación →](https://claude.ai/artifact/RR6Giy5q9NNkm4wDwvMjJU)**

---

*Estructuras de Datos II · Universidad del Norte · 2026*
