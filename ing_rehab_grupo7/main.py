import subprocess #permitirá abrir los distintos .py respectivos de cada test
from tkinter import *
from tkinter import font, messagebox as msgbox, messagebox, simpledialog, ttk
import tkinter as tk #librería para el formulario del login
import random
import os
path = os.path.dirname(__file__) #ruta relativa de la carpeta del proyecto
path_img = os.path.join(path, "imagenes")
global usuarios
usuarios = ["a"] #usuario admin
claves = ["aaaaaaaa"] #contraseña admin
verde_oscuro = "#769382" #distintos colores guardados para la paleta
verde_claro = "#c0c389"
beige = ""
azul = "#007bff"
color_principal = verde_oscuro

def hayEntrada(event, field_name): #si hay un texto ingresado en la entrada de texto
    if event.widget.get() == field_name:
        event.widget.delete(0, tk.END)
        event.widget.config(fg='black')  #negro, ya que lo escrito por el paciente va negro

def entradaVacia(event, field_name): #si no hay un texto ingresado en la entrada de texto
    if event.widget.get() == "":
        event.widget.insert(0, field_name)
        event.widget.config(show='')
        event.widget.config(fg='gray')  #gris, asi el mensaje de guia va gris

root = tk.Tk() #se define la ventana principal, con su ícono, tamaño, título
icon = tk.PhotoImage(file=path_img+r"\icon_rehab.png") 
root.iconphoto(True,icon)
root.geometry('700x300+100+100')
root.configure(bg='#fff')
root.title("Rehabilitación")
root.resizable(False, False) #No es posible cambiar el tamaño de la ventana
fuente = font.Font(family="Microsoft YaHei UI Light",size=20,weight='normal')

logo = PhotoImage(file=path_img+r"\saludlogo.png") #/\
logo = PhotoImage(file=path_img+r"\saludlogo.png").subsample(4,4)  #reduce 25% el tamaño de la imagen
logo_label = tk.Label(root,image=logo,bg='#fff')
logo_label.pack(side=tk.LEFT,padx=(10,10),pady=1)

global loginMensaje #global asi luego se puede cambiar su estado para registrarse
loginMensaje = tk.StringVar(value='Iniciar Sesión')
login_label = tk.Label(root,textvariable=loginMensaje,fg=color_principal,bg='#fff',font=fuente)
login_label.pack(side=tk.TOP, padx=(1,1),pady=(20,1))

global entry_user 
entry_user = Entry(root,width=40,fg='gray',border=0,bg='white',font=("Microsoft YaHei UI Light",12),
                    relief='sunken',insertwidth='1')
entry_user.pack(side=tk.TOP, padx=(10,1),pady=(20,1))
entry_user.insert(0, 'Nombre del socio')
entry_user.bind("<FocusIn>", lambda e: hayEntrada(e, "Nombre del socio")) #predetermina el texto de la entrada
entry_user.bind("<FocusOut>", lambda e: entradaVacia(e, "Nombre del socio")) #predetermina el texto de la entrada
Frame(width=363,height=1,bg='black').place(x=298,y=105)

global entry_pass
entry_pass = Entry(root,width=40,fg='gray',border=0,bg='white',show='',font=("Microsoft YaHei UI Light",12))
entry_pass.pack(side=tk.TOP, padx=(10,1),pady=(30,1))
entry_pass.bind("<FocusIn>", lambda e: hayEntrada(e, "Contraseña")) #predetermina el texto de la entrada
entry_pass.bind("<FocusOut>", lambda e: entradaVacia(e, "Contraseña")) #predetermina el texto de la entrada
entry_pass.insert(0, 'Contraseña')
Frame(width=363,height=1,bg='black').place(x=298,y=159)

global estadoBoton
global estadoMensaje
global estadoMensajeBoton
estadoBoton = tk.StringVar(value='Sign In')
bot_enter = tk.Button(root,width=10,textvariable=estadoBoton,font=("Microsoft YaHei UI Light",12,'bold'),
                        fg='#fff',bg=color_principal,activebackground=verde_claro,activeforeground="white",border=0,cursor='hand2',command=lambda: iniciarSesion(entry_user,entry_pass))
bot_enter.place(x=430,y=200)
bot_enter.bind("<Enter>", lambda e:bot_enter.config(bg=verde_claro))
bot_enter.bind("<Leave>", lambda e:bot_enter.config(bg=color_principal))
estadoMensaje = tk.StringVar(value='Todavía no tienes una cuenta?')
mensaje = tk.Label(root,textvariable=estadoMensaje,fg='black',bg='white',font=("Microsoft YaHei UI Light",10))
mensaje.place(x=350,y=250)
estadoMensajeBoton = tk.StringVar(value='Registrarse')
bot_mensaje = tk.Button(root,width=9,textvariable=estadoMensajeBoton,bg='white',border=0,
                        cursor='hand2',fg=color_principal,font=("Microsoft YaHei UI Light",10)
                        ,command=lambda:definirEstado(imagenDesocultar)) #para que cambie la imagen de ocultar o no contraseña (ojo tachado o no)
