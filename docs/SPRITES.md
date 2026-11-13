# Sprites de personajes

## Origen e importación

Los sprites oficiales del equipo (`sprites.zip`) se importan con:

```
python tools/arte/importar_sprites.py <carpeta_extraida_del_zip>
python tools/web/exportar_ritmo_online.py      # retratos de la Arena Online y del Duelo web
```

- **Solo se usan los PNG.** Los `.kra` (Krita) son archivos de trabajo: no van al juego ni a la distribución.
- **Encuadre común por personaje.** Todas las expresiones se recortan con la unión de sus cajas y se escalan igual, así cambiar de expresión no mueve la figura. La salida tiene 760 px de alto y se muestra a zoom ~0,96 detrás de la caja de diálogo, con fundido inferior.
- **Retratos laterales** (`sprites/lado/*_lado.png`, 230 px): se regeneran desde los sprites nuevos con el aro del color del personaje.

## Inventario verificado (2026-11-11)

| Personaje | Expresiones en el ZIP | Observaciones verificadas | En el juego |
|---|---|---|---|
| Claudia | neutral, feliz, seria, enojada, triste, sorprendida | `neutral` y `seria` son de **570 × 570** e **idénticas pixel a pixel**; el resto es de 2480 × 2480 con el mismo encuadre | `seria` = alias de `neutral` (un solo archivo). La de 570 px se escala al mismo encuadre: queda algo más suave |
| Martina | las 6 | `seria` es de **570 × 570**; el resto de 2480 | Las 6 se usan. El color de piel con manchas aparece en todas las expresiones: es el diseño, no un error de importación |
| Rodrigo | neutral, feliz, serio, enojado, triste, sorprendido (en masculino) | `neutral` y `serio` son **idénticos** | Nombres normalizados al esquema del juego (`seria`, `enojada`, `sorprendida`). `seria` = alias de `neutral` |
| NOVA | neutral, seria, enojada, triste, sorprendida | **No trae `feliz`**, que el guion usa | `feliz` = alias de `neutral` (guiño y sonrisa). No se generó arte nuevo |
| Tomás | las 6 (`tomas_sprites.zip`, aparte) | 1254 × 1254, fondo transparente real; la figura venía con alfa 253 | Se llevó a alfa 255 y al mismo encuadre (761 × 760). Mismo estilo que los demás |

Los alias están en `ALIAS_EXPRESION` (`game/story/personajes.rpy`) y en `tools/web/exportar_ritmo_online.py`.

## Qué se sustituyó

- **Historia, Feria y Arena LAN:** las imágenes `claudia/martina/rodrigo/nova *` y los retratos laterales.
- **Duelo de Frecuencias (Ren'Py):** NOVA y el aliado se dibujan con `retrato_escena`, así que usan los sprites nuevos.
- **Arena Online:** `leaderboard/app/static/arena/*.webp` (escenas, lobby) y `static/ritmo/nova_*.webp` (Duelo web).
- **Distribución:** el arte antiguo de esos cuatro personajes (`lateral/`, `*_base.png` y los paneles enmarcados) queda **excluido** del paquete (`options.rpy`). Sigue en Git como respaldo.

## Pruebas

```
python tests/qa_visual.py galeria --etapas personajes --salida <dir>
```

Genera, con el motor real:
- una hoja de contacto por personaje (6 expresiones con sus alias, más los retratos laterales);
- cada expresión en escena con diálogo;
- dos personajes a la vez (foco y atenuado);
- un retrato lateral.

Capturas en `docs/auditoria/sprites/` («antes_*» con el arte anterior y «despues_*» con el nuevo).

Revisión visual (2026-11-11):
- **Bien:** sin artefactos de transparencia; las figuras no saltan al cambiar de expresión; las caras quedan por encima de la caja de diálogo; nada sale de la pantalla.
- **Observación:** las expresiones entregadas a 570 px se ven un poco menos nítidas que las de 2480.
