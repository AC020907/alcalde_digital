# Voces sintéticas para Alcalde Digital / Civitas

Herramienta que convierte el export de diálogo de Ren'Py en archivos `game/voice/{Identifier}.ogg` usando las voces
OneCore de Windows (gratis, offline, sin nube). Ren'Py las reproduce solo gracias a `config.auto_voice = "voice/{id}.ogg"`.

**Aviso honesto:** es una voz sintética de calidad "placeholder". Se verificó solo de forma numérica
(existencia, decodificación, duración, loudness, true peak, no-silencio, tono medio por personaje). **Ningún humano la ha escuchado.**
La pronunciación, las pausas y el carácter de cada personaje están sin validar a oído.

## Uso

```
pip install -r tools/voces/requirements.txt
renpy.exe <proyecto> dialogue None --notags           # genera dialogue.tab
python tools/voces/generar_voces.py --tab dialogue.tab                  # escribe en game/voice
python tools/voces/generar_voces.py --tab dialogue.tab --only c,m --limit 20
python tools/voces/generar_voces.py --tab dialogue.tab --force          # regenera todo
python tools/voces/verificar_voces.py --out game/voice                  # verificación numérica
```

Opciones: `--out` (por defecto `game/voice`), `--only` (variables Ren'Py separadas por coma), `--limit N`,
`--force`, `--overwrite-manual`, `--inventario`, `--jobs`.

## Cómo funciona

1. Lee el `.tab` (`Identifier, Character, Dialogue, ..., Ren'Py Script`). La expresión (`feliz`, `triste`, `enojada`,
   `sorprendida`, `seria`) se toma de la columna 6 (`c seria "[what]"`).
2. `texto_es.py` normaliza el texto para el TTS: `@usuario.x` -> "arroba usuario x", `#AguaEnvenenada` -> "hashtag agua envenenada",
   horas (`6:47 A.M.` -> "seis y cuarenta y siete de la mañana"), números, `%`, `RSN` -> "R S N", etc. Quita etiquetas `{...}`.
3. Se arma SSML por frases: `pitch`/`rate` del perfil + expresión; `...` -> pausa; `¡!` -> leve subida de tono (y `<emphasis>` en enojada/sorprendida);
   pausa extra entre frases según el personaje.
4. Síntesis in-process con `winrt` (Windows.Media.SpeechSynthesis, voces `Microsoft Sabina` / `Microsoft Raul`, es-MX), sin PowerShell.
5. `procesado.py`: recorte de silencio (margen 60 ms), pasa-altos 80 Hz, de-esser suave y pasa-bajos 7 kHz, tono por personaje,
   sonoridad ~ -16 LUFS (ponderación K, `pyloudnorm`) con offset por personaje/emoción, limitador, true peak <= -1.5 dBTP
   (se comprueba sobre el OGG decodificado), fades de 10 ms, OGG Vorbis ~q0.4 mono 22,05 kHz (NOVA en estéreo).
   NOVA: modulación en anillo 45 Hz (mezcla baja), reducción de bits/frecuencia, peine metálico, chorus, desplazamiento de tono/formantes y ensanchado estéreo.

## Perfiles (`perfiles.py`)

| Var | Personaje | Voz base | Tono | Velocidad | Notas |
|-----|-----------|----------|------|-----------|-------|
| c | Claudia Reyes | Sabina | -12% | 0,95 | pausas cortas |
| m | Martina Sol | Sabina | +20% | 1,15 | muy expresiva, más brillante |
| r | Rodrigo | Raul | -28% | 0,90 | tono cálido/oscuro + saturación leve |
| t | Tomás Vega | Raul | 0% | 0,86 | pausas largas entre frases, algo más claro |
| n | NOVA | Sabina | -25% | 0,94 | efectos sintéticos, estéreo |

No se doblan: `tu` (jugador), `civitas`, narrador (personaje vacío) y las líneas con interpolación `[...]`.
Para ajustar una voz, edita `perfiles.py` (pitch en %, rate multiplicador, `EMOTIONS`) y vuelve a ejecutar: el hash incluye el perfil,
así que solo se regeneran las líneas afectadas.

## Regenerar tras cambios del guion

1. Exporta de nuevo `dialogue.tab` y ejecuta `generar_voces.py`. El manifiesto (`tools/voces/manifests/*.json`, id -> hash de texto+perfil+versión)
   hace que solo se regeneren las líneas nuevas o cambiadas, y se borran los `.ogg` huérfanos que generó esta herramienta.
2. Los ids de Ren'Py incluyen un hash del texto: si cambia el texto de una línea, cambia su id (y su audio viejo queda huérfano y se elimina).
3. `inventario_voces.csv` se reescribe siempre con TODAS las líneas: id, personaje, emoción, texto normalizado, con voz sí/no y motivo.

## Reemplazar una línea con un actor

Copia el archivo grabado como `game/voice/{Identifier}.ogg`. La herramienta nunca sobrescribe ni borra un `.ogg` que no creó ella
(compara el SHA-1 con el manifiesto) salvo que uses `--overwrite-manual`. Los archivos manuales aparecen como `manual_kept` en el resumen.

## Inventario de la muestra (`dialogue_muestra.tab`)

- Líneas totales: 210. Con voz: **163** (c 80, m 32, r 27, n 16, t 8). Omitidas: **47**.
- Omitidas: 44 narrador, 1 jugador (`tu`), 2 con interpolación (`Resultado: [texto_resultado]` del narrador y `[sesion.actual.texto]` de `civitas`;
  la interpolación tiene prioridad sobre el motivo de personaje).
- Salida: 163 `.ogg`, 4,48 MiB (~28 KB por línea), 22,05 kHz.
- Tiempo: 163 líneas en 9,3 s en frío (0,06 s por línea; síntesis ~0,02 s por línea). Re-ejecutar sin cambios: 0 regeneradas.

## Limitaciones

- Calidad de TTS OneCore es-MX; entonación plana en frases largas. Los matices emocionales son sutiles.
- Solo hay 2 voces es-MX (una femenina, una masculina): las identidades se separan por tono, velocidad, timbre (EQ/saturación) y, en NOVA, efectos.
- Anglicismos (`live`, `reposts`, `Civitas`) pueden sonar raros; hay un diccionario mínimo en `texto_es.py`.
- Las líneas con `[interpolación]` requieren voz manual o reescribir la línea.

## Voces humanas con ElevenLabs

Motor opcional con voces naturales, de la biblioteca de ElevenLabs en español latinoamericano:
- **Elección de voces:** los Voice ID y los ajustes de cada personaje (`ELEVEN_VOCES`) y la emoción del guion (`ELEVEN_EMOCION`) están en `perfiles.py`.
- **Procesado:** no se cambia el tono ni el timbre; solo se recorta, se normaliza el volumen y se aplica el efecto robótico a NOVA.

1. Crea la clave en elevenlabs.io (*API Keys*) y guárdala solo en tu equipo:
   - Comando: `setx ELEVENLABS_API_KEY "..."`.
   - No va al repositorio y el script nunca la imprime.
2. Genera muestras: N líneas por personaje, variando las emociones, en una carpeta aparte:
   `python tools/voces/generar_voces.py --tab tools/voces/dialogue.tab --motor elevenlabs --muestra 3 --out tools/voces/muestras_eleven`
   - Para comparar con la segunda voz de cada personaje: añade `--alt --out tools/voces/muestras_eleven_alt`.
3. Cuando te gusten, dobla el juego: `python tools/voces/generar_voces.py --tab tools/voces/dialogue.tab --motor elevenlabs`.
   - Sustituye las voces de Windows, pero nunca las grabaciones humanas (salvo con `--overwrite-manual`).
   - Consumo: unos 23.000 caracteres para las 298 líneas.

El texto de las líneas vecinas se envía como contexto (`previous_text` y `next_text`) para que la entonación continúe entre líneas.