bot_mensaje.place(x=535,y=248)

global bot_ocultar #boton para ocultar la contraseña
imagenOcultar = tk.PhotoImage(file=path_img+r'\ojoOculto.PNG')
imagenDesocultar = tk.PhotoImage(file=path_img+r'\ojoVisible.PNG')
bot_ocultar = tk.Button(root,image=imagenDesocultar,bg='white',border=0,cursor='hand2',
                        command=lambda: ocultarContra(imagenDesocultar,imagenOcultar))
bot_ocultar.place(x=630,y=160)

 
def ocultarContra(imgVisible,imgOculta): #cambia entre dos estados el boton para ocultar la contraseña
    global bot_ocultar
    global entry_pass
    if bot_ocultar['image'] == str(imgVisible):
        bot_ocultar['image'] = imgOculta
        if entry_pass.get().strip() != 'Contraseña' and entry_pass.get().strip() != "":
            entry_pass.config(show='*')
    else:
        bot_ocultar['image'] = str(imgVisible)
        entry_pass.config(show='')
        
def definirEstado(imgVisible): #cambia entre dos estados el boton para ocultar la contraseña
    global loginMensaje
    global estadoBoton
    global estadoMensaje
    global estadoMensajeBoton
    global entry_user
    global entry_pass
    global bot_ocultar
    if loginMensaje.get() == 'Iniciar Sesión':
        loginMensaje.set('Registrarse')
        estadoMensaje.set('Ya tienes una cuenta?')
        estadoMensajeBoton.set('Iniciar sesión')
        estadoBoton.set('Sign Up')
        cambiarEntrada(entry_user,'Nombre del socio')
        bot_ocultar.config(image=imgVisible)
        cambiarEntrada(entry_pass,'Contraseña')
        bot_ocultar.config(image=imgVisible)
    else:
        loginMensaje.set('Iniciar Sesión')
        estadoMensaje.set('Todavía no tienes una cuenta?')
        estadoMensajeBoton.set('Registrarse')
        estadoBoton.set('Sign In')
        cambiarEntrada(entry_user,'Nombre del socio')
        bot_ocultar.config(image=imgVisible)
        cambiarEntrada(entry_pass,'Contraseña')
        bot_ocultar.config(image=imgVisible)
        
def cambiarEntrada(entry, field_name): #cambia al mensaje de bienvenida
    entry.delete(0, tk.END)
    entry.insert(0, field_name)
    entry.config(fg='gray')
    entry.config(show='')

def iniciarSesion(entryUser, entryPass): #toma las credenciales de las entradas de texto
        global loginMensaje
        usuario_ingresado = entryUser.get().strip()
        contra_ingresada = entryPass.get().strip()
        if usuario_ingresado == "" or usuario_ingresado == "Nombre del socio" or contra_ingresada == "" or contra_ingresada == "Contraseña":
            messagebox.showinfo("ERROR", "Por favor ingrese usuario y contraseña.")
        else:
            if loginMensaje.get() == 'Iniciar Sesión':
                if usuario_ingresado in usuarios:
                    index = usuarios.index(usuario_ingresado)
                    if contra_ingresada == claves[index]:
                        print("inicio")
                        iniciarMenu(usuario_ingresado, contra_ingresada)
                    else:
                        messagebox.showinfo("ERROR", "Contraseña incorrecta.")
                else:
                    messagebox.showinfo("ERROR", "Nombre de usuario incorrecto.")
            else: #registrarse
                if usuario_ingresado in usuarios:
                    messagebox.showinfo("ERROR", "Este usuario ya existe. Pruebe con otro nombre de usuario.")
                else:
                    if len(contra_ingresada) >= 8:
                        usuarios.append(usuario_ingresado)
                        claves.append(contra_ingresada)
                        messagebox.showinfo("Registro", "Nuevo usuario registrado. Puede iniciar sesión.")
                    else:
                        messagebox.showinfo("ERROR", "La contraseña debe tener al menos 8 caracteres. Intente nuevamente.")

