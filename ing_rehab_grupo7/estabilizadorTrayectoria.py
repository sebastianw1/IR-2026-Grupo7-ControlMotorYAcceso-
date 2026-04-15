#Estabilizador de Trayectoria: Seguir un camino laberíntico sin tocar los bordes. Mide el "ruido" motor y la espasticidad.
import json
from datetime import datetime
import sys
nombre = sys.argv[1] #el nombre del paciente que le envía el menu

def guardar_partida(tiempo, errores, precision, temblor, rigidez): #guarda los datos obtenidos del test en la carpeta de resultados
    carpeta_resultados = os.path.join(path, "resultados_pacientes")
    os.makedirs(carpeta_resultados, exist_ok=True)
    nombre_archivo = f"{nombre}(estabilizador de trayectoria).json"
    archivo_json = os.path.join(carpeta_resultados, nombre_archivo)
    archivo_txt = os.path.join(path, "historial.txt") #ademas guarda todo el historial en un .txt para tener un registro de todos los
    #intentos de test que hizo cada paciente en un formato mas accesible por un profesional
    nueva_partida = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nombre": nombre,
        "tiempo": round(tiempo, 3),
        "errores": errores,
        "precision": round(precision, 2),
        "temblor": round(temblor, 2),
        "rigidez": round(rigidez, 2)
    }

    #Si el archivo existe, lo cargamos
    try:
        with open(archivo_json, "r") as f:
            datos = json.load(f)
    except:
        datos = []

    datos.append(nueva_partida)
    datos = datos[-30:] #limita el historial a las últimas 30 partidas solamente

    with open(archivo_json, "w") as f:
        json.dump(datos, f, indent=4)
        
    with open(archivo_txt, "a") as f:
        f.write(
            f"Fecha: {nueva_partida['fecha']}\n"
            f"Nombre: {nueva_partida['nombre']}\n"
            f"Tiempo: {nueva_partida['tiempo']} s\n"
            f"Errores: {nueva_partida['errores']}\n"
            f"Precision: {nueva_partida['precision']} %\n"
            f"Temblor: {nueva_partida['temblor']} Hz\n"
            f"Rigidez: {nueva_partida['rigidez']} rad/s\n"
            f"{'-'*30}\n"
        )
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" #evita el mensaje de bienvenida en consola de pygame
path = os.path.dirname(__file__) #ruta relativa de la carpeta del proyecto
path_img = os.path.join(path, "imagenes") #ruta relativa de la carpeta de imagenes
import time
import math
import random
import pygame
pygame.init()

ANCHO, ALTO = 900, 600
screen = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Estabilizador de Trayectoria")
icono = pygame.image.load(os.path.join(path_img, r"icon_rehab.png")) #loadea las rutas del icono
pygame.display.set_icon(icono)
clock = pygame.time.Clock()
font_timer = pygame.font.Font(path+r"\Orbitron-VariableFont_wght.ttf", 20)
font_record = pygame.font.Font(path+r"\Orbitron-Bold.ttf", 20)
imagen_trofeo = pygame.image.load(os.path.join(path_img, "trofeo_ucl.png")).convert_alpha()
imagen_trofeo = pygame.transform.scale(imagen_trofeo, (75, 75)) #para la ventana del record
imagen_laureles = pygame.image.load(os.path.join(path_img, "laureles.png")).convert_alpha()
imagen_laureles = pygame.transform.scale(imagen_laureles, (75, 75)) #para la ventana del record
def dibujar_meta(): #dibuja los cuadrados negros y blancos al final del camino
    meta_x = ANCHO-50
    meta_y = ALTO-134
    lado = 7
    for i in range(0,10):
        if i%2==0: #es par o no, para intercalar cuadrados de colores opuestos
            color_meta1 = (255,255,255) #como se dibujan en simultaneo las 4 columnas, cada una tiene una variable propia
            color_meta2 = (0,0,0)
            color_meta3 = (255,255,255)
            color_meta4 = (0,0,0)
        else:
            color_meta1 = (0,0,0)
            color_meta2 = (255,255,255)
            color_meta3 = (0,0,0)
            color_meta4 = (255,255,255)
        pygame.draw.rect(screen, color_meta1, (meta_x,meta_y+lado*i,lado,lado)) #primera columna de cuadrados
        pygame.draw.rect(screen, color_meta2, (meta_x+lado,meta_y+lado*i,lado,lado)) #2da columna
        pygame.draw.rect(screen, color_meta3, (meta_x+2*lado,meta_y+lado*i,lado,lado)) #3er columna
        pygame.draw.rect(screen, color_meta4, (meta_x+3*lado,meta_y+lado*i,lado,lado)) #4ta columna
