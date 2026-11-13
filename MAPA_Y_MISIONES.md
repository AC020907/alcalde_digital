# Mapa de Ciudad Nova, misiones y nuevo HUD

Resumen de los cambios de esta sesión para el equipo: qué se hizo, cómo está construido, cómo cambia la jugabilidad y cómo extenderlo.

> **Estado:** la lógica pura tiene pruebas (`python tests/test_civitas_logica.py`, 37 pruebas) y el lint de Ren'Py (Check Script) no reporta errores. La parte visual y de teclado (dibujo del mapa, animación del carro, paneles) **se escribió sin ejecutar el juego**; hay que probarla jugando antes de la feria. Ver la lista de revisión al final.

---

## 1. Qué cambia para el jugador

| Antes | Ahora |
|---|---|
| Barra superior fija con las 4 estadísticas, que tapaba parte de la escena | Solo 5 botones flotantes arriba a la derecha. Las estadísticas están en un **panel lateral** que se abre con el botón **Ciudad** |
| La historia avanzaba sola de una escena a la siguiente | Entre escenas el jugador **conduce un carro por el mapa** hasta el lugar de la misión; la escena empieza al llegar |
| No había guía de qué hacer | **Misiones principales**: diario con lo hecho, lo activo y lo pendiente, con el destino marcado en el mapa |

### Controles del mapa
- **Flechas o WASD:** conducir (solo por las calles).
- **Enter / Espacio:** entrar al lugar cuando el carro está cerca de una parada.
- **Esc:** cerrar el mapa libre, o abrir el menú del juego durante un viaje obligatorio.
- **F9** (solo en modo desarrollo): dibuja las calles y paradas sobre el mapa, para calibrar rutas.

### Flujo de un viaje
1. Termina una escena. La historia ejecuta `call viajar_a_mision("id")`.
2. Si el carro ya está en el lugar, **no pasa nada** y la escena sigue. Si no, se abre el mapa con un aviso "Nueva misión: …".
3. El destino se marca con un aro amarillo pulsante; si queda fuera de pantalla, una flecha en el borde. Una tarjeta a la derecha muestra la misión.
4. El jugador conduce. Si pulsa Enter en otro lugar, sale "Aquí todavía no pasa nada. Tu misión: …".
5. Al llegar al destino y pulsar Enter se cierra el mapa y empieza la escena.

Durante el viaje el HUD sigue visible, así que se pueden consultar CivitasNet, Expediente, Misiones y estadísticas.

### Viajes de la historia completa
| Escena | Destino |
|---|---|
| Plaza (lunes) | Alcaldía (el carro ya empieza ahí, no hay viaje) |
| Estudio de Martina | Centro |
| Balcón nocturno (lunes) | Alcaldía |
| Barrio Sur (miércoles) | Barrio Sur |
| Centro de operaciones (miércoles) | Alcaldía |
| Redacción (viernes) | Prensa |
| Centro de operaciones (viernes) | Alcaldía |
| Elecciones (domingo) | Alcaldía (ya está ahí) |

### Modo Feria
Se mantiene la demo corta (~8 min): solo se **conducen 3 viajes** (Centro, Barrio Sur y Prensa). El resto llega directo. Solo se pueden visitar Centro, Barrio Sur, Alcaldía y Prensa; las otras 4 ubicaciones se ven atenuadas y dicen "No disponible en el Modo Feria". En la partida completa las 8 están activas.

---

## 2. Cómo está construido

Se siguió la convención del proyecto: la **lógica en Python puro** (`game/clases/`, con pruebas) y **Ren'Py solo para pantallas e historia**.

```
game/clases/MapaCiudad.py   Grafo de calles, carro, rumbo (sin Ren'Py)
game/clases/Misiones.py     Catálogo de misiones y su estado (sin Ren'Py)
game/story/mapa.rpy         Mapa dibujado, teclado, pantallas y label de viaje
game/story/misiones.rpy     Pantalla del diario y completar_mision()
game/screens.rpy            Nuevo HUD y panel lateral de estadísticas
```

### 2.1 `MapaCiudad.py`: calles y carro
- **Grafo no dirigido:** cada nodo tiene `(x, y)` y cada arista es una calle. Las coordenadas están en un espacio de referencia de 2000×1333 px (el mapa a 2000 px de ancho); la pantalla las escala (×0.96) al dibujar.
- **Paradas:** 8 nodos son ubicaciones (`centro`, `alcaldia`, `prensa`, `barrio_sur`, `universidad`, `barrio_norte`, `parque`, `transporte`).
- **`Carro`:** siempre está en un nodo o a cierta distancia (`avance`) de una arista. `avanzar(dt, dx, dy)` recibe la dirección que pide el teclado:
  - en medio de una calle solo puede ir adelante o atrás;
  - en un cruce elige la calle cuyo ángulo mejor encaja con la tecla (tolerancia ±67.5°); si ninguna encaja, se detiene;
  - velocidad máxima y aceleración constantes.
- **Rumbo:** el ángulo de la calle se convierte en 1 de 8 sectores de 45° (`der`, `izq`, `arriba`, `abajo` y 4 diagonales) para elegir qué sprite mostrar, con histéresis para que no parpadee en curvas.
- **Guardado:** `estado()` y `restaurar()` guardan y recuperan la posición. Si el mapa cambió y la posición ya no es válida, el carro vuelve al origen.
- **Rutas calibradas a mano** (`crear_mapa_nova()`): se trazaron sobre la imagen `images/bg/mapa.jpg` revisando superposiciones. Se corrigió la ruta al Centro, que cruzaba edificios, y se eliminó el enlace Centro→avenida norte porque no se pudo confirmar que hubiera calle ahí.

