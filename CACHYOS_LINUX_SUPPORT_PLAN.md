# Plan de soporte de VanishCam para Linux y CachyOS

## Propósito

Este documento define el trabajo necesario para convertir el soporte Linux
incipiente de VanishCam en una plataforma instalable, diagnosticable, probada
y distribuible.

El entorno principal de desarrollo y validación será:

- CachyOS x86-64.
- Kernel oficial de CachyOS.
- Hyprland sobre Wayland.
- Python 3.13 administrado en un entorno aislado durante la primera etapa.
- Una webcam V4L2 física.
- Una cámara virtual basada en `v4l2loopback`.

KDE Plasma Wayland, X11, Python 3.14 y kernels alternativos quedan como
compatibilidad ampliada posterior. No son requisitos para declarar completa la
primera implementación.

## Estado actual verificado

### Soporte oficial

El proyecto está soportado y distribuido oficialmente solo para Windows:

- `README.md` exige Windows 10 o posterior y Python 3.13.
- Los launchers disponibles (`AVVIA_LOCALE.bat`, `AVVIA_VIRTUAL.bat` y
  `AVVIA_OBS.bat`) son scripts de Windows.
- `AVVIA_LOCALE.bat` busca el intérprete en
  `.venv\Scripts\python.exe`.
- `BUILD_WINDOWS.bat` y `VanishCam.spec` producen
  `dist\VanishCam.exe`.
- La documentación de cámara virtual está escrita para OBS Virtual Camera y
  Unity Capture en Windows.
- No hay launcher, documentación, paquete ni validación de hardware para
  Linux.

### Código reutilizable en Linux

El núcleo de procesamiento no necesita una reescritura completa:

- Los efectos, la segmentación y el reconocimiento usan NumPy, OpenCV y
  MediaPipe sin APIs exclusivas de Windows.
- `vanish_cam.py` usa DirectShow solo cuando
  `platform.system() == "Windows"`; en otros sistemas abre la cámara mediante
  `cv2.VideoCapture` genérico.
- El argumento `--virtual-backend` ya acepta `v4l2loopback`.
- `pyvirtualcam` soporta Linux mediante `v4l2loopback`.
- El audio usa `pygame.mixer` y dispone de un fallback a `ffplay`.
- La descarga y verificación de modelos usa APIs portables de Python.

Esto constituye soporte preliminar en el código, no soporte Linux terminado.

### Código legado

`run3.py` contiene rutas específicas para DirectShow, Media Foundation y OBS.
Parece ser una implementación anterior y no es el entry point documentado.
Debe marcarse formalmente como legado, excluirse del soporte Linux y evitar que
se convierta accidentalmente en una segunda implementación que haya que
mantener. El entry point soportado debe ser `vanish_cam.py`.

### Limitación de la validación actual en Windows

El repositorio contiene 45 pruebas, pero el `.venv` local apunta a una
instalación anterior de Python 3.13 que Windows ya no permite ejecutar. Por
ello, durante este análisis no se pudo obtener una ejecución limpia de la
suite. Esto describe un problema del entorno local y no un fallo confirmado de
las pruebas.

Antes de empezar el port en CachyOS se deberá crear un entorno nuevo y obtener
una línea base de la suite completa.

## Decisiones iniciales

### Python

CachyOS, por su base Arch rolling release, puede tener una versión del Python
del sistema más reciente que la exigida por el proyecto. La primera
implementación conservará Python 3.13 en un entorno administrado por `uv` o una
herramienta equivalente. Esto reduce simultáneamente los cambios de sistema
operativo y de runtime.

Después de estabilizar Linux se evaluará Python 3.14 por separado. La
evaluación debe incluir la disponibilidad real de wheels para MediaPipe,
OpenCV, `pyvirtualcam`, NumPy y especialmente `pygame`.

No se instalarán dependencias Python globalmente ni se modificará el Python
administrado por `pacman`.

### Cámara virtual

El kernel oficial de CachyOS incluye el módulo `v4l2loopback` precompilado. En
esa configuración no se instalará `v4l2loopback-dkms` por defecto.

El módulo se cargará inicialmente de forma explícita:

```bash
sudo modprobe v4l2loopback devices=1 exclusive_caps=1 card_label="VanishCam"
```

`exclusive_caps=1` es necesario para una detección consistente en clientes
WebRTC. La persistencia mediante `/etc/modules-load.d/` y
`/etc/modprobe.d/` se documentará solo después de validar los parámetros en la
máquina real.

