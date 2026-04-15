import json
import os
from datetime import datetime
import sys
import time

# Obtenemos el nombre desde los argumentos o ponemos uno por defecto
path = os.path.dirname(os.path.abspath(__file__))
nombre_paciente = sys.argv[1]

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

#tengo que crear una clase para armar el bloque con sus caracteristicas ()

class MainWindow (QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()
        
        # SETEO DE LAS VARIABLES PARA LOS CONTROLES
        self.presion_umbral = 0.7
        self.offset = None
        self.pos_inicial_bloque = QPoint(20, 175)
        self.juego_activo = True #ESTE ME VA A SERVIR PARA FRENAR EL JUEGO CUANDO GANE
        self.victoria()
        self.timer_inicio = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_reloj)
        self.errores = 0
        
        
    
    def setupUi(self):   
        self.setFixedSize(1200,400)
        
        self.meta = QFrame(self)
        self.meta.setGeometry (1000,0,200,400)
        self.meta.setStyleSheet ("background: green")
        
        self.objeto = QFrame(self)
        self.objeto.setGeometry (20,175,80,80)
        self.objeto.setStyleSheet ("background: gray")
        
        self.label_cronometro = QLabel("Tiempo: 0.00s", self)
        self.label_cronometro.setGeometry(500, 10, 200, 50)
        self.label_cronometro.setStyleSheet("font-size: 20px; color: black; font-weight: bold;")
        
        self.label_errores = QLabel("Errores: 0", self)
        self.label_errores.setGeometry(500, 60, 200, 50) # Un poco más abajo que el cronómetro
        self.label_errores.setStyleSheet("font-size: 18px; color: red; font-weight: bold;")
        
        self.barra_presion = QProgressBar(self)
        self.barra_presion.setGeometry(50, 10, 300, 30) 
        self.barra_presion.setRange(0, 100)            
        self.barra_presion.setValue(0)
        self.barra_presion.setStyleSheet("""
            QProgressBar {
            border: 2px solid grey;
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #3498db; /* Azul */
            width: 10px;
        }
        """)
    
    def victoria (self):
        self.offset = None
        self.ganaste = QWidget(self)
        self.ganaste.setGeometry(0,0,1200,400)
        self.ganaste.setStyleSheet("background-color: rgba(0, 0, 0, 200);")
        self.ganaste.hide()
        
        layout = QVBoxLayout(self.ganaste)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        self.label_ganar = QLabel ("¡VICTORIA!",self.ganaste)
        self.label_ganar.setFont(QFont("Arial", 48, QFont.Bold))
        self.label_ganar.setStyleSheet("color: white; background: transparent;")
        self.label_ganar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_ganar)           
        
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(30)
        
        self.btn_reiniciar = QPushButton("Reiniciar Juego", self.ganaste)
        self.btn_reiniciar.setMinimumSize(150, 50)
        self.btn_reiniciar.setStyleSheet("background-color: #3498db; color: white; border-radius: 5px; font-size: 16px;")
        self.btn_reiniciar.clicked.connect(self.reiniciarJuego) 
        layout_botones.addWidget(self.btn_reiniciar) 
        
        self.btn_cerrar = QPushButton("Cerrar", self.ganaste)
        self.btn_cerrar.setMinimumSize(150, 50)
        self.btn_cerrar.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 5px; font-size: 16px;")
        self.btn_cerrar.clicked.connect(self.close) 
        layout_botones.addWidget(self.btn_cerrar)
        
        layout.addLayout(layout_botones)
        
    def reiniciarJuego(self):
        self.ganaste.hide()
        self.objeto.move(self.pos_inicial_bloque) 
        self.offset = None
        self.juego_activo = True 
        self.timer_inicio = None
        self.errores = 0
        
    def victoria_show(self):
        self.juego_activo = False
        self.timer.stop()
        texto_tiempo = (f"¡GANASTE!\nTiempo: {self.resultado_final:.2f} segundos\n errores :{self.errores}")
        self.label_ganar.setText(texto_tiempo) 
        self.ganaste.show()
        self.objeto.move(1000, self.objeto.y()) 
        self.offset = None 
        self.guardar_partida()
        print("guardo")
    
    def actualizar_reloj(self):
        if self.timer_inicio is not None and self.juego_activo:
            tiempo_actual = time.time() - self.timer_inicio
            self.label_cronometro.setText(f"Tiempo: {tiempo_actual:.2f}s")    
        
    def tabletEvent(self, event):
        pos_mouse = event.position().toPoint()
        self.presion_actual = event.pressure()
        
        if not self.juego_activo:
            event.ignore()
            return
        valor_barra = int(self.presion_actual * 100)
        self.barra_presion.setValue(valor_barra)
        if self.presion_actual > self.presion_umbral:
            # Color Verde si puedes moverlo
            self.barra_presion.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }")
        else:
        # Color rojo si no llegas al umbral
            self.barra_presion.setStyleSheet("QProgressBar::chunk { background-color: #FF0000; }")
        
        if event.type() == QTabletEvent.TabletPress:
           if self.objeto.geometry().contains(pos_mouse):
                if self.presion_actual > self.presion_umbral:
                    self.offset = pos_mouse - self.objeto.pos()
                    self.pos_inicial = self.pos()
                    if self.timer_inicio is None:
                        self.timer_inicio=time.time()
                        self.timer.start(10)
                else:
                    self.offset = None
                
        elif event.type() == QTabletEvent.TabletMove:
            if self.offset != None and self.presion_actual > self.presion_umbral:
                nueva_pos = pos_mouse - self.offset
                self.objeto.move(nueva_pos)
                if nueva_pos.x() >= self.meta.x():
                    self.timer_fin = time.time()
                    self.resultado_final = self.timer_fin - self.timer_inicio
                    self.victoria_show()
                else:
                    self.objeto.move(nueva_pos)
                    
            else:
                self.reset_bloque()
                
        elif event.type() == QTabletEvent.TabletRelease:   
            self.reset_bloque()
        
        event.accept()
    
    def reset_bloque(self):
        if self.juego_activo and self.offset is not None:
            self.errores +=1
            self.offset = None
            self.objeto.move(self.pos_inicial_bloque)
            self.label_errores.setText(f"Errores: {self.errores}")
            
    def guardar_partida(self):
        tiempo = self.resultado_final
        errores = self.errores

        carpeta_resultados = os.path.join(path, "resultados_pacientes")
        os.makedirs(carpeta_resultados, exist_ok=True)
    
        nombre_archivo = f"{nombre_paciente}(Drag and Drop).json"
        archivo_json = os.path.join(carpeta_resultados, nombre_archivo)
        archivo_txt = os.path.join(path, "historial.txt")
    
        nueva_partida = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nombre": nombre_paciente,
            "tiempo": round(tiempo, 3),
            "errores": errores,
        }
        try:
            with open(archivo_json, "r") as f:
                datos = json.load(f)
                if not isinstance(datos, list): datos = []
        except:
            datos = []

        datos.append(nueva_partida)
        datos = datos[-30:] # Mantener solo las últimas 30

        # Guardar en JSON
        with open(archivo_json, "w") as f:
            json.dump(datos, f, indent=4)
        
        # Guardar en TXT (Historial general)
        with open(archivo_txt, "a") as f:
            f.write(
                f"Fecha: {nueva_partida['fecha']}\n"
                f"Nombre: {nueva_partida['nombre']}\n"
                f"Tiempo: {nueva_partida['tiempo']} s\n"
                f"Errores: {nueva_partida['errores']}\n"
                f"------------------------------\n"
            )
        print("Partida guardada correctamente.")
            
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 