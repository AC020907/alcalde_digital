## Web: Ren'Py 8.5 descarga imagenes bajo demanda y, si una descarga falla (WiFi inestable, corte
## breve), lanza una excepcion y el juego se cierra. Aqui la peticion fallida se retira de la cola y se
## reintenta con espera creciente; mientras tanto la imagen simplemente tarda en aparecer.
## Solo actua en la web (o con RENPY_SIMULATE_DOWNLOAD, el modo de prueba de Ren'Py en PC).

init -100 python:
    import os as _wd_os
    import time as _wd_time

    if renpy.emscripten or _wd_os.environ.get("RENPY_SIMULATE_DOWNLOAD"):
        import renpy.webloader as _wd_loader

        _wd_pendientes = []          # [cuando, relpath, rtype, data, intentos]
        _wd_original = _wd_loader.process_downloaded_resources
        WEB_REINTENTO_MAX_S = 8.0

        def _wd_procesar():
            ahora = _wd_time.time()
            with _wd_loader.queue_lock:
                for rr in list(_wd_loader.queue):
                    if rr.rtype != "image" or not rr.download_completed():
                        continue
                    if _wd_os.path.exists(_wd_os.path.join(renpy.config.gamedir, rr.relpath)):
                        continue
                    _wd_loader.queue.remove(rr)
                    intentos = getattr(rr, "civ_intentos", 0) + 1
                    _wd_pendientes.append([ahora + min(WEB_REINTENTO_MAX_S, 1.5 * intentos),
                                           rr.relpath, rr.rtype, rr.data, intentos])
                for p in list(_wd_pendientes):
                    if p[0] <= ahora:
                        _wd_pendientes.remove(p)
                        nueva = _wd_loader.ReloadRequest(p[1], p[2], p[3])
                        nueva.civ_intentos = p[4]
                        _wd_loader.queue.append(nueva)
            return _wd_original()

        _wd_loader.process_downloaded_resources = _wd_procesar
