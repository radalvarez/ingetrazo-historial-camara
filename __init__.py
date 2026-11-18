from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QKeySequence, QVector3D

historial = []
indice = -1
ignorando = False


def _obtener_vp(app):
    vp = getattr(app, "viewport", None)
    return vp() if callable(vp) else vp


def _leer_estado(cam):
    t = cam.target
    u = cam.up
    return (
        (round(float(t.x()), 4), round(float(t.y()), 4), round(float(t.z()), 4)),
        round(float(cam.distance), 4),
        round(float(cam.yaw), 4),
        round(float(cam.pitch), 4),
        (round(float(u.x()), 4), round(float(u.y()), 4), round(float(u.z()), 4)),
        round(float(cam.fov_deg), 2),
        bool(cam.perspective),
    )


def _aplicar_estado(vp, cam, estado):
    global ignorando
    ignorando = True
    try:
        t, dist, yaw, pitch, u, fov, persp = estado
        cam.target = QVector3D(*t)
        cam.distance = dist
        cam.yaw = yaw
        cam.pitch = pitch
        cam.up = QVector3D(*u)
        cam.fov_deg = fov
        cam.perspective = persp
        vp.update()
    finally:
        ignorando = False


def setup(app) -> None:
    def vigilar():
        global indice
        if ignorando:
            return
        vp = _obtener_vp(app)
        if vp is None or not hasattr(vp, "camera"):
            return
        actual = _leer_estado(vp.camera)
        if not historial or actual != historial[indice]:
            del historial[indice + 1:]
            historial.append(actual)
            if len(historial) > 40:
                historial.pop(0)
            indice = len(historial) - 1

    def ir_atras():
        global indice
        vp = _obtener_vp(app)
        if vp is not None and indice > 0:
            indice -= 1
            _aplicar_estado(vp, vp.camera, historial[indice])

    def ir_adelante():
        global indice
        vp = _obtener_vp(app)
        if vp is not None and indice < len(historial) - 1:
            indice += 1
            _aplicar_estado(vp, vp.camera, historial[indice])

    vp_inicial = _obtener_vp(app)
    ventana = vp_inicial.window()

    accion_atras = QAction("⬅ Anterior", ventana)
    accion_atras.setToolTip("Regresar a la posición anterior de cámara (Alt+Izquierda)")
    accion_atras.setShortcut(QKeySequence("Alt+Left"))
    accion_atras.triggered.connect(ir_atras)

    accion_adelante = QAction("➡ Siguiente", ventana)
    accion_adelante.setToolTip("Avanzar a la siguiente posición de cámara (Alt+Derecha)")
    accion_adelante.setShortcut(QKeySequence("Alt+Right"))
    accion_adelante.triggered.connect(ir_adelante)

    barra = ventana.addToolBar("Historial Cámara")
    barra.setObjectName("ToolbarHistorialCamara")
    barra.addAction(accion_atras)
    barra.addAction(accion_adelante)

    sub = app.add_menu("Historial Cámara")
    if sub is not None:
        sub.addAction(accion_atras)
        sub.addAction(accion_adelante)

    timer = QTimer(ventana)
    timer.timeout.connect(vigilar)
    timer.start(800)