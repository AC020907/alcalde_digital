"""
Protocolo de la Arena Civitas: un mensaje JSON por linea sobre TCP (sockets).

Todo mensaje lleva "v" (version) y "tipo". Los del cliente llevan ademas "id" (unico por mensaje): el
servidor ignora un id repetido, asi un reenvio tras un corte no duplica una accion (idempotencia).
Los del servidor llevan "seq", que solo crece: el cliente descarta lo que llegue fuera de orden.
"""
import json

VERSION = 1
MAX_LINEA = 16 * 1024
PUERTO = 50777

# tipo -> {campo: tipos permitidos}. Campos fuera de esta lista se ignoran.
MENSAJES_CLIENTE = {
    "hola": {"nombre": (str,), "rol": (str,), "token": (str, type(None)), "clave": (str, type(None))},
    "listo": {"listo": (bool,)},
    "empezar": {},
    "accion": {"ronda": (int,), "ruta": (list,)},
    "pausa": {"pausar": (bool,)},
    "continuar": {},
    "salir": {},
    "ping": {},
    "resultado_prueba": {"indice": (int,), "datos": (dict,)},
}
OBLIGATORIOS = {"hola": ("nombre", "rol"), "listo": ("listo",), "accion": ("ronda", "ruta"), "pausa": ("pausar",),
               "resultado_prueba": ("indice", "datos")}


class ErrorProtocolo(Exception):
    def __init__(self, codigo, mensaje):
        super(ErrorProtocolo, self).__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


def codificar(mensaje):
    datos = dict(mensaje, v=VERSION)
    return (json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def decodificar(linea):
    if len(linea) > MAX_LINEA:
        raise ErrorProtocolo("muy_largo", "Mensaje demasiado largo.")
    try:
        msg = json.loads(linea.decode("utf-8") if isinstance(linea, bytes) else linea)
    except (ValueError, UnicodeDecodeError):
        raise ErrorProtocolo("json", "El mensaje no es JSON válido.")
    if not isinstance(msg, dict):
        raise ErrorProtocolo("formato", "Se esperaba un objeto JSON.")
    if msg.get("v") != VERSION:
        raise ErrorProtocolo("version", "Versión de protocolo incompatible (se espera %d)." % VERSION)
    return msg


def validar_cliente(msg):
    """Devuelve el mensaje limpio (solo campos conocidos) o lanza ErrorProtocolo."""
    tipo = msg.get("tipo")
    if tipo not in MENSAJES_CLIENTE:
        raise ErrorProtocolo("tipo", "Tipo de mensaje desconocido.")
    mid = msg.get("id")
    if not isinstance(mid, str) or not 0 < len(mid) <= 64:
        raise ErrorProtocolo("id", "Falta un id de mensaje válido.")
    limpio = {"tipo": tipo, "id": mid}
    esquema = MENSAJES_CLIENTE[tipo]
    for campo in OBLIGATORIOS.get(tipo, ()):
        if campo not in msg:
            raise ErrorProtocolo("campo", "Falta el campo '%s'." % campo)
    for campo, tipos in esquema.items():
        if campo in msg:
            valor = msg[campo]
            # bool es subclase de int: una ronda o un indice nunca pueden ser True/False.
            if isinstance(valor, bool) and bool not in tipos:
                raise ErrorProtocolo("campo", "Tipo inválido en '%s'." % campo)
            if not isinstance(valor, tipos):
                raise ErrorProtocolo("campo", "Tipo inválido en '%s'." % campo)
            limpio[campo] = valor
    if tipo == "accion" and not all(isinstance(i, int) and not isinstance(i, bool) for i in limpio["ruta"]):
        raise ErrorProtocolo("campo", "La ruta debe ser una lista de enteros.")
    if tipo == "hola":
        limpio["nombre"] = limpio["nombre"][:20]
    return limpio
