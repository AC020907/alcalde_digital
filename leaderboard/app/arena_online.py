"""
Arena Online: la misma Arena (reglas en game/clases/arena) jugada desde el navegador por HTTPS.

El motor de reglas NO se duplica: se importa de game/clases/arena (Render clona el repositorio completo y
el servicio arranca en leaderboard/). Las salas viven en memoria del unico proceso del servicio: son
efimeras (una partida dura ~5 min) y no tocan la base de datos del leaderboard.

Endpoints (todas las respuestas JSON; el cliente solo envia decisiones, nunca puntos):
  POST /api/arena/salas                    {nombre, rol}            -> crea sala y une al anfitrion
  POST /api/arena/salas/{codigo}/unir      {nombre, rol}            -> une a un jugador
  GET  /api/arena/salas/{codigo}?token=..&grafo=0|1                 -> vista del jugador (tambien hace de reloj)
  POST /api/arena/salas/{codigo}/{accion}  {token, ...}             -> listo | empezar | bots | accion | pausa | continuar
  Campana (historia compartida + 5 retos que juegan todos):
  POST /api/arena/salas/{codigo}/escena    {token}                  -> «listo» tras leer la escena y la pista de su rol
  POST /api/arena/salas/{codigo}/moderar   {token, indice, eliminar}-> una decision de Moderacion (el servidor la juzga)
  POST /api/arena/salas/{codigo}/rastrear  {token, accion, slots..} -> comprobar cadena o pedir pista (tablero en el servidor)
  POST /api/arena/salas/{codigo}/reto      {token, datos}           -> traza, intercepciones o juicios: el servidor rejuega
  POST /api/arena/salas/{codigo}/progreso  {token, ...}             -> marcador en vivo (solo se muestra)
  GET  /api/arena/salas/{codigo}/publico                            -> pantalla de espectadores (sin pistas de rol)
  GET  /api/arena/ritmo/{modo}                                      -> chart, ventanas y valores (fuente: game/)
"""
import os
import secrets
import sys
import threading
import time

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

_GAME = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "game"))
if _GAME not in sys.path:
    sys.path.insert(0, _GAME)

try:
    from clases.arena.sala import SalaArena, ErrorSala   # noqa: E402
    from clases.arena.reglas import ROLES                 # noqa: E402
    from clases.arena import duelo_online as DO           # noqa: E402
    DISPONIBLE = True
except ImportError:   # p. ej. si se despliega solo la carpeta leaderboard/
    SalaArena = ErrorSala = DO = None
    ROLES = ()
    DISPONIBLE = False

ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"   # sin 0/O ni 1/I/L: se dictan en voz alta en la feria
MAX_SALAS = 300
CADUCIDAD_S = 2 * 3600


class Unirse(BaseModel):
    nombre: str = Field("", max_length=20)
    rol: str = Field(..., max_length=20)
    duelo: bool = True            # campana completa (historia + 5 retos); False = solo Consejo Civico
    modo_duelo: str = Field("", max_length=12)
    modo: str = Field("feria", max_length=12)


class EntregaDuelo(BaseModel):
    token: str = Field(..., min_length=10, max_length=64)
    id: str = Field("", max_length=64)
    dificultad: str = Field("normal", max_length=12)
    juicios: list[str] = Field(..., max_length=400)
    desvios: list[Optional[float]] = Field(..., max_length=400)
    calibracion_ms: float = 0
    latencia_ms: Optional[float] = None


class Progreso(BaseModel):
    token: str = Field(..., min_length=10, max_length=64)
    juzgadas: int = 0
    puntos: int = 0
    combo: int = 0
    precision: float = 0
    avance: float = 0


class Paso(BaseModel):
    token: str = Field(..., min_length=10, max_length=64)
    id: str = Field("", max_length=64)
    indice: int = 0
    eliminar: bool = False
    accion: str = Field("", max_length=12)
    slots: list[str] = Field(default_factory=list, max_length=8)
    conclusion: Optional[str] = Field(None, max_length=20)


class EntregaReto(BaseModel):
    token: str = Field(..., min_length=10, max_length=64)
    id: str = Field("", max_length=64)
    datos: dict


class Orden(BaseModel):
    token: str = Field(..., min_length=10, max_length=64)
    listo: bool = True
    ronda: int = 0
    ruta: list[int] = Field(default_factory=list, max_length=4)
    pausar: bool = True
    id: str = Field("", max_length=64)


class ArenaOnline(object):
    def __init__(self, reloj=time.monotonic):
        self.reloj = reloj
        self.salas = {}
        self.lock = threading.Lock()

    def _purgar(self):
        ahora = self.reloj()
        for codigo in [c for c, s in self.salas.items() if ahora - s.ultima_actividad > CADUCIDAD_S]:
            del self.salas[codigo]

    def crear(self, campana=True, modo="feria", modo_duelo=None):
        with self.lock:
            self._purgar()
            if len(self.salas) >= MAX_SALAS:
                return None
            while True:
                codigo = "".join(secrets.choice(ALFABETO) for _ in range(5))
                if codigo not in self.salas:
                    break
            self.salas[codigo] = SalaArena(codigo, reloj=self.reloj, campana=campana, modo=modo, modo_duelo=modo_duelo)
            return self.salas[codigo]

    def sala(self, codigo):
        return self.salas.get((codigo or "").strip().upper())