Si se utiliza un kernel que no incluya el módulo, la documentación ofrecerá
como fallback `v4l2loopback-dkms` junto con los headers exactos de ese kernel.
La aplicación nunca instalará módulos, modificará `/etc` ni ejecutará `sudo`
automáticamente.

### Entorno gráfico

Hyprland/Wayland es el objetivo principal. OpenCV HighGUI puede terminar
ejecutándose de forma nativa o a través de XWayland dependiendo del wheel y su
backend gráfico. Ambas rutas deben diagnosticarse y probarse.

La cámara virtual V4L2 no depende del protocolo gráfico, pero la ventana de
preview, el teclado, fullscreen y el menú sí. Se añadirá un modo
`--no-preview` para que el procesamiento y la salida virtual puedan funcionar
aunque HighGUI o XWayland no estén disponibles.

### Alcance de distribución

El primer objetivo será una ejecución soportada desde el repositorio. El
empaquetado PyInstaller, el archivo `.desktop`, AppImage y un posible PKGBUILD
se abordarán después de validar hardware, Wayland, audio y cámara virtual.

## Fase 0: línea base en CachyOS

1. Clonar el repositorio y cambiar a la rama que contiene este plan.
2. Confirmar sistema, sesión y kernel:

   ```bash
   uname -a
   uname -m
   printf '%s\n' "$XDG_SESSION_TYPE" "$XDG_CURRENT_DESKTOP"
   hyprctl version
   ```

3. Confirmar la presencia del módulo y las cámaras:

   ```bash
   modinfo v4l2loopback
   lsmod | grep v4l2loopback
   v4l2-ctl --list-devices
   ls -l /dev/video*
   ```

4. Instalar únicamente herramientas de sistema necesarias, por ejemplo
   `uv`, `v4l-utils` y `ffmpeg`, usando los repositorios configurados de
   CachyOS.
5. Crear un entorno Python 3.13 nuevo:

   ```bash
   uv python install 3.13
   uv venv --python 3.13 .venv
   .venv/bin/python -m pip install -r requirements.txt
   ```

6. Preparar y verificar modelos:

   ```bash
   .venv/bin/python prepare_models.py
   .venv/bin/python prepare_models.py --verify-only
   .venv/bin/python vanish_cam.py --self-test
   ```

7. Ejecutar todas las pruebas y conservar el resultado como línea base:

   ```bash
   .venv/bin/python -m unittest discover -v
   ```

8. Probar el preview actual sin cámara virtual:

   ```bash
   .venv/bin/python vanish_cam.py --no-virtual-camera --mode normal
   ```

Los fallos encontrados aquí deben registrarse antes de modificar el código,
separando fallos de dependencias, dispositivo, GUI, audio y lógica.

## Fase 1: abstracción de plataforma y captura

Crear un módulo como `platform_support.py` que centralice:

- Detección de Windows y Linux.
- Detección de Wayland, X11, Hyprland y disponibilidad de XWayland.
- Backend de captura recomendado.
- Enumeración y clasificación de dispositivos V4L2.
- Mensajes y comandos correctivos específicos de cada plataforma.
- Diagnóstico de permisos y dispositivos ocupados.
- Diagnóstico de `v4l2loopback`.

### Cambios en la entrada de cámara

Modificar `--camera` para aceptar:

```text
--camera 0
--camera /dev/video0
--camera /dev/v4l/by-id/...
```

En Linux se preferirá una ruta persistente en lugar de un índice. Los números
de `/dev/videoN` pueden cambiar al conectar hardware o cargar
`v4l2loopback`.

La implementación deberá:

- Usar `cv2.CAP_V4L2` explícitamente en Linux, con fallback controlado a
  `CAP_ANY` si fuera necesario.
- Informar qué dispositivo y backend fueron seleccionados.
- Validar `isOpened()` y la lectura del primer frame.
- Mostrar resolución y FPS realmente negociados, no solo los solicitados.
- Evitar elegir como entrada el dispositivo virtual de VanishCam.
- Mantener DirectShow y su fallback actual en Windows.

### Criterios de aceptación

- Índices de Windows continúan funcionando.
- Linux acepta índice y ruta.
- Una ruta inválida produce un error accionable.
- La cámara virtual nunca se selecciona silenciosamente como entrada.
- Los tests no necesitan hardware real para validar la selección de backend.

