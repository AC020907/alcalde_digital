## Resultado comun de los minijuegos (remaster): la misma tarjeta de papel con contorno de tinta para
## Moderacion Express, Caza-Rumores, Rastreador y la Ruta de la Verdad. Solo presentacion: cada minijuego
## sigue pasando sus propios textos y cifras.

transform resultado_entra(retraso):
    alpha 0.0 yoffset (0 if persistent.reducir_movimiento else 22)
    pause retraso
    easein 0.35 alpha 1.0 yoffset 0

## exito: bool | titulo: texto grande | nota: "S".."D" o None | mensaje: frase del motor
## cifras: [(etiqueta, valor, color)] | lineas: [(texto, color)] adicionales
screen resultado_tarjeta(exito, titulo, nota, mensaje, cifras, lineas=()):
    add Solid("#120d1cc8")
    fixed at resultado_entra(0.0):
        align (0.5, 0.5)
        xysize (1180, (600 if nota else 470) + 34 * len(lineas))
        add Solid("#2b2440")
        frame:
            pos (10, 10)
            xysize (1160, (580 if nota else 450) + 34 * len(lineas))
            background Solid("#fbf6ee")
            padding (60, 44)
            vbox:
                spacing 18
                hbox:
                    spacing 34
                    if nota:
                        fixed:
                            xysize (170, 170)
                            add circulo(("#e8b04b" if exito else "#d1495b"), "#2b2440", 80) align (0.5, 0.5)
                            text nota size 110 bold True color "#2b2440" align (0.5, 0.52) at nota_golpe
                    vbox:
                        yalign 0.5
                        spacing 8
                        text titulo size 50 bold True color ("#2f9e8f" if exito else "#d1495b")
                        text mensaje size 23 color "#2b2440" xmaximum (860 if nota else 1040)
                hbox:
                    spacing 18
                    for i, (etq, valor, col) in enumerate(cifras):
                        frame at resultado_entra(0.25 + i * 0.08):
                            background Solid("#efe8f5")
                            xsize int((1040 - 18 * (len(cifras) - 1)) / max(1, len(cifras)))
                            padding (20, 14)
                            vbox:
                                text etq size 15 bold True color "#8b84a8" kerning 3
                                text valor size 40 bold True color col
                for k, (texto, col) in enumerate(lineas):
                    text texto size 20 color col xmaximum 1040 at resultado_entra(0.5 + k * 0.08)
                null height 4
                textbutton "CONTINUAR" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Return() default_focus True
    key "civ_accion" action Return()