### 2.2 `mapa.rpy`: dibujo y entrada
- **`MapaConduccion`** es un `renpy.Displayable` (mismo patrón que `arcade.rpy`): en `render` avanza el carro con el `dt` del cuadro y dibuja el mapa, el aro de destino y el carro; en `event` traduce teclas.
- **Cámara:** el mapa se escala al ancho de 1920 px; la cámara sigue al carro en vertical con suavizado.
- **Sprites del carro** (`images/personajes/Sprites_carro/`): 8 direcciones con 3–6 cuadros. Como los cuadros miden distinto, cada uno se centra en una caja fija de 120×90 para que no "salte". Animación a 9 cuadros/s, solo si el carro se mueve.
- **Tres pantallas comparten el mismo cuerpo** (`mapa_cuerpo`):
  - `mapa_ciudad` (zorder 103): mapa libre desde el HUD, con botón Volver.
  - `mapa_viaje(destino)` (zorder 40, **debajo** del HUD): viaje obligatorio de la historia, sin Volver.
  - `mapa_cuerpo`: barra de título, tarjeta de misión, controles y tarjeta del lugar cercano.
- **`viajar_a_mision(id)`** (label): decide si hay que conducir (`mapa_debe_conducir`), muestra el mapa con `call screen`, y limpia el estado al volver.
- La posición del carro se guarda en `mapa_posicion` (variable `default`, se guarda con la partida).

### 2.3 Misiones (`Misiones.py` + `misiones.rpy`)
- El catálogo es una tabla: `(id, momento, título, descripción, ubicación, minijuego, entra en feria)`.
- La misión **activa** es siempre la primera sin completar, en orden de historia.
- La historia las marca con `$ completar_mision("id")`, normalmente justo al terminar la escena o el minijuego asociado. `misiones_hechas` se reinicia en `preparar_partida`.
- Hay 8 misiones en la partida completa y 5 en feria.

### 2.4 HUD nuevo (`screens.rpy`)
- Se eliminó la barra de fondo (92 px). `hud_ciudad` ahora solo contiene los botones **Ciudad, CivitasNet, Expediente, Misiones y Mapa**, con el mismo estilo de píldora.
- **Panel lateral:** el botón Ciudad lo abre/cierra (`panel_ciudad_abierto`, empieza cerrado). Tiene las 4 estadísticas con sus barras, una × para cerrarlo y una animación corta de entrada. No bloquea la historia y se oculta junto con el HUD en los minijuegos.
- **Alerta:** si algún indicador está en nivel crítico, el botón Ciudad muestra una insignia roja "!" aunque el panel esté cerrado (con la barra anterior eso se veía siempre).

---

## 3. Cambios en archivos existentes

| Archivo | Cambio |
|---|---|
| `story/acto1.rpy`, `acto2`, `acto3`, `elecciones`, `modo_feria` | Una línea `call viajar_a_mision("...")` antes de cada escena con lugar y `completar_mision` al terminar. Acto 1 termina con la misión nueva `lunes_noche` |
| `story/investigacion.rpy` | `preparar_partida` reinicia `misiones_hechas` |
| `minijuegos/civitas_ui.rpy` | `ocultar_avisos_juego` también oculta el mapa y el diario |
| `minijuegos/laboratorio.rpy` | Entrada "QA - Mapa de Ciudad Nova" (Shift+L en modo desarrollo) |
| `tests/test_civitas_logica.py` | Pruebas del mapa y las misiones |

---

## 4. Cómo extenderlo

**Añadir una misión:** agregar una fila a `_MISIONES` en `clases/Misiones.py` (en orden de historia), poner `call viajar_a_mision("id")` antes de la escena y `$ completar_mision("id")` al terminar. Si debe aparecer en feria, marcar la última columna `True` y decidir si se conduce (`FERIA_CONDUCIR`).

**Ajustar una ruta:** abrir el mapa desde el lanzador de Ren'Py, pulsar **F9** y editar los nodos de `crear_mapa_nova()` en `MapaCiudad.py`. Las coordenadas son del mapa a 2000 px de ancho. Las pruebas comprueban que el grafo sea conexo y que el carro nunca salga de las calles.

**Añadir una ubicación:** agregarla a `UBICACIONES` en `mapa.rpy`, crear su nodo con `parada="id"` en `crear_mapa_nova()` y conectarlo a una calle real.

**Tamaño del carro:** `MAPA_ZOOM_CARRO` (hoy 0.34) y `MAPA_CAJA_CARRO` en `mapa.rpy`.

---

## 5. Pendiente y a revisar jugando

- Que el carro **llegue a las 4 ubicaciones de la feria** (Centro, Barrio Sur, Alcaldía, Prensa) por calles que se vean correctas, y a las otras 4 en la partida completa.
- Que el aro de destino, la tarjeta de misión y el HUD se vean bien juntos, y que el panel lateral no choque con la tarjeta de lugar ("LUNES · 9:10 A.M.", arriba a la izquierda, ~3 s).
- Que el paso del mapa a la escena (corte a negro) no se sienta brusco.
- Que el Modo Feria siga durando cerca de 8 minutos con los 3 viajes.
- La Universidad ya no se alcanza directo desde Centro (ese enlace cruzaba edificios); el carro da la vuelta por el oeste.
- **Guardado:** si el jugador guarda en medio de un viaje y vuelve a cargar, el mapa de viaje se reconstruye con la posición guardada. Probarlo.
- Siguiente paso natural: conectar eventos propios a las ubicaciones que hoy no tienen escena (Universidad, Barrio Norte, Parque Central, Transporte Público).