def iniciarMenu(user1, pass1): #inicia la ventana del menu, cerrando previamente el login
    root.withdraw()
    menu = tk.Toplevel() #Creo otra instancia de la clase Tk
    menu.icon = tk.PhotoImage(file=path_img+r'\icon_rehab.png')
    menu.iconphoto(True,menu.icon)
    menu.geometry('700x500+150+150')
    menu.configure(bg='#fff')
    menu.title("Rehabilitación")
    frame = tk.Frame(menu, bg="white")
    frame.pack(expand=True)
    fuente = font.Font(family="Microsoft YaHei UI Light",size=20,weight='normal')
    saludo = tk.Label(menu,
        text=f"Bienvenido {user1} a una nueva sesión de Rehabilitación", #mensaje de bienvenida personalizado
        font=fuente, fg=color_principal, bg='white')
    saludo.pack(in_=frame, pady=(5,30))
    #según el botón que se presione, se abre el proceso de cada test
    bot_estabilizador = crear_boton(menu, 'Estabilizador de Trayectoria', 
                                    lambda: subprocess.Popen(["python", path+r"\estabilizadorTrayectoria.py", user1]))
    bot_estabilizador.pack(in_=frame, pady=20)
    bot_drag = crear_boton(menu, 'Drag & Drop (Arrastre sostenido)', 
                           lambda: subprocess.Popen(["python", path+r"\drag_drop.py", user1]))
    bot_drag.pack(in_=frame, pady=15)
    bot_sensibilidad = crear_boton(menu, 'Ganancia Adaptativa', 
                                   lambda: subprocess.Popen(["python", path+r"\adaptive_gain.py", user1]))
    bot_sensibilidad.pack(in_=frame, pady=15)
    
    agregar_tooltip(bot_estabilizador, 
                    "Ejercicio de control fino y espasticidad que consiste en seguir un camino laberíntico sin tocar los bordes. \nMide rigidez y temblor.")
    
    agregar_tooltip(bot_drag, 
                    "Arrastre continuo de un punto a otro sin soltar. \nMide fatiga muscular y control de la presión.")
    
    agregar_tooltip(bot_sensibilidad,
                    "Módulo de ejercicios de control y motricidad. \nMide rango de movimiento y te asigna tu sensibilidad adecuada.")
    #funciones que muestran los tooltips, carteles que explican brevemente de qué se trata cada test y qué mide
    def cerrar_menu():
        menu.destroy()
        root.deiconify()
    menu.protocol("WM_DELETE_WINDOW", cerrar_menu)
    #cierra la ventana del menu al ingresar en un test
def crear_boton(parent, texto, comando): #crea un botón según los parámetros que se le otorguen
    boton = tk.Button(parent,
        text=texto,
        font=("Microsoft YaHei UI Light", 14, "bold"),
        bg=color_principal,
        fg="white",
        activebackground=verde_claro,
        activeforeground="white",
        width=18,
        height=3,
        border=0,
        cursor="hand2",
        justify="center",
        wraplength=160,
        relief="flat"
    )

    def hover_on(e): #función de hover para que cambie el color del fondo al presionar el botón
        boton["bg"] = verde_claro
        boton["relief"] = "raised"
        print("hover")

    def hover_off(e): 
        boton["bg"] = color_principal
        boton["relief"] = "flat"

    boton.bind("<Enter>", hover_on) #detecta si el mouse clickeo en el botón o no
    boton.bind("<Leave>", hover_off)

    boton.config(command=comando) #acciona el comando de ingreso al respectivo test
    return boton

def agregar_tooltip(widget, texto):
    tooltip = None
    after_id = None

    def mostrar(event):
        nonlocal tooltip
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)

        #posición relativa al mouse para mover el tooltip
        x = event.x_root + 40
        y = event.y_root + 10
        tooltip.geometry(f"+{x}+{y}")

        frame = tk.Frame(tooltip, bg="#333333", bd=1, relief="solid")
        frame.pack()

        label = tk.Label(frame,
            text=texto,
            bg="#333333",
            fg="white",
            font=("Segoe UI", 11),   #más grande
            wraplength=300,          #más ancho
            justify="left",
            padx=12,                 #más padding
            pady=8
        )
        label.pack()

    def mover(event): #mueve el tooltip según la posición del mouse
        nonlocal tooltip
        if tooltip:
            x = event.x_root + 15
            y = event.y_root + 10
            tooltip.geometry(f"+{x}+{y}")

    def ocultar(): #oculta el tooltip si el mouse se alejó del botón
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None

    def entrar(event): #función que muestra el tooltip y coloca el after_id en true
        nonlocal after_id
        after_id = widget.after(700, lambda: mostrar(event))

    def salir(event):
        nonlocal after_id
        if after_id:
            widget.after_cancel(after_id)
            after_id = None
        ocultar()

    widget.bind("<Enter>", entrar) #si el mouse se encuentra dentro del rango del botón
    widget.bind("<Leave>", salir) #si el mouse salió del rango del botón
    widget.bind("<Motion>", mover)  #sigue al mouse

root.mainloop() 
