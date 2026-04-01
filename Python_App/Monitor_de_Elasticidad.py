import customtkinter as ctk
#import serial
import serial.tools.list_ports 
import threading
import time
from datetime import datetime
import csv
import os
import pandas as pd
from tkinter import filedialog 

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Configuración global del tema
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DataLoggerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Monitor de Elasticidad - Pro Edition")
        self.geometry("950x650") 
        self.resizable(False, False)

        # Variables de estado del sistema
        self.esp32 = None
        self.is_connected = False
        self.is_logging = False
        self.csv_file = None
        self.csv_writer = None
        self.ruta_guardado = os.getcwd() 

        # Variables de recolección de datos y gráfica
        self.start_time = 0
        self.x_data = []
        self.y_data = []
        self.current_val = 0.0
        self.current_sufijo = "cm"
        self.current_pulsos = 0

        self.crear_interfaz()
        self.actualizar_lista_puertos() 

    def crear_interfaz(self):
        # ==========================================
        # COLUMNA IZQUIERDA: PANEL DE CONTROL
        # ==========================================
        self.frame_controles = ctk.CTkFrame(self, width=300)
        self.frame_controles.pack(side="left", fill="y", padx=10, pady=10)

        # --- SECCIÓN 1: CONEXIÓN SERIAL ---
        frame_conexion = ctk.CTkFrame(self.frame_controles)
        frame_conexion.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(frame_conexion, text="1. CONEXIÓN AL HARDWARE", font=("Roboto", 14, "bold")).pack(pady=5)
        
        fila_puertos = ctk.CTkFrame(frame_conexion, fg_color="transparent")
        fila_puertos.pack(pady=5)
        
        self.combo_puertos = ctk.CTkOptionMenu(fila_puertos, width=120)
        self.combo_puertos.pack(side="left", padx=5)
        
        btn_recargar = ctk.CTkButton(fila_puertos, text="🔄", width=40, command=self.actualizar_lista_puertos)
        btn_recargar.pack(side="left", padx=5)

        self.btn_conectar = ctk.CTkButton(frame_conexion, text="Conectar", command=self.conectar_serial)
        self.btn_conectar.pack(pady=10)
        
        self.lbl_estado = ctk.CTkLabel(frame_conexion, text="Estado: Desconectado", text_color="gray")
        self.lbl_estado.pack(pady=5)

        # --- SECCIÓN 2: CALIBRACIÓN DE HARDWARE ---
        self.frame_calib = ctk.CTkFrame(self.frame_controles)
        ctk.CTkLabel(self.frame_calib, text="2. CALIBRACIÓN", font=("Roboto", 14, "bold")).pack(pady=5)
        
        self.unidad_var = ctk.StringVar(value="Centímetros (cm)")
        self.combo_unidades = ctk.CTkOptionMenu(
            self.frame_calib, values=["Milímetros (mm)", "Centímetros (cm)", "Metros (m)"], 
            variable=self.unidad_var, command=self.cambiar_unidad_hardware)
        self.combo_unidades.pack(pady=5)

        self.diametro_entry = ctk.CTkEntry(self.frame_calib, placeholder_text="Diámetro", width=120)
        self.diametro_entry.insert(0, "1.910") 
        self.diametro_entry.pack(pady=5)

        self.btn_calibrar = ctk.CTkButton(self.frame_calib, text="Aplicar", command=self.enviar_calibracion)
        self.btn_calibrar.pack(pady=5)

        self.btn_reset = ctk.CTkButton(self.frame_calib, text="Resetear a 0", fg_color="#D97706", hover_color="#B45309", command=self.resetear_medidor)
        self.btn_reset.pack(pady=5)

        # --- SECCIÓN 3: CONTROL DE EXPORTACIÓN ---
        self.frame_guardado = ctk.CTkFrame(self.frame_controles)
        ctk.CTkLabel(self.frame_guardado, text="3. REGISTRO DE DATOS", font=("Roboto", 14, "bold")).pack(pady=5)

        self.btn_ruta = ctk.CTkButton(self.frame_guardado, text="Elegir Carpeta", fg_color="gray", command=self.elegir_ruta)
        self.btn_ruta.pack(pady=5)
        
        self.lbl_ruta = ctk.CTkLabel(self.frame_guardado, text="Ruta: Carpeta actual", font=("Roboto", 10), text_color="gray")
        self.lbl_ruta.pack(pady=0)

        self.formato_var = ctk.StringVar(value=".csv")
        self.combo_formato = ctk.CTkOptionMenu(self.frame_guardado, values=[".csv", ".xlsx (Excel)"], variable=self.formato_var)
        self.combo_formato.pack(pady=5)

        self.btn_iniciar = ctk.CTkButton(self.frame_guardado, text="INICIAR GRABACIÓN", fg_color="green", hover_color="darkgreen", command=self.iniciar_grabacion)
        self.btn_iniciar.pack(pady=10)

        self.btn_detener = ctk.CTkButton(self.frame_guardado, text="DETENER", fg_color="red", hover_color="darkred", command=self.detener_grabacion, state="disabled")
        self.btn_detener.pack(pady=5)


        # ==========================================
        # COLUMNA DERECHA: MONITORIZACIÓN Y GRÁFICA
        # ==========================================
        self.frame_derecho = ctk.CTkFrame(self)
        self.frame_derecho.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Layout inicial de espera
        self.lbl_espera = ctk.CTkLabel(self.frame_derecho, text="🔌 Por favor, conecte el dispositivo\npara inicializar el sistema.", font=("Roboto", 24), text_color="gray")
        self.lbl_espera.pack(expand=True)

        # Elementos dinámicos del monitor
        self.lbl_titulo_monitor = ctk.CTkLabel(self.frame_derecho, text="MONITOR EN TIEMPO REAL", font=("Roboto", 20, "bold"))
        self.lbl_distancia = ctk.CTkLabel(self.frame_derecho, text="0.00 cm", font=("Roboto", 60, "bold"), text_color="#00BFFF")
        self.lbl_pulsos = ctk.CTkLabel(self.frame_derecho, text="Pulsos Crudos: 0", font=("Roboto", 16), text_color="gray")

        # Inicialización de entorno Matplotlib
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor('#2B2B2B') 
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2B2B2B')
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_derecho)

    # ==========================================
    # LÓGICA DE INTERFAZ Y EVENTOS
    # ==========================================
    def mostrar_interfaz_completa(self):
        self.lbl_espera.pack_forget()
        self.frame_calib.pack(pady=10, padx=10, fill="x")
        self.frame_guardado.pack(pady=10, padx=10, fill="x")
        self.lbl_titulo_monitor.pack(pady=10)
        self.lbl_distancia.pack(pady=0)
        self.lbl_pulsos.pack(pady=5)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def ocultar_interfaz_completa(self):
        self.frame_calib.pack_forget()
        self.frame_guardado.pack_forget()
        self.lbl_titulo_monitor.pack_forget()
        self.lbl_distancia.pack_forget()
        self.lbl_pulsos.pack_forget()
        self.canvas.get_tk_widget().pack_forget()
        self.lbl_espera.pack(expand=True)

    def actualizar_lista_puertos(self):
        puertos = [port.device for port in serial.tools.list_ports.comports()]
        if not puertos:
            puertos = ["Sin dispositivos"]
        self.combo_puertos.configure(values=puertos)
        self.combo_puertos.set(puertos[0])

    def elegir_ruta(self):
        ruta = filedialog.askdirectory(title="Selecciona directorio de almacenamiento")
        if ruta:
            self.ruta_guardado = ruta
            ruta_corta = f"...{ruta[-25:]}" if len(ruta) > 25 else ruta
            self.lbl_ruta.configure(text=f"Ruta: {ruta_corta}")

    # ==========================================
    # COMUNICACIÓN SERIAL Y PROCESAMIENTO
    # ==========================================
    def conectar_serial(self):
        if not self.is_connected:
            puerto = self.combo_puertos.get()
            if puerto == "Sin dispositivos": return

            try:
                self.esp32 = serial.Serial(puerto, 115200, timeout=0.1)
                self.is_connected = True
                
                self.lbl_estado.configure(text=f"Conectado a {puerto}", text_color="green")
                self.btn_conectar.configure(text="Desconectar", fg_color="red")
                
                self.mostrar_interfaz_completa()

                self.x_data = []
                self.y_data = []
                self.start_time = time.time()

                self.enviar_calibracion()
                self.cambiar_unidad_hardware(self.unidad_var.get())

                self.hilo_lectura = threading.Thread(target=self.leer_datos, daemon=True)
                self.hilo_lectura.start()
                self.actualizar_interfaz_y_grafica() 

            except Exception as e:
                self.lbl_estado.configure(text="Error de conexión", text_color="red")
        else:
            self.desconectar_serial()

    def desconectar_serial(self):
        self.detener_grabacion()
        self.is_connected = False
        time.sleep(0.5)
        if self.esp32 and self.esp32.is_open:
            self.esp32.close()
        
        self.lbl_estado.configure(text="Desconectado", text_color="gray")
        self.btn_conectar.configure(text="Conectar", fg_color=['#3B8ED0', '#1F6AA5'])
        self.ocultar_interfaz_completa()

    def enviar_calibracion(self):
        if self.is_connected:
            diametro = self.diametro_entry.get()
            self.esp32.write(f"CALIB:{diametro}\n".encode('utf-8'))

    def cambiar_unidad_hardware(self, seleccion):
        if self.is_connected:
            if seleccion == "Milímetros (mm)": self.esp32.write(b"UNIT:mm\n")
            elif seleccion == "Metros (m)": self.esp32.write(b"UNIT:m\n")
            else: self.esp32.write(b"UNIT:cm\n")

    def resetear_medidor(self):
        if self.is_connected:
            self.esp32.write(b"RESET\n")
            self.x_data = [] 
            self.y_data = []
            self.start_time = time.time()

    def iniciar_grabacion(self):
        if self.is_connected:
            fecha_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nombre_archivo = f"Registro_{fecha_str}.csv"
            
            self.ruta_completa_actual = os.path.join(self.ruta_guardado, nombre_archivo)
            
            self.csv_file = open(self.ruta_completa_actual, mode='w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            unidad_actual = self.unidad_var.get()
            self.csv_writer.writerow(["Fecha", "Hora", f"Distancia ({unidad_actual})", "Pulsos"])
            
            self.esp32.write(b"START\n")
            self.is_logging = True
            
            self.btn_iniciar.configure(state="disabled")
            self.btn_detener.configure(state="normal")
            self.combo_unidades.configure(state="disabled") 
            self.btn_ruta.configure(state="disabled")
            self.combo_formato.configure(state="disabled")

    def detener_grabacion(self):
        if self.is_connected and self.is_logging:
            self.esp32.write(b"STOP\n")
            self.is_logging = False
            
            if self.csv_file:
                self.csv_file.close()
            
            # Exportación condicional a formato .xlsx mediante Pandas
            if self.formato_var.get() == ".xlsx (Excel)":
                try:
                    df = pd.read_csv(self.ruta_completa_actual)
                    ruta_excel = self.ruta_completa_actual.replace(".csv", ".xlsx")
                    df.to_excel(ruta_excel, index=False)
                    os.remove(self.ruta_completa_actual)
                except Exception as e:
                    print(f"Excepción en conversión a Excel: {e}")

            self.btn_iniciar.configure(state="normal")
            self.btn_detener.configure(state="disabled")
            self.combo_unidades.configure(state="normal")
            self.btn_ruta.configure(state="normal")
            self.combo_formato.configure(state="normal")

    def leer_datos(self):
        import random # Importamos random solo para el simulador
        dist_falsa = 5.0 
        pulsos_falsos = 100

        while self.is_connected:
            try:
                if self.esp32.in_waiting > 0:
                    linea = self.esp32.readline().decode('utf-8').strip()
                    
                    if linea and not linea.startswith("ACK_"):
                        datos = linea.split(',')
                        if len(datos) == 2:
                            distancia_cm = float(datos[0])
                            self.current_pulsos = int(datos[1])
                            
                            unidad = self.unidad_var.get()
                            if unidad == "Milímetros (mm)":
                                self.current_val = distancia_cm * 10.0
                                self.current_sufijo = "mm"
                            elif unidad == "Metros (m)":
                                self.current_val = distancia_cm / 100.0
                                self.current_sufijo = "m"
                            else:
                                self.current_val = distancia_cm
                                self.current_sufijo = "cm"

                            tiempo_actual = time.time() - self.start_time
                            self.x_data.append(tiempo_actual)
                            self.y_data.append(self.current_val)
                            
                            if len(self.x_data) > 100:
                                self.x_data.pop(0)
                                self.y_data.pop(0)
                            
                            if self.is_logging and self.csv_writer:
                                ahora = datetime.now()
                                self.csv_writer.writerow([
                                    ahora.strftime("%Y-%m-%d"), 
                                    ahora.strftime("%H:%M:%S.%f")[:-4], 
                                    f"{self.current_val:.2f}", 
                                    self.current_pulsos
                                ])
            except Exception:
                pass # Ignorar tramas corruptas en la transmisión Serial
            time.sleep(0.01)

    def actualizar_interfaz_y_grafica(self):
        if self.is_connected:
            self.lbl_distancia.configure(text=f"{self.current_val:.2f} {self.current_sufijo}")
            self.lbl_pulsos.configure(text=f"Pulsos Crudos: {self.current_pulsos}")

            self.ax.clear()
            self.ax.plot(self.x_data, self.y_data, color="#00BFFF", linewidth=2.5)
            self.ax.set_ylabel(f"Distancia ({self.current_sufijo})", color="white")
            self.ax.set_xlabel("Tiempo (s)", color="gray")
            
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['bottom'].set_color('gray')
            self.ax.spines['left'].set_color('gray')
            
            self.canvas.draw()
            self.after(100, self.actualizar_interfaz_y_grafica)

if __name__ == "__main__":
    app = DataLoggerApp()
    app.mainloop()