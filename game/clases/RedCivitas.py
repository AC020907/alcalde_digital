from clases.GrafoSocial import GrafoSocial


# (id, tipo, alcance, seguidores, creada, verificada, barrio)
# "alcance" = peso de la cuenta al compartir (se convierte en reposts).
# El tipo "bot" es informacion oculta: el jugador solo lo descubre investigando.
USUARIOS = [
    ("jugador",            "jugador",    12,  3400, "2015",          True,  "Alcaldia"),
    ("@noticias.nova",     "medio",      55, 23000, "2014",          True,  "Medios"),
    ("@investigador.nova", "medio",      22,  8400, "2019",          True,  "Medios"),
    ("@salud.nova",        "medio",      30, 12000, "2016",          True,  "Medios"),
    ("@barrio.central",    "ciudadano",   9,   640, "2020",          False, "Centro"),
    ("@ciudadano",         "ciudadano",   5,   210, "2021",          False, "Centro"),
    ("@vecina.ana",        "ciudadano",   7,   380, "2018",          False, "Sur"),
    ("@preocupado99",      "ciudadano",   6,    95, "2023",          False, "Sur"),
    ("@verdad.oculta",     "bot",        23,  4200, "hace 2 meses",  False, "Norte"),
    ("@bot.4521",          "bot",        19,  1900, "hace 3 semanas", False, "Norte"),
    ("@sol.y.limon",       "ciudadano",   8,   450, "2017",          False, "Oeste"),
    ("@verde.ciudad",      "ciudadano",  11,  1300, "2019",          False, "Oeste"),
    ("@eco.urbano",        "influencer", 22,  9800, "2018",          False, "Centro"),
    ("@candidata.luna",    "influencer", 45, 31000, "2017",          True,  "Oeste"),
    ("@NovaLibre",         "bot",        14,    18, "ayer",          False, "Norte"),
    ("@PatriotaNova",      "influencer", 38, 15000, "2021",          False, "Norte"),
    ("@ciudadano345",      "ciudadano",   6,   126, "2022",          False, "Sur"),
    ("@bot.7788",          "bot",        12,   860, "hace 5 dias",   False, "Oeste"),
    ("@lector.critico",    "ciudadano",   4,   150, "2016",          False, "Medios"),
    ("@fan.noticias",      "ciudadano",   5,   230, "2020",          False, "Medios"),
    ("@leo.centro",        "ciudadano",   4,   120, "2019",          False, "Centro"),
    ("@marta.ventas",      "ciudadano",   6,   310, "2015",          False, "Centro"),
    ("@don.pedro",         "ciudadano",   3,    60, "2022",          False, "Sur"),
    ("@sofia.sur",         "ciudadano",   5,   270, "2018",          False, "Sur"),
    ("@carlos.norte",      "ciudadano",   4,   140, "2021",          False, "Norte"),
    ("@vecino.anonimo",    "ciudadano",   3,    35, "2024",          False, "Norte"),
    ("@luz.oeste",         "ciudadano",   5,   200, "2019",          False, "Oeste"),
    ("@pipe.skate",        "ciudadano",   4,   180, "2023",          False, "Oeste"),
]

