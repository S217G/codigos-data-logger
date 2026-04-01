# codigos-data-logger

**Universidad del Bío-Bío | Laboratorio CIM**
**Carrera:** Ingeniería de Ejecucio en Computacion e Informática

Este repositorio contiene el código fuente (C++ y Python) y la documentación de un sistema de monitorización de resistencia de materiales. El sistema utiliza un microcontrolador ESP32 para leer la deformación de materiales sometidos a tensión mediante un encoder rotatorio y enviar los datos para su análisis.

## 🚀 Características Principales (Arquitectura Híbrida)

A diferencia de los data loggers tradicionales, este sistema opera en dos frentes simultáneos para garantizar cero pérdida de datos:
1. **Modo Independiente (Hardware):** Utiliza interrupciones en la memoria RAM del ESP32 para recolectar datos a alta velocidad y guardarlos en una memoria microSD mediante un sistema de *buffer*.
2. **Modo Monitor (Software):** Transmite los datos por USB hacia una aplicación de escritorio desarrollada en Python. La interfaz gráfica procesa la información, ajusta el diámetro de calibración y renderiza una gráfica de osciloscopio en tiempo real.

## 🛠️ Hardware Requerido

El sistema está construido con los siguientes componentes físicos:
* **Microcontrolador:** ESP32-C3 Super Mini + Placa de expansión.
* **Módulo de Memoria:** Data Logging board (ID:8122) para almacenamiento en microSD.
* **Seguridad de Voltaje:** Convertidor de nivel lógico de 4 canales (3.3V a 5V).
* **Sensor:** Encoder Rotatorio LPD3806 (1200 pulsos por revolución).
* **Visualización Local:** Pantalla OLED Tenstar de 0.91 pulgadas (I2C).

## 💻 Instalación y Uso de la Aplicación (Python)

Si solo deseas utilizar el programa de monitoreo en tu computador sin modificar el código fuente, sigue estos pasos:

1. Ve a la sección **[Releases]** a la derecha de esta página.
2. Descarga el archivo `Monitor_de_Elasticidad.exe`.
3. Conecta el ESP32 por USB a tu computador.
4. Ejecuta el archivo `.exe` (no requiere instalación).
5. Selecciona el puerto COM correspondiente y haz clic en **Conectar**.
6. Ajusta el "Diámetro Efectivo" en la sección de calibración (ej: `1.910` cm) y presiona **Aplicar**.
7. Selecciona una carpeta de destino y presiona **Iniciar Grabación** para generar tu archivo `.csv`.

## 📂 Estructura del Repositorio

* `/arduino`: Contiene el firmware en C++ (`.ino`) que debe ser subido al ESP32-C3.
* `/python_app`: Contiene el código fuente `monitor_de_elasticidad` desarrollado con `customtkinter` y `matplotlib`.
* `/docs`: Manuales de usuario, diagramas de conexión y recursos gráficos.

## ⚙️ Desarrollo y Compilación (Para desarrolladores)

Si deseas modificar la interfaz gráfica, asegúrate de tener Python 3.10+ instalado y ejecuta:

```bash
pip install customtkinter pyserial matplotlib
