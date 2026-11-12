# Transferir la versión aprobada a `AC020907/alcalde_digital`

Esta transferencia la hace **una persona del equipo, a mano y con su propia cuenta**. Nadie la automatiza desde aquí. Así cada commit queda con la autoría real de quien lo sube.

## 1. Preparar

En PowerShell. Ajusta las rutas si tu copia del repositorio del equipo está en otra carpeta.

```powershell
cd C:\Users\ALEJANDRO\Documents
git clone https://github.com/AC020907/alcalde_digital.git alcalde_digital_transfer
cd alcalde_digital_transfer
git checkout -b integracion-version-final
```

Usar un clon nuevo evita mezclarlo con cambios sin subir que tengas en otra copia.

## 2. Copiar el contenido aprobado de `pruebaslaboratorio` (rama `main`)

Primero, asegúrate de que `pruebaslaboratorio` esté en `main` y actualizado:

```powershell
cd C:\Users\ALEJANDRO\Documents\pruebaslaboratorio
git checkout main
git pull
```

Después copia, **sin** la carpeta `.git`, sin capturas locales de QA y sin archivos temporales:

```powershell
robocopy C:\Users\ALEJANDRO\Documents\pruebaslaboratorio C:\Users\ALEJANDRO\Documents\alcalde_digital_transfer /E /XD .git demo_arena __pycache__ saves cache /XF log.txt traceback.txt errors.txt *.rpyc leaderboard.db
```

`robocopy` devuelve un código de 0 a 7 cuando todo salió bien. Si quieres que la copia también **borre** del repositorio del equipo los archivos que ya no existen aquí, añade `/PURGE`. Hazlo solo si estás seguro: `/PURGE` borraría cualquier archivo propio del equipo que no esté en `pruebaslaboratorio`.

## 3. Revisar y subir con tu cuenta

```powershell
cd C:\Users\ALEJANDRO\Documents\alcalde_digital_transfer
git status
git diff --stat
git add -A
git commit -m "Version final: sprites oficiales, plataformero, Arena narrativa y pulido"
git push -u origin integracion-version-final
```

Después abre un Pull Request en GitHub de `integracion-version-final` hacia la rama principal de `alcalde_digital`. Revísalo y fusiónalo desde la web.

## Notas

- Cada integrante puede subir su parte con su cuenta, repitiendo el paso 3 con commits más pequeños (por ejemplo, solo `game/images/personajes/sprites/`). Así su autoría queda registrada.
- **Archivos que no deben subirse:** `.env`, claves (`ELEVENLABS_API_KEY` vive solo en las variables de entorno de tu equipo) y `leaderboard.db`.
