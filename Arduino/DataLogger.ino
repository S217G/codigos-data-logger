#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <RTClib.h>

// ==========================================
// CONFIGURACIÓN DE PINES (ESP32-C3)
// ==========================================
const int pinA = 7;           
const int pinB = 10;          
#define I2C_SDA 8             
#define I2C_SCL 9             

const int SPI_SCK = 4;
const int SPI_MISO = 5;
const int SPI_MOSI = 6;
const int SD_CS = 3;

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET -1 
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
RTC_DS1307 rtc;
File dataFile;

// ==========================================
// VARIABLES GLOBALES DEL SISTEMA
// ==========================================
volatile long Pos = 0;        
float distance = 0.0;         
bool isLogging = false;       
bool sd_ok = false;
String currentFileName = "";

String currentUnit = "cm";
float unitMultiplier = 1.0;

const float pi = 3.14159;
const int N_PULSOS_VUELTA = 1200; 
float diametro_polea_cm = 1.910;  
float cm_per_pulse = 0.0;

unsigned long lastMsgTime = 0;
const unsigned long samplingInterval = 20; // Frecuencia de muestreo (50 Hz)
unsigned long startTime = 0; 
long lastRecordedPos = -999999; // Control de posición para optimizar escritura en SD

// ==========================================
// CONFIGURACIÓN DEL BUFFER RAM
// ==========================================
#define BUFFER_SIZE 25
String dataBuffer[BUFFER_SIZE];
int bufferIndex = 0;

// ==========================================
// INTERRUPCIÓN DEL ENCODER
// ==========================================
void IRAM_ATTR encoderISR() {
  static int lastStateA = LOW;
  int currentStateA = digitalRead(pinA);
  int currentStateB = digitalRead(pinB);

  if (currentStateA != lastStateA) {
    if (currentStateB != currentStateA) { Pos++; } 
    else { Pos--; }
  }
  lastStateA = currentStateA;
}

void recalcularFactor() {
  float perimetro = pi * diametro_polea_cm;
  cm_per_pulse = perimetro / (float)N_PULSOS_VUELTA;
}

// ==========================================
// INICIALIZACIÓN (SETUP)
// ==========================================
void setup() {
  Serial.begin(115200); 

  Wire.begin(I2C_SDA, I2C_SCL);
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("Fallo OLED");
  }
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0,0);
  display.println("Iniciando...");
  display.display();

  if (!rtc.begin()) {
    Serial.println("Fallo RTC");
  } else if (!rtc.isrunning()) {
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__))); 
  }

  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI, SD_CS);
  if (!SD.begin(SD_CS)) {
    Serial.println("Fallo SD");
    display.println("ERROR: Sin SD");
    display.display();
    sd_ok = false;
  } else {
    sd_ok = true;
    display.println("SD Detectada OK");
    display.display();
    
    DateTime now = rtc.now();
    currentFileName = "/log_" + String(now.month()) + String(now.day()) + "_" + String(now.hour()) + String(now.minute()) + ".csv";
    dataFile = SD.open(currentFileName, FILE_WRITE);
    if (dataFile) {
      dataFile.println("Tiempo(s),Distancia,Pulsos");
      dataFile.close();
    }
    
    isLogging = true; 
    bufferIndex = 0;
    startTime = millis(); 
    lastRecordedPos = -999999;
  }
  delay(1000);

  pinMode(pinA, INPUT_PULLUP);
  pinMode(pinB, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(pinA), encoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(pinB), encoderISR, CHANGE);

  recalcularFactor();
}

// ==========================================
// FUNCIONES AUXILIARES
// ==========================================
void guardarBufferEnSD() {
  if (sd_ok && isLogging && bufferIndex > 0) {
    dataFile = SD.open(currentFileName, FILE_APPEND);
    
    if (dataFile) {
      for (int i = 0; i < bufferIndex; i++) {
        dataFile.println(dataBuffer[i]);
      }
      dataFile.close();
    } else {
      // Detención de seguridad por extracción o corrupción de memoria SD
      sd_ok = false; 
      isLogging = false;
    }
    
    bufferIndex = 0; 
  }
}

// ==========================================
// BUCLE PRINCIPAL (LOOP)
// ==========================================
void loop() {
  distance = Pos * cm_per_pulse; 
  unsigned long currentMillis = millis();

  // Procesamiento de comandos entrantes por Serial
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n'); 
    cmd.trim(); 

    if (cmd == "START") {
      Pos = 0; 
      isLogging = true;
      bufferIndex = 0;
      startTime = millis(); 
      lastRecordedPos = -999999;
      
      if (sd_ok) {
        DateTime now = rtc.now();
        currentFileName = "/log_" + String(now.month()) + String(now.day()) + "_" + String(now.hour()) + String(now.minute()) + ".csv";
        dataFile = SD.open(currentFileName, FILE_WRITE);
        if (dataFile) {
          dataFile.println("Tiempo(s),Distancia,Pulsos");
          dataFile.close();
        } else {
          sd_ok = false;
        }
      }
      Serial.println("ACK_START"); 
    } 
    else if (cmd == "STOP") {
      isLogging = false;
      guardarBufferEnSD(); 
      Serial.println("ACK_STOP");
    }
    else if (cmd == "RESET") {
      Pos = 0;
      Serial.println("ACK_RESET");
    }
    else if (cmd.startsWith("CALIB:")) {
      diametro_polea_cm = cmd.substring(6).toFloat();
      recalcularFactor();
      Serial.println("ACK_CALIB");
    }
  }

  // Ciclo de muestreo y actualización de estado
  if (currentMillis - lastMsgTime >= samplingInterval) {
    lastMsgTime = currentMillis;

    // Transmisión de datos por Serial para la interfaz gráfica
    Serial.print(distance, 2); 
    Serial.print(",");
    Serial.println(Pos);

    // Almacenamiento en Buffer (solo si hay variación de posición)
    if (isLogging && sd_ok && (Pos != lastRecordedPos)) {
      float elapsedTime = (millis() - startTime) / 1000.0;
      
      String dataLine = String(elapsedTime, 2) + "," + String(distance * unitMultiplier, 2) + "," + String(Pos);
      
      dataBuffer[bufferIndex] = dataLine;
      bufferIndex++;
      
      lastRecordedPos = Pos;

      if (bufferIndex >= BUFFER_SIZE) {
        guardarBufferEnSD();
      }
    }

    // Actualización de Pantalla OLED
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0,0);
    
    if(isLogging && sd_ok) {
      display.print("GRABANDO EN SD...");
    } else if (isLogging && !sd_ok) {
      display.print("ERR: NO SD (Solo PC)");
    } else {
      display.print("LISTO. Polea:");
      display.print(diametro_polea_cm, 2);
    }
    
    display.setTextSize(2);
    display.setCursor(0, 16);
    display.print(distance * unitMultiplier, 2); 
    display.print(" ");
    display.print(currentUnit);
    display.display();
  }
}