# (origen, destino, peso): lo que publica origen le llega a destino.
CONEXIONES = [
    ("@verdad.oculta",     "@preocupado99",      0.8),
    ("@verdad.oculta",     "@bot.4521",          0.9),
    ("@verdad.oculta",     "@sol.y.limon",       0.4),
    ("@preocupado99",      "@vecina.ana",        0.7),
    ("@preocupado99",      "@barrio.central",    0.5),
    ("@preocupado99",      "@ciudadano345",      0.4),
    ("@bot.4521",          "@eco.urbano",        0.6),
    ("@bot.4521",          "@ciudadano",         0.7),
    ("@sol.y.limon",       "@verde.ciudad",      0.5),
    ("@vecina.ana",        "jugador",            0.6),
    ("@vecina.ana",        "@salud.nova",        0.3),
    ("@barrio.central",    "@ciudadano",         0.4),
    ("@barrio.central",    "@investigador.nova", 0.5),
    ("@eco.urbano",        "jugador",            0.8),
    ("@eco.urbano",        "@noticias.nova",     0.6),
    ("@eco.urbano",        "@candidata.luna",    0.7),
    ("@eco.urbano",        "@PatriotaNova",      0.4),
    ("@ciudadano",         "jugador",            0.5),
    ("@ciudadano",         "@vecina.ana",        0.4),
    ("@noticias.nova",     "jugador",            0.6),
    ("@noticias.nova",     "@salud.nova",        0.7),
    ("@noticias.nova",     "@investigador.nova", 0.6),
    ("@noticias.nova",     "@PatriotaNova",      0.3),
    ("@verde.ciudad",      "@candidata.luna",    0.4),
    ("@verde.ciudad",      "@eco.urbano",        0.3),
    ("@investigador.nova", "@noticias.nova",     0.5),
    ("@salud.nova",        "@barrio.central",    0.4),
    ("@candidata.luna",    "@noticias.nova",     0.5),
    ("@candidata.luna",    "@verde.ciudad",      0.6),
    ("@NovaLibre",         "@PatriotaNova",      0.8),
    ("@NovaLibre",         "@ciudadano345",      0.7),
    ("@NovaLibre",         "@bot.7788",          0.9),
    ("@bot.7788",          "@barrio.central",    0.6),
    ("@bot.7788",          "@sol.y.limon",       0.6),
    ("@bot.7788",          "@eco.urbano",        0.5),
    ("@PatriotaNova",      "@noticias.nova",     0.5),
    ("@PatriotaNova",      "@candidata.luna",    0.6),
    ("@PatriotaNova",      "@verde.ciudad",      0.7),
    ("@PatriotaNova",      "@ciudadano345",      0.5),
    ("@ciudadano345",      "@vecina.ana",        0.6),
    ("@ciudadano345",      "@preocupado99",      0.5),
    ("@noticias.nova",     "@lector.critico",    0.7),
    ("@noticias.nova",     "@fan.noticias",      0.8),
    ("@salud.nova",        "@fan.noticias",      0.5),
    ("@fan.noticias",      "@lector.critico",    0.5),
    ("@lector.critico",    "@investigador.nova", 0.4),
    ("@fan.noticias",      "@leo.centro",        0.4),
    ("@eco.urbano",        "@leo.centro",        0.7),
    ("@eco.urbano",        "@marta.ventas",      0.6),
    ("@barrio.central",    "@marta.ventas",      0.5),
    ("@marta.ventas",      "@leo.centro",        0.5),
    ("@leo.centro",        "@ciudadano",         0.4),
    ("@marta.ventas",      "@sofia.sur",         0.3),
    ("@vecina.ana",        "@don.pedro",         0.7),
    ("@vecina.ana",        "@sofia.sur",         0.6),
    ("@preocupado99",      "@don.pedro",         0.6),
    ("@sofia.sur",         "@ciudadano345",      0.5),
    ("@don.pedro",         "@preocupado99",      0.4),
    ("@sofia.sur",         "@salud.nova",        0.3),
    ("@PatriotaNova",      "@carlos.norte",      0.7),
    ("@bot.4521",          "@vecino.anonimo",    0.8),
    ("@NovaLibre",         "@vecino.anonimo",    0.8),
    ("@carlos.norte",      "@vecino.anonimo",    0.5),
    ("@vecino.anonimo",    "@carlos.norte",      0.5),
    ("@carlos.norte",      "@luz.oeste",         0.3),
    ("@candidata.luna",    "@luz.oeste",         0.7),
    ("@candidata.luna",    "@pipe.skate",        0.6),
    ("@sol.y.limon",       "@luz.oeste",         0.5),
    ("@bot.7788",          "@pipe.skate",        0.7),
    ("@pipe.skate",        "@verde.ciudad",      0.5),
    ("@luz.oeste",         "@pipe.skate",        0.4),
    ("jugador",            "@noticias.nova",     0.6),
    ("jugador",            "@vecina.ana",        0.7),
    ("jugador",            "@verde.ciudad",      0.5),
]

ORIGEN_RUMOR = "@verdad.oculta"

# Cuentas que pueden haber iniciado un rumor en el Rastreador (varia cada partida).
CANDIDATOS_ORIGEN = ["@verdad.oculta", "@NovaLibre", "@bot.7788", "@PatriotaNova"]

# Cuentas que pueden encender una crisis en Contencion.
CANDIDATOS_FOCO = ["@bot.4521", "@NovaLibre", "@bot.7788", "@sol.y.limon", "@preocupado99",
                   "@ciudadano345", "@vecino.anonimo", "@pipe.skate"]

RUMORES = [
    "URGENTE: el agua de Ciudad Nova está contaminada. No la tomen.",
    "El hospital central cerrará esta noche y no atenderá emergencias.",
    "La alcaldía va a cancelar las elecciones por 'seguridad'.",
    "Cierran todos los bancos mañana: saquen su dinero ya.",
]


def crear_red_civitas():
    grafo = GrafoSocial()
    for nodo, tipo, alcance, seguidores, creada, verificada, barrio in USUARIOS:
        nombre = "Tu" if nodo == "jugador" else nodo
        perfil = {"seguidores": seguidores, "creada": creada,
                  "verificada": verificada, "barrio": barrio}
        grafo.agregar_usuario(nodo, nombre, tipo, alcance, perfil)
    for origen, destino, peso in CONEXIONES:
        grafo.agregar_conexion(origen, destino, peso)
    return grafo
