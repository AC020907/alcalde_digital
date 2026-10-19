# Parametros de dificultad de los minijuegos. Editar aqui para balancear.

# Cuantos reposts genera cada punto de "alcance" de una cuenta.
REPOSTS_POR_ALCANCE = 15

# Motor arcade "Caza-Rumores" (Contencion, Gran Viralizacion y Rastreador).
ARCADE = {
    "duracion": 60.0,                  # segundos que hay que resistir
    "cuenta_regresiva": 3.0,
    "umbral_viral": 10000,             # reposts para perder (VIRAL)
    "tiempo_viaje": 3.2,               # s que tarda un rumor en cruzar una conexion de peso 0.5
    "aceleracion": 0.8,                # los rumores viajan +80% mas rapido al final
    "retardo_emision": 1.0,            # s entre contagiarse y empezar a reenviar
    "reemision": 1.5,                  # s para que una cuenta activa vuelva a intentarlo
    "duracion_contagio": 12.0,         # s que una cuenta comparte antes de aburrirse (0 = nunca)
    "prob_envio": 1.2,                 # multiplica el peso de la conexion
    "reposts_por_segundo": 0.08,       # fraccion del alcance que suma cada cuenta activa por s
    "cooldown_cuarentena": 3.0,
    "duracion_cuarentena": 7.0,        # luego la cuenta vuelve a contagiar
    "intervalo_foco": 9.0,             # cada N s aparece un foco nuevo
    "intercepciones_por_onda": 8,      # cada N intercepciones se gana una onda
    "ondas_iniciales": 1,
    "max_ondas": 3,
    "radio_onda": 260,                 # px (lo usa la vista)
    "intervalo_evento": 12.0,
    "puntos_intercepcion": 10,
    "max_combo": 5,
    "puntos_cuarentena": 25,
    "bono_contencion": 500,
}

MODOS = {
    "contencion": {},
    "viral": {
        "duracion": 45.0,
        "umbral_viral": 15000,
        "tiempo_viaje": 2.6,
        "reemision": 1.1,
        "intervalo_evento": 8.0,
        "intervalo_foco": 6.0,
        "oleadas_iniciales": 2,
    },
    "rastreo": {
        "duracion": 70.0,
        "umbral_viral": 6000,          # reposts NUEVOS desde que empieza el rastreo
        "reposts_por_segundo": 0.03,
        "tiempo_viaje": 3.4,
        "reemision": 5.0,
        "intervalo_evento": 18.0,
        "intervalo_foco": 0,           # sin focos nuevos: el rumor viene de un solo origen
        "duracion_contagio": 0,        # la cadena hasta el origen no debe borrarse
        "prob_envio": 0.9,
        "precalentamiento": 7.0,       # s que el rumor se propaga antes de que empiece el jugador
        "penalizacion_rastro": 4.0,    # s que se pierden por seguir una pista falsa
        "costo_pista": 6.0,            # s que cuesta pedir una pista
        "puntos_rastro": 50,
    },
}
