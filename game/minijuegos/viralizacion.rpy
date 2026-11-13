## La Gran Viralizacion: la crisis del domingo. Antes su reto repetia el arcade de Caza-Rumores (misma clase y
## misma pantalla); ahora la respuesta del jugador es el plataformero «Ruta de la Verdad - Infiltracion NOVA».
## El label y la clave "viralizacion" se conservan: finales, expediente, puntuacion y guardados no cambian.
## Uso:  call evento_gran_viralizacion            (ajustes: {"nivel": "historia"|"feria"|"arena", "extra_s": n})

label evento_gran_viralizacion(origen=None, semilla=None, aplicar=True, ajustes=None):
    $ nivel_viral = (ajustes or {}).get("nivel", "historia")
    call minijuego_plataformas(nivel_viral, aplicar, ajustes, (ajustes or {}).get("tutorial", True))
    $ viralizacion = plataformas
    return _return