def crear_router(api_error, rate_limit, client_ip):
    router = APIRouter(prefix="/api/arena")
    arena = ArenaOnline()
    router.arena = arena

    def requerir():
        if not DISPONIBLE:
            raise api_error(503, "arena_no_disponible", "La Arena Online no está disponible en este servidor.")

    def buscar(codigo):
        requerir()
        s = arena.sala(codigo)
        if s is None:
            raise api_error(404, "sala_no_existe", "No existe ninguna sala con ese código (o ya caducó).")
        return s

    def ejecutar(funcion, *args):
        try:
            return funcion(*args)
        except ErrorSala as e:
            status = 409 if e.codigo in ("llena", "empezada", "rol", "listos", "jugadores", "ronda", "pausa", "regla", "fase") else (
                403 if e.codigo in ("token", "permiso") else 400)
            raise api_error(status, e.codigo, e.mensaje)

    @router.post("/salas")
    def crear(body: Unirse, request: Request):
        requerir()
        rate_limit("arena_crear", client_ip(request))
        if body.rol not in ROLES:
            raise api_error(400, "rol", "Rol desconocido.")
        if body.modo_duelo not in ("", "feria", "historia") or body.modo not in ("feria", "completo"):
            raise api_error(400, "modo", "Modo desconocido.")
        s = arena.crear(body.duelo, body.modo, body.modo_duelo or None)
        if s is None:
            raise api_error(503, "sin_salas", "El servidor tiene demasiadas salas abiertas. Prueba en unos minutos.")
        jid, token = ejecutar(s.unir, body.nombre, body.rol)
        return {"codigo": s.codigo, "jugador_id": jid, "token": token}

    @router.post("/salas/{codigo}/unir")
    def unir(codigo: str, body: Unirse, request: Request):
        rate_limit("arena_accion", client_ip(request))
        s = buscar(codigo)
        if body.rol not in ROLES:
            raise api_error(400, "rol", "Rol desconocido.")
        jid, token = ejecutar(s.unir, body.nombre, body.rol)
        return {"codigo": s.codigo, "jugador_id": jid, "token": token}

    @router.get("/salas/{codigo}")
    def vista(codigo: str, token: str, grafo: int = 0):
        s = buscar(codigo)
        return ejecutar(s.vista, token, bool(grafo))

    @router.get("/ritmo/{modo}")
    def ritmo(modo: str):
        requerir()
        if modo not in ("feria", "historia"):
            raise api_error(404, "modo", "Modo de duelo desconocido.")
        return DO.config_cliente(modo)

    @router.post("/salas/{codigo}/duelo")
    def duelo(codigo: str, body: EntregaDuelo, request: Request):
        rate_limit("arena_accion", client_ip(request))
        s = buscar(codigo)
        desvios = [None if d is None else int(round(d)) for d in body.desvios]
        datos = {"dificultad": body.dificultad, "juicios": body.juicios, "desvios": desvios,
                 "calibracion_ms": body.calibracion_ms, "latencia_ms": body.latencia_ms}
        res = ejecutar(s.entregar_reto, body.token, datos, body.id or None)
        return {"ok": True, "resultado": res, "version": s.version}

    @router.get("/salas/{codigo}/publico")
    def publico(codigo: str):
        return buscar(codigo).vista_publica()

    @router.post("/salas/{codigo}/escena")
    def escena(codigo: str, body: Orden, request: Request):
        rate_limit("arena_accion", client_ip(request))
        s = buscar(codigo)
        ejecutar(s.escena_lista, body.token)
        return {"ok": True, "version": s.version}

    @router.post("/salas/{codigo}/moderar")
    def moderar(codigo: str, body: Paso, request: Request):
        rate_limit("arena_accion", client_ip(request))
        return ejecutar(buscar(codigo).moderar, body.token, body.indice, body.eliminar, body.id or None)

    @router.post("/salas/{codigo}/rastrear")
    def rastrear(codigo: str, body: Paso, request: Request):
        rate_limit("arena_accion", client_ip(request))
        return ejecutar(buscar(codigo).rastrear, body.token, body.accion, body.slots, body.conclusion, body.id or None)

    @router.post("/salas/{codigo}/reto")
    def reto(codigo: str, body: EntregaReto, request: Request):
        rate_limit("arena_accion", client_ip(request))
        s = buscar(codigo)
        if len(str(body.datos)) > 60000:
            raise api_error(413, "muy_grande", "Resultado demasiado grande.")
        res = ejecutar(s.entregar_reto, body.token, body.datos, body.id or None)
        return {"ok": True, "resultado": res, "version": s.version}

    @router.post("/salas/{codigo}/progreso")
    def progreso(codigo: str, body: Progreso, request: Request):
        rate_limit("arena_accion", client_ip(request))
        s = buscar(codigo)
        ejecutar(s.progreso, body.token, body.puntos, body.combo, body.avance)
        return {"ok": True}

    @router.post("/salas/{codigo}/{orden}")
    def ordenar(codigo: str, orden: str, body: Orden, request: Request):
        rate_limit("arena_accion", client_ip(request))
        s = buscar(codigo)
        if orden == "listo":
            ejecutar(s.listo, body.token, body.listo)
        elif orden == "empezar":
            ejecutar(s.empezar, body.token)
        elif orden == "bots":
            ejecutar(s.agregar_bots, body.token)
        elif orden == "accion":
            ejecutar(s.accion, body.token, body.ronda, body.ruta, body.id or None)
        elif orden == "pausa":
            ejecutar(s.pausa, body.token, body.pausar)
        elif orden == "continuar":
            ejecutar(s.continuar, body.token)
        else:
            raise api_error(404, "not_found", "Orden desconocida.")
        return {"ok": True, "version": s.version}

    return router
