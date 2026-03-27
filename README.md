# codigos-data-logger

**Universidad del Bío-Bío | Laboratorio CIM**
**Carrera:** Ingeniería Civil en Informática

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

1. Ve a la sección **[Releases]
