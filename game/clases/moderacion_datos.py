"""Datos y generador de la cola de Moderacion Express (puros: los usan Historia, Arena y el servidor)."""
import random

from clases.Publicacion import Publicacion

# (autor, texto, creada, es_bot). Ojo: la critica dura pero real NO se borra.
COMENTARIOS_MODERACION = [
    ("@noticias_YA_2391", "COMPARTE ANTES DE QUE LO BORREN!!! la alcaldia esconde la verdad bit.ly/v3rd4d", "hace 2 dias", True),
    ("@lucia.marquez", "Martina, ¿tienes la fuente de lo del agua? Mi mamá está preocupada.", "2017", False),
    ("@verdad.oculta.77", "EL AGUA ESTA ENVENENADA. NO LA TOMEN. LOS MEDIOS CALLAN.", "ayer", True),
    ("@don.pedro", "Yo vivo en el Barrio Sur y el agua sale normal, no exageren.", "2022", False),
    ("@patriota_nova_01", "Despierten!!! #CiudadNovaMiente #CiudadNovaMiente #CiudadNovaMiente", "hace 3 dias", True),
    ("@camila.r", "El alcalde llega tarde a todo. Igual que con los huecos de mi calle.", "2019", False),
    ("@info24_real", "Gana un bono de 500.000 si compartes esto con 10 amigos", "hace 1 dia", True),
    ("@profe.andres", "Antes de compartir, revisen el comunicado oficial de la empresa de acueducto.", "2015", False),
    ("@user8812345", "yo tambien lo vi yo tambien lo vi yo tambien lo vi", "hoy", True),
    ("@sofia.sur", "No me gusta la gestión del alcalde, pero esto del agua suena a mentira.", "2018", False),
    ("@alerta_ciudadana_x", "URGENTE: mañana cortan el agua en toda la ciudad (fuente: confía)", "hace 4 dias", True),
    ("@marta.ventas", "Martina, te sigo hace años y te pido que verifiques antes de publicar.", "2015", False),
    ("@bot_nova_445", "Los que defienden al alcalde están pagados. Todos.", "ayer", True),
    ("@leo.centro", "Qué pereza este tema, mejor hablemos de los conciertos del sábado jaja", "2019", False),
    ("@nova.libre.real", "Video filtrado: funcionarios echando químicos al tanque >> bit.ly/xx9", "hace 2 dias", True),
    ("@pipe.skate", "Esta administración es un desastre y lo voy a seguir diciendo.", "2023", False),
    ("@ciudadano_consciente_9", "Si no compartes eres cómplice. #DespiertaNova", "hoy", True),
    ("@lector.critico", "La universidad publicó análisis del agua de ayer: todo dentro de lo normal.", "2016", False),
    ("@hidro_verdad", "Mi primo trabaja en el acueducto y dice que es cierto (no puede dar su nombre)", "hace 6 dias", True),
    ("@fan.noticias", "Martina, ¿vas a hacer live hoy? Quiero preguntarte sobre esto.", "2020", False),
    ("@xx_ciudadnova_xx", "RT RT RT RT el agua el agua el agua", "hoy", True),
    ("@vecino.anonimo", "Soy nuevo en Civitas y no sé a quién creerle, la verdad.", "2024", False),
]


def publicaciones_moderacion(semilla, cantidad=16):
    rng = random.Random("moderacion|%s" % semilla)
    elegidos = rng.sample(COMENTARIOS_MODERACION, cantidad)
    return [Publicacion(autor, texto, es_bot, 0, None) for autor, texto, _, es_bot in elegidos], \
           {autor: creada for autor, _, creada, _ in elegidos}

