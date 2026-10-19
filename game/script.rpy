## Flujo principal de Alcalde Digital.
## Prologo -> tres actos (lunes, miercoles, viernes) -> elecciones (domingo) -> finales.
## Cada acto consume publicaciones del banco AVL (de menor a mayor riesgo).

default modo_feria_activo = False

label start:
    $ preparar_partida(feria=False)
    call prologo
    call acto1
    call acto2
    call acto3
    jump elecciones