## Fase 2: integración completa de v4l2loopback

Implementar un diagnóstico previo que:

1. Compruebe `modinfo v4l2loopback`.
2. Compruebe si el módulo está cargado.
3. Enumere dispositivos mediante sysfs o `v4l2-ctl`.
4. Identifique el dispositivo con label `VanishCam`.
5. Compruebe capacidades V4L2 y `exclusive_caps`.
6. Compruebe que el proceso puede abrir el dispositivo como productor.
7. Pase la ruta explícita a `pyvirtualcam.Camera(device=...)`.
8. Distinga entre módulo ausente, módulo descargado, permisos insuficientes y
   dispositivo ocupado.

Agregar, al menos, estas opciones:

```text
--virtual-backend v4l2loopback
--virtual-device /dev/videoN
--virtual-camera
--no-virtual-camera
```

El modo automático puede continuar con preview local cuando no encuentre una
cámara virtual. En cambio, `--virtual-camera`, `--virtual-backend` o
`--virtual-device` deben tratar la ausencia como error fatal.

Los mensajes Linux deben recomendar `modprobe`, `v4l2-ctl` y rutas
`.venv/bin/python`; no deben mencionar Unity Capture, `.bat` ni rutas de
Windows.

### Permisos

No se asumirá que agregar el usuario al grupo `video` es siempre la solución.
Primero se inspeccionarán permisos, ACL y reglas udev del dispositivo. El
diagnóstico debe mostrar el dispositivo exacto y el permiso faltante sin
intentar elevar privilegios.

### Criterios de aceptación

- VanishCam envía frames BGR válidos a la cámara virtual.
- OBS y un navegador reconocen el dispositivo.
- El dispositivo se libera al salir normalmente o por `Ctrl+C`.
- Un segundo productor genera un error comprensible.
- El cierre no deja bloqueado `/dev/videoN`.

## Fase 3: Hyprland, preview y controles

Validar bajo una sesión real de Hyprland:

- Creación y destrucción del menú de selección.
- Preview redimensionable.
- Entrada de teclado: espacio, `R`, `V`, `F`, `Q` y Escape.
- Clicks del menú.
- Fullscreen y retorno a modo ventana.
- Comportamiento al cerrar la ventana desde Hyprland.
- Reglas de ventana opcionales, sin imponer configuración global al usuario.
- Escalado fraccional y monitores HiDPI.

### Modo sin preview

Agregar `--no-preview` con estas propiedades:

- No llama a `cv2.namedWindow`, `imshow`, `waitKey` ni APIs de fullscreen.
- Requiere `--mode` porque no puede mostrar el menú.
- Conserva manejo de `SIGINT`/`SIGTERM` y liberación de recursos.
- Puede producir la cámara virtual sin XWayland.
- Ofrece una alternativa documentada a los controles de teclado, al menos
  para salir y, si es necesario, activar manualmente el efecto.

Si se necesita control interactivo completo en modo headless, se evaluará una
interfaz de señales, stdin o socket local como tarea separada; no se debe
improvisar dentro del primer port.

## Fase 4: audio en PipeWire

Probar `pygame.mixer` sobre el stack de audio de CachyOS/PipeWire:

- Inicialización y cierre repetidos.
- Reproducción del MP3 en modo Naruto.
- Cambio de dispositivo de salida.
- Ausencia temporal del servidor de audio.
- Latencia y ausencia de bloqueos en el loop de video.

Mantener `ffplay` como fallback, pero mejorar su diagnóstico y cierre:

- No dejar procesos huérfanos.
- Terminar la reproducción anterior antes de reiniciarla.
- Esperar brevemente el cierre y forzar terminación solo si fuese necesario.
- No usar flags específicos de Windows fuera de Windows.

El `self-test` deberá diferenciar decodificación del archivo e inicialización
del dispositivo de audio, porque una sesión CI puede no tener un sink real.

## Fase 5: launcher y documentación Linux

Agregar:

- `run_linux.sh` como launcher equivalente a `AVVIA_LOCALE.bat`.
- `run_virtual_linux.sh`, o una opción documentada del mismo launcher.
- `docs/CACHYOS.md` con instalación y resolución de problemas.
- Una sección Linux resumida en `README.md`.

El launcher deberá:

- Resolver siempre el directorio del repositorio.
- Crear o reutilizar exclusivamente `.venv`.
- Validar la versión de Python del entorno.
- Instalar dependencias solo dentro del entorno.
- No actualizar `pip` ni paquetes del sistema automáticamente.
- No ejecutar `sudo`.
- No cargar módulos del kernel silenciosamente.
- Reenviar todos los argumentos a `vanish_cam.py` sin perder quoting.
- Fallar con instrucciones concretas.

Ejemplos finales esperados:

```bash
./run_linux.sh --mode normal --no-virtual-camera
./run_linux.sh --mode naruto --virtual-camera \
  --virtual-backend v4l2loopback \
  --virtual-device /dev/videoN
./run_linux.sh --mode normal --no-preview --virtual-camera
```

## Fase 6: pruebas automatizadas

Extender la suite con pruebas para:

- Selección de `CAP_DSHOW` en Windows.
- Selección de `CAP_V4L2` en Linux.
- Fallbacks de ambos sistemas.
- Cámara por índice, `/dev/videoN` y `/dev/v4l/by-id/...`.
- Rechazo de la cámara virtual como entrada.
- Enumeración de dispositivos simulada.
- Módulo ausente, no cargado y mal configurado.
- Dispositivo ocupado y permisos insuficientes.
- Mensajes de error específicos por plataforma.
- Selección automática y explícita de backend virtual.
- Ejecución `--no-preview` sin ninguna llamada HighGUI.
- Inicialización de audio y fallback a `ffplay`.
- Limpieza de cámara, procesos, modelos y ventanas ante excepciones.

### CI

Agregar una matriz Windows/Linux que cubra:

- Tests unitarios.
- Verificación de modelos disponibles en el job.
- `--self-test`.
- Pruebas de GUI Linux con Xvfb cuando aporten valor.
- Construcción PyInstaller específica de cada sistema en una etapa posterior.

La CI genérica no sustituye las pruebas reales de `v4l2loopback`, PipeWire y
Hyprland. Si el runner no permite cargar módulos, esas pruebas se marcarán como
integración de hardware y se ejecutarán en CachyOS.

## Fase 7: validación manual en CachyOS

### Matriz obligatoria de la primera entrega

- Hyprland/Wayland con XWayland instalado.
- Hyprland/Wayland sin depender del preview mediante `--no-preview`.
- Preview sin cámara virtual.
- Cámara virtual consumida por OBS.
- Cámara virtual consumida por Chromium o Firefox mediante WebRTC.
- Modos Normal y Naruto.
- Audio PipeWire y fallback `ffplay`.
- Webcam seleccionada por ruta persistente.
- Desconexión o fallo de la webcam durante la ejecución.
- Webcam ocupada por otra aplicación.
- Cámara virtual ocupada por otro productor.
- Salida mediante teclado, cierre de ventana, `Ctrl+C` y `SIGTERM`.
- Reinicio después de una actualización del kernel.

### Compatibilidad ampliada

Una vez completada la matriz anterior:

- Hyprland con escalado fraccional y múltiples monitores.
- KDE Plasma Wayland.
- Sesión X11.
- Python 3.14.
- Kernel CachyOS alternativo.
- Kernel sin `v4l2loopback` precompilado mediante DKMS.
- Otros consumidores de webcam como Discord, Zoom o aplicaciones Flatpak.

Los clientes Flatpak pueden requerir permisos y portales diferentes; deben
documentarse como integración del consumidor, no confundirse con un fallo del
productor V4L2.

### Criterio de aceptación funcional

- Ejecución continua de al menos 30 minutos.
- Preview estable cuando está habilitado.
- Salida virtual estable a 1280x720 y 30 FPS, o degradación explícita si el
  hardware no lo sostiene.
- Los dos efectos se ven iguales en preview y cámara virtual.
- Audio Naruto no bloquea ni degrada el loop de video.
- No hay procesos huérfanos ni dispositivos bloqueados al cerrar.
- Los errores de configuración indican una acción correctiva concreta.

## Fase 8: empaquetado Linux

Después de estabilizar la ejecución desde fuente:

1. Crear una especificación PyInstaller para Linux separada de
   `VanishCam.spec`, o convertirla cuidadosamente en una spec multiplataforma.
2. Reemplazar el requisito de `.ico` por un PNG adecuado en Linux.
3. Construir el artefacto directamente en CachyOS; PyInstaller no debe
   tratarse como herramienta de cross-compilation desde Windows.