def dibujar_salida(): #similar a la funcion que dibuja la meta, pero al inicio del camino y con 3 columnas solamente
    meta_x = 40
    meta_y = 66
    lado = 7
    for i in range(0,10):
        if i%2==0: #es par
            color_meta1 = (255,255,255)
            color_meta2 = (156,27,3)
            color_meta3 = (255,255,255)
        else:
            color_meta1 = (156,27,3)
            color_meta2 = (255,255,255)
            color_meta3 = (156,27,3)
        pygame.draw.rect(screen, color_meta1, (meta_x,meta_y+lado*i,lado,lado))
        pygame.draw.rect(screen, color_meta2, (meta_x+lado,meta_y+lado*i,lado,lado))
        pygame.draw.rect(screen, color_meta3, (meta_x+2*lado,meta_y+lado*i,lado,lado))
def reiniciar_juego(): #setea todas las variables a sus valores iniciales, para que el paciente pueda volver a realizar el test
    global maquinaEstados, tiempo_inicio, tiempo_fin, targets, mask_targets
    global errores, tiempo_afuera, tiempo_salida, duraciones_salidas
    global precision, posiciones, cambios_direccion, dir_anterior, targets_inactivos
    global tiempo_fin_record, precision_record, errores_record
    salio, errores, tiempo_inicio, tiempo_fin, tiempo_afuera, tiempo_salida = 1, 0, None, None, 0, 0
    targets_inactivos, duraciones_salidas = [0, 0, 0, 0, 0, 0], []
    maquinaEstados = "juego" #0: juego, 1: metricas, 2: cerrar
    precision, posiciones, cambios_direccion, dir_anterior = 0, [], 0, None
    targets_inactivos = [0, 0, 0, 0, 0, 0]
    targets = [ #el diccionario para los objetivos que el paciente tiene que tocar
        {"pos": (random.randint(100,400),100), "r": grosor//2, "color": (255,255,255), "est": 1, "res": None},
        {"pos": (random.randint(400,700),300), "r": grosor//2, "color": (255,255,255), "est": 1, "res": None},
        {"pos": (ANCHO-100,random.randint(100,400)), "r": grosor//2, "color": (255,255,255), "est": 1, "res": None},
        {"pos": (random.randint(300,ANCHO-100),400), "r": grosor//2, "color": (255,255,255), "est": 1, "res": None},
        {"pos": (100,random.randint(200,500)), "r": grosor//2, "color": (255,255,255), "est": 1, "res": None},
        {"pos": (random.randint(100,ANCHO-200),ALTO-100), "r": grosor//2, "color": (255,255,255), "est": 1, "res": None},
    ]
    mask_targets = pygame.Surface((ANCHO, ALTO))
    mask_targets.fill((0,0,0))
    for t in targets:
        pygame.draw.circle(mask_targets, t["color"], t["pos"], t["r"])
grosor = 70 #del camino
camino = [(0,100), (400,100), (400,300), (700,300), (700,100), (ANCHO-100,100), #lista de puntos para dibujar los segmentos
          (ANCHO-100,400), (300,400), (300,200),(100,200),(100,500),(ANCHO,ALTO-100)] 
targets = [{"pos": (random.randint(100,400),100), "r": grosor//2.00000000001, "color": (255, 255, 255), "est": 1, "res": None},
    {"pos": (random.randint(400,700),300), "r": grosor//2.00000000001, "color": (255, 255, 255), "est": 1, "res": None},
    {"pos": (ANCHO-100,random.randint(100,400)), "r": grosor//2.00000000001, "color": (255, 255, 255), "est": 1, "res": None},
    {"pos": (random.randint(300,ANCHO-100),400), "r": grosor//2.00000000001, "color": (255, 255, 255), "est": 1, "res": None},
    {"pos": (100,random.randint(200,500)), "r": grosor//2.00000000001, "color": (255, 255, 255), "est": 1, "res": None},
    {"pos": (random.randint(100,ANCHO-200),ALTO-100), "r": grosor//2.00000000001, "color": (255, 255, 255), "est": 1, "res": None},] 
#diccionario para los objetivos, define su posicion fijando una coordenada fija y la otra random, según en qué rama del camino esté
#luego el r para el radio común a todos, color igual, est significa 1 si está activo y 0 si está inactivo porque el paciente ya lo tocó
#res representa el resaltado, si está en None es porque está blanco, cuando el paciente toca la meta habiendo quedado objetivos por tocar
#res deja de ser None y se cambia su color rojo, esta explicado mas abajo
mask_targets = pygame.Surface((ANCHO, ALTO))
mask_targets.fill((0, 0, 0))
for i in range(0,len(targets)):
    pygame.draw.circle(mask_targets, targets[i]["color"], targets[i]["pos"], grosor//2.00000000001) 
    #objetivos invisibles para que el programa detecte la posicion del mouse sin modificar lo que ve el paciente
def dibujar_camino(camino,superficie,color1,color2,grosor):
    for i in range(len(camino) - 1):
        p1 = camino[i]
        p2 = camino[i+1]
        pygame.draw.line(superficie, color1, p1, p2, grosor) #dibuja un segmento entre ambos puntos
        if i != 0: #para que el inicio y la meta queden rectos
            pygame.draw.circle(superficie, color1, p1, grosor//2.00000000001) #suaviza la unión dibujando círculos en esos puntos
def renderTexto(mensaje, color):
    render_texto = font_timer.render(mensaje, True, color)    
    return render_texto
mask_surface = pygame.Surface((ANCHO, ALTO))
mask_surface.fill((0, 0, 0))
dibujar_camino(camino,mask_surface,(255, 255, 255),None,grosor) #camino invisible, en el que se medirá en todo momento la posicion del mouse
pygame.mouse.set_pos((ANCHO,ALTO))
salio, errores, tiempo_inicio, tiempo_fin, tiempo_afuera, tiempo_salida = 1, 0, None, None, 0, 0
targets_inactivos = [0, 0, 0, 0, 0, 0] #cuando son tocados guardan 1 en esa posicion, util para llevar el contador de objetivos
maquinaEstados = "juego" #logica que me enseñaron en el secundario para estructurar las etapas, 0: juego, 1: metricas, 2: cerrar
duracion_salida, duraciones_salidas = 0, [] #tomará las duraciones de cada salida del camino
precision, posiciones, cambios_direccion, dir_anterior = 0, [], 0, None
rigidez_acumulada, ultimo_evento_rigidez, tiempo_fin_record, precision_record, errores_record = 0, 0, None, None, None
running = True
while running: #lee mouse, redibuja todo, repite...
    for event in pygame.event.get(): #EVENTOS
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if maquinaEstados == "metricas": #ventana al terminar el test
                if boton_retry.collidepoint(event.pos):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    reiniciar_juego()
                if boton_quit.collidepoint(event.pos):
                    running = False
    match maquinaEstados:
        case "juego":
            #LÓGICA (actualizar variables)
            mouse_x, mouse_y = pygame.mouse.get_pos() #posición del mouse
            #print(f"({mouse_x},{mouse_y})")
            color = mask_surface.get_at((mouse_x, mouse_y)) #Chequeo si está dentro del camino (LEE SÓLO DE MASK_SURFACE)
            if color == (255, 255, 255, 255):
                if tiempo_inicio == None and mouse_x <=40: #si esta dentro del camino y dentro de la zona de salida
                    tiempo_inicio = pygame.time.get_ticks() #toma el instante en que inicia oficialmente el test
                dentro = True
            else:
                dentro = False
            color_target = mask_targets.get_at((mouse_x, mouse_y)) #Chequeo si está dentro del camino (LEE SÓLO DE MASK_SURFACE)
            if color_target == (255, 255, 255, 255) and tiempo_inicio is not None: #solo si ya inicio el test
                for i in range(len(targets)):
                    dx = mouse_x - targets[i]["pos"][0] #distancia en x del mouse al objetivo
                    dy = mouse_y - targets[i]["pos"][1] #distancia en y del mouse al objetivo
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist <= targets[i]["r"]: #está tocando el objetivo i
                        targets[i]["est"] = 0 #lo deja inactivo asi ya no se muestra ese en especifico
            if tiempo_inicio is not None:
                tiempo = (pygame.time.get_ticks() - tiempo_inicio) / 1000 #contador real del tiempo que lleva
                texto_timer = font_timer.render(f"Tiempo: {tiempo:.2f}s", True, (255,255,255))
                if tiempo_fin is None and dentro and ANCHO-50 <= mouse_x and ALTO-134 <= mouse_y: #si llego a la meta
                    if all(t["est"] == 0 for t in targets): #si toco todos los objetivos
                        tiempo_fin = tiempo
                        tiempo_adentro = tiempo_fin - tiempo_afuera
                        precision = (1 - (tiempo_afuera / tiempo_fin)) * 100
                        temblor = cambios_direccion / tiempo_fin #cambios de dirección por segundo (frecuencia del temblor)
                        rigidez = rigidez_acumulada / tiempo_fin #variaciones del angulo por segundo  
                        #print(rigidez_acumulada)
                        guardar_partida(tiempo_fin, errores, precision, temblor, rigidez) #guarda el .json
                        maquinaEstados = "metricas" #pasa al siguiente estado
                    else:
                        for i in range(len(targets)):
                            if targets[i]["est"] == 1:
                                targets[i]["res"] = tiempo #comienza el resaltado en este instante
                                targets[i]["color"] = (255,0,0) #cambia de color los objetivos
            else:
                tiempo = 0
            if tiempo_inicio is None:
                texto_timer = font_timer.render("Esperando inicio...", True, (255,255,255)) #antes de entrar a la zona de salida
            elif tiempo_fin is None:
                if dentro:
                    color_timer = (255,255,255)
                    if salio == 1: #entró luego de salir
                        salio = 0
                        tiempo_afuera = sum(duraciones_salidas)
                        duracion_salida = tiempo - tiempo_salida
                        duraciones_salidas.append(duracion_salida)
                        duracion_salida=0
                else:
                    color_timer = (255,0,0) #cambia el color del timer si sale del camino
                    if salio == 0 and tiempo_inicio != None and tiempo_fin == None: #salió, ya inició, aún no llegó a la meta
                        salio = 1
                        errores += 1 #suma un error y solo vuelve a sumar si volvio a entrar al camino y volvió a salir
                        tiempo_salida = tiempo #instante en el que salió
                texto_timer = font_timer.render(f"Tiempo: {tiempo:.3f} s", True, color_timer) #tiempo en blanco
            else:
                texto_timer = font_timer.render(f"Tiempo: {tiempo_fin:.3f} s", True, (0,255,0)) #tiempo final
            
            if tiempo_inicio is not None and tiempo_fin is None:
                posiciones.append((mouse_x, mouse_y))
                if len(posiciones) >= 3: #cálculo del temblor y rigidez
                    x1, y1 = posiciones[-3]
                    x2, y2 = posiciones[-2]
                    x3, y3 = posiciones[-1]
                    v1 = (x2 - x1, y2 - y1) #vectores
                    v2 = (x3 - x2, y3 - y2)
                    mag1 = math.hypot(*v1) #magnitud de cada vector usando la hipotenusa de sus componentes
                    mag2 = math.hypot(*v2) #* para extraer los valores de cada tupla
                    if 0<mag1 and 0<mag2: #evitar división por cero
                        cos_theta = (v1[0]*v2[0] + v1[1]*v2[1]) / (mag1 * mag2) #producto escalar de los vectores sobre sus normas
                        cos_theta = max(-1, min(1, cos_theta)) #clamp por seguridad para que sólo esté entre -1 y 1
                        angulo = math.acos(cos_theta)  #obtiene el angulo en radianes con el arcocoseno
                        #print(f"angulo: {angulo:.2f}, mag: {mag2:.2f}")
                        if angulo > 1.1 and mag2 >= 10: #70°
                            if tiempo - ultimo_evento_rigidez > 0.2: #si paso cierto tiempo desde la ultima vez que midió rigidez
                                ultimo_evento_rigidez = tiempo
                                rigidez_acumulada += angulo #a mayor variacion, mas importancia tiene en la rigidez
                        elif angulo > 0.7 and mag2 < 5:  #40° # si el cambio es grande, cuenta como temblor
                            cambios_direccion += 1 #para el temblor tomo en cuenta solamente la cantidad de veces que ocurre
                            #print("temblor")
            for i in range(len(targets)):
                if targets[i]["est"] == 0:
                    targets_inactivos[i] = 1 #chequea cuantos estan inactivos y lo guarda en el vector
            texto_targets = font_timer.render(f"Objetivos: {sum(targets_inactivos)}/{len(targets)}", True, (255,255,255)) 
            tiempo_afuera = sum(duraciones_salidas) #suma la duracion de cada error
            if salio == 1 and tiempo_inicio is not None and tiempo_fin is None: 
                tiempo_afuera += (tiempo - tiempo_salida)
            texto_errores = font_timer.render(f"Errores: {errores}", True, (255,255,255))
            texto_tiempo_afuera = font_timer.render(f"Tiempo afuera: {tiempo_afuera:.3f} s", True, (255,0,0))
            #DIBUJO
            screen.fill((112, 112, 112))  #limpiar pantalla
            dibujar_camino(camino,screen,(0, 116, 255),None,grosor) #dibujar camino visible y suavizado
            for i in range(len(targets)):
                if targets[i]["est"] == 1: #dibuja los objetivos aun no tocados
                    pygame.draw.circle(screen, targets[i]["color"], targets[i]["pos"], grosor//4.00000000001)
            if dentro: #cursor verde si está dentro del camino
                pygame.draw.circle(screen, (0, 255, 0), (mouse_x, mouse_y), 6)
            else: #cursor rojo (y más grande) si salió
                pygame.draw.circle(screen, (255, 0, 0), (mouse_x, mouse_y), 10)
            for i in range(len(targets)):
                if targets[i]["res"] is not None: #si no es None, significa que empezaron a resaltarse
                    if tiempo - targets[i]["res"] > 0.5: #cuando pasen 0,5segs desde que haya empezado
                        targets[i]["res"] = None 
                        targets[i]["color"] = (255, 255, 255) #vuelve al color original
            dibujar_meta()
            dibujar_salida()
            screen.blit(texto_timer, (ANCHO//2 - 80, 20))
            screen.blit(texto_errores, (20, ALTO-40))
            screen.blit(texto_tiempo_afuera, (170, ALTO-40))
            screen.blit(texto_targets, (20, 20))
        case "metricas": #ventana de estadisticas y record
            mouse_pos = pygame.mouse.get_pos()
            dibujar_meta()
            dibujar_salida()
            if temblor<=5: nivel_temblor = "bajo"
            elif temblor <=10: nivel_temblor = "moderado"
            else: nivel_temblor = "alto"
            if rigidez<=0.5: nivel_rigidez = "bajo"
            elif rigidez <=2: nivel_rigidez = "medio"
            else: nivel_rigidez = "alto"
            
            panel = pygame.Rect(100, 120, 500, 350) 
            pygame.draw.rect(screen, (50,50,50), panel, border_radius=8)
            metricas_texto_errores = font_timer.render(f"Errores: {errores}", True, (255,255,255))
            metricas_texto_tiempo = font_timer.render(f"Tiempo: {tiempo_fin:.3f}s", True, (255,255,255))
            metricas_texto_precision = font_timer.render(f"Precisión: {precision:.1f}%", True, (255,255,255))
            metricas_texto_temblor = font_timer.render(f"Temblor: {temblor:.2f} Hz (nivel {nivel_temblor})", True, (255,255,255))
            metricas_texto_rigidez = font_timer.render(f"Rigidez: {rigidez:.2f} rad/s (nivel {nivel_rigidez})", True, (255,255,255))
            #muestra las estadisticas en el cartel principal
            record = pygame.Rect(panel.x + panel.width + 30, panel.y, 230, panel.height) #un segundo panel para el record
            pygame.draw.rect(screen, (50,50,50), record, border_radius=8)
            if errores_record is None or errores_record > errores: #si hizo menos errores, cuenta para el record al ser la máxima prioridad
                errores_record = errores
                tiempo_fin_record = tiempo_fin
                precision_record = precision
            elif tiempo_fin_record is None or tiempo_fin_record > tiempo_fin: #segunda prioridad, menor tiempo
                errores_record = errores
                tiempo_fin_record = tiempo_fin
                precision_record = precision
            elif precision_record is None or precision_record < precision: #tercera prioridad, mayor precisión
                errores_record = errores
                tiempo_fin_record = tiempo_fin
                precision_record = precision      
            record_texto_tiempo = font_timer.render(f"Tiempo: {tiempo_fin_record:.3f}s", True, (255,255,255))
            record_texto_precision = font_timer.render(f"Precisión: {precision_record:.1f}%", True, (255,255,255))
            record_texto_temblor = font_timer.render(f"Temblor: {temblor:.2f} Hz", True, (255,255,255))
            record_texto_rigidez = font_timer.render(f"Rigidez: {rigidez:.2f} rad/s", True, (255,255,255))
            record_texto_errores = font_timer.render(f"Errores: {errores_record}", True, (255,255,255))
            record_texto_record = font_record.render(f"Mejor puntaje", True, (255,255,255))
            
            boton_retry = pygame.Rect(panel.x + 100, panel.y + 280, 140, 40)
            boton_quit = pygame.Rect(panel.x + 330, panel.y + 280, 80, 40)
            if boton_retry.collidepoint(mouse_pos): color_boton_retry = (132,252,129)
            else: color_boton_retry = (0,200,0) #le da un efecto si el mouse pasa encima del botón
            if boton_quit.collidepoint(mouse_pos): color_boton_quit = (255,120,92)
            else: color_boton_quit = (200,0,0)
            if boton_retry.collidepoint(mouse_pos) or boton_quit.collidepoint(mouse_pos):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW) #simplemente motivo visual

            pygame.draw.rect(screen, color_boton_retry, boton_retry, border_radius=4)
            pygame.draw.rect(screen, color_boton_quit, boton_quit, border_radius=4)
            screen.blit(font_timer.render("Reintentar", True, (255,255,255)), (boton_retry.x+15, boton_retry.y+5))
            screen.blit(font_timer.render("Salir", True, (255,255,255)), (boton_quit.x+18, boton_quit.y+5))
            screen.blit(metricas_texto_errores, (panel.x + 50, panel.y + 20))
            screen.blit(metricas_texto_tiempo, (panel.x + 50, panel.y + 70))
            screen.blit(metricas_texto_precision, (panel.x + 50, panel.y + 120))
            screen.blit(metricas_texto_temblor, (panel.x + 50, panel.y + 170))
            screen.blit(metricas_texto_rigidez, (panel.x + 50, panel.y + 220))
            screen.blit(record_texto_errores, (record.x + 10, record.y + 20))
            screen.blit(record_texto_tiempo, (record.x + 10, record.y + 70))
            screen.blit(record_texto_precision, (record.x + 10, record.y + 120))
            screen.blit(record_texto_temblor, (record.x + 10, record.y + 170))
            screen.blit(record_texto_rigidez, (record.x + 10, record.y + 220))
            screen.blit(record_texto_record, (record.x + 44, record.y + record.height - 30))
            screen.blit(imagen_trofeo, (record.x + record.width//2 - 36, record.y + record.height - 107)) #referencia al fútbol, puede gustar si el paciente es fánatico del deporte
            screen.blit(imagen_laureles, (record.x + record.width//2 - 35, record.y + record.height - 102)) #decoración visual
    pygame.display.flip() #ACTUALIZAR PANTALLA
    clock.tick(60) #cantidad de veces por segundo que corre el while running
pygame.quit()

