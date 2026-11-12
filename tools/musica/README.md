# Banda sonora procedural de Alcalde Digital / Civitas

Toda la música y los SFX se generan con Python (numpy/scipy), sin samples ni melodías de terceros: licencia limpia.
Salida: OGG Vorbis 44.1 kHz estéreo (calidad ~0.45) en `game/assets/audio/music/` y `game/assets/audio/sfx/`.
No se tocan los `.wav` anteriores ni ningún `.rpy`.

## Regenerar

```
pip install numpy scipy soundfile matplotlib
python tools/musica/componer.py                # todo
python tools/musica/componer.py --only crisis  # una pista o un SFX
python tools/musica/componer.py --seed 7       # semilla (por defecto 7; determinista)
python tools/musica/verificar.py               # tabla de verificación, exit != 0 si algo falla
```

Los espectrogramas quedan en `tools/musica/espectrogramas/`.

## Pistas (todas en bucle)

| Archivo | Uso | Tempo / tonalidad |
|---|---|---|
| menu | menú principal, cálido y nostálgico (motivo de Ciudad Nova) | 78 bpm, Fa mayor |
| conversacion | diálogo cotidiano, discreto (motivo de Ciudad Nova) | 92 bpm, Do mayor / La menor |
| investigacion | expediente / pistas, pulso mínimo y ticks de reloj | 88 bpm, Re dórico |
| tension | tensión creciente (ostinato grave, cuerdas con trémolo) | 108 bpm, La menor |
| crisis | rumor viral / minijuegos con tiempo | 132 bpm, Mi frigio |
| nova | tema de NOVA (campanas FM, arpegios bit-crushed, glitches) | 116 bpm, Do# menor |
| revelacion | revelación, de casi silencio a clímax y vuelta | 70 bpm, Si bemol mayor a Sol menor |
| calma | noche / vínculo entre personajes, piano íntimo | 66 bpm, Mi bemol mayor |
| final_informada | final luminoso (motivo de Ciudad Nova) | 84 bpm, Re mayor |
| final_dividida | final agridulce, sin resolver del todo | 72 bpm, La menor / Do mayor |
| final_caos | ambiente oscuro, drones disonantes, notificaciones distorsionadas | 60 bpm, sin centro tonal |
| final_secreto | "Fuente Abierta", triunfal pero sobrio (motivo de Ciudad Nova) | 96 bpm, Sol mayor |
| final_mandato | "Mandato Prestado", vals hueco con caja de música desafinada | 100 bpm en 3/4, Si menor |
| creditos | recapitulación del motivo del menú, arreglo más lleno | 88 bpm, Fa mayor |

SFX: `pista`, `logro`, `error`, `decision`, `menu_hover`, `menu_select`, `pagina`, `glitch`, `transicion`, `voz_blip`.

Motivos: Ciudad Nova = sol-do-re-do-la (con sexto grado bajo en tonalidades menores); NOVA = trepada disminuida
(0, +3, +6, +5, +1 semitonos), reutilizada distorsionada (invertida, bit-crushed, en stab) en crisis y final_caos.

## Cómo está hecho (resumen)

- `dsp.py` envolventes, filtros, reverb por convolución con IR de ruido decreciente, medidor LUFS (K-weighting aproximado).
- `instruments.py` voces aditivas/FM de bajo índice y percusión de ruido filtrado.
- `song.py` render con envoltura circular: la cola de reverb y las notas se pliegan al inicio, y los filtros
  maestros se aplican circularmente. Por eso el bucle es continuo en la muestra N-1 a 0.
- `tracks.py` las 14 composiciones; `sfx.py` los efectos; `componer.py` master (HP 36 Hz, LP 11 kHz, LUFS objetivo,
  limitador suave a -1.9 dBFS) y codificación.

## Resultados de verificación (`verificar.py`, sobre los OGG decodificados)

- Música: 14/14 OK. Duraciones 50.9 a 76.4 s, 44.1 kHz estéreo, 12.5 MB en total.
- True peak entre -6.2 y -1.8 dBFS (límite -1.0). LUFS aproximado: -18.0 (juego) o -16.0 (menú, finales, créditos), tolerancia 1 dB.
- DC máximo 0.00008. Energía por encima de 10 kHz < -33 dB y por debajo de 28 Hz < -37 dB respecto al total.
- Bucle: salto entre última y primera muestra <= 0.61 veces el salto típico (percentil 99.9); prueba negativa con un corte
  no periódico da 2.4 a 4.0, así que el chequeo sí detecta bucles rotos.
- SFX: 10/10 OK, picos -4.5 a -5 dBFS (hover y blip más bajos a propósito), sin clicks en bordes.
- Nota: el límite de 35 Hz se mide en la banda 0-28 Hz porque el filtro paso alto (cuarto orden, 36 Hz) deja una falda legítima
  de las notas graves de crisis alrededor de 41 Hz.

## Advertencia honesta

Las pistas se verificaron numéricamente y mirando espectrogramas, pero **ningún humano las ha escuchado**.
Queda pendiente una escucha: balance entre capas, si las melodías suenan bien a oído, si el humor de cada pista
coincide con su escena, si algún timbre (campanas, caja de música desafinada, glitch) cansa, y si el nivel
queda bien bajo las voces. Los parámetros de mezcla están en `tracks.py` (ganancias por capa) y se pueden ajustar y regenerar.