4. Ejecutar el self-test del artefacto.
5. Verificar librerías dinámicas y plugins gráficos/audio incluidos.
6. Agregar un archivo `.desktop` y los iconos correspondientes.
7. Evaluar AppImage solamente después de comprobar que no oculta ni rompe el
   acceso a `/dev/video*`, Wayland/XWayland y PipeWire.
8. Evaluar un `PKGBUILD` o AUR como fase final.

El paquete nunca debe administrar `v4l2loopback` automáticamente. Puede
declarar o documentar dependencias, pero la configuración del kernel queda bajo
control del usuario.

## Organización recomendada en commits o PRs

1. **Linux platform foundation**
   - Abstracción de plataforma.
   - Cámara por índice o ruta.
   - `CAP_V4L2` y tests unitarios.
2. **CachyOS virtual camera**
   - Descubrimiento y diagnóstico de `v4l2loopback`.
   - Selección segura de dispositivo virtual.
   - Mensajes específicos de Linux.
3. **Hyprland and headless operation**
   - Validación de HighGUI/XWayland.
   - `--no-preview`.
   - Limpieza por señales.
4. **Linux audio, launcher and docs**
   - PipeWire/SDL y `ffplay`.
   - `run_linux.sh`.
   - Documentación de CachyOS.
5. **Linux testing and packaging**
   - CI Linux.
   - Matriz manual.
   - PyInstaller, `.desktop` e iconos.

Cada cambio debe conservar el comportamiento de Windows y acompañarse de
pruebas. No se mezclará la migración a Python 3.14 con la primera habilitación
de Linux.

## Riesgos principales y mitigaciones

| Riesgo | Mitigación |
| --- | --- |
| Python del sistema más nuevo que el soportado | Python 3.13 administrado y aislado; probar 3.14 después |
| Índices `/dev/videoN` inestables | Aceptar rutas persistentes y clasificar dispositivos |
| VanishCam abre su propia salida como entrada | Separar dispositivos físicos y loopback por capacidades/label |
| Chrome o WebRTC no detecta la cámara | Validar `exclusive_caps=1` y estado productor/consumidor |
| HighGUI falla en Wayland | Probar XWayland y ofrecer `--no-preview` |
| Permisos insuficientes | Diagnóstico de ACL/udev sin ejecutar `sudo` |
| Audio bloquea el video | Precarga, reproducción asíncrona y pruebas PipeWire |
| Actualización del kernel cambia el módulo | Usar módulo precompilado de CachyOS y prueba post-actualización |
| PyInstaller omite plugins o librerías | Build nativo, self-test y prueba visual/audio del artefacto |
| Regresión de Windows | Matriz CI y conservar rutas Windows aisladas |

## Fuentes técnicas

- [Kernel de CachyOS](https://wiki.cachyos.org/features/kernel/): incluye
  módulos multimedia como `v4l2loopback` y explica los módulos precompilados.
- [pyvirtualcam](https://github.com/letmaik/pyvirtualcam): soporte Linux basado
  en `v4l2loopback`.
- [v4l2loopback](https://github.com/v4l2loopback/v4l2loopback/blob/main/README.md):
  parámetros del módulo, labels, números de dispositivo y `exclusive_caps`.
- [OpenCV Video I/O](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html):
  captura y selección de backend.
- [Paquete Python de Arch Linux](https://archlinux.org/packages/core/x86_64/python/):
  referencia de la versión del runtime de la distribución.
- [v4l2-ctl](https://man.archlinux.org/man/v4l2-ctl.1.en): inspección y control
  de dispositivos V4L2.

## Definición de terminado

El soporte CachyOS se considerará terminado cuando:

- La instalación desde un clon limpio esté documentada y sea reproducible.
- La aplicación funcione bajo Hyprland/Wayland con y sin preview.
- La webcam física y la virtual se seleccionen sin ambigüedad.
- OBS y un navegador consuman la salida de VanishCam.
- Normal Vanish, Naruto Vanish y el audio funcionen correctamente.
- La suite Windows/Linux esté en verde.
- La prueba manual de 30 minutos no deje recursos bloqueados.
- El README declare CachyOS como plataforma soportada y enumere claramente
  los límites restantes.
- Exista, como mínimo, una forma soportada de ejecución desde fuente. El
  empaquetado binario puede entregarse inmediatamente después si se mantiene
  como hito separado.
