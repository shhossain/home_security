#include "esp_camera.h"
#include <WiFi.h>
#include <WiFiManager.h>

#define CAMERA_MODEL_AI_THINKER // Has PSRAM

#define BUZZER_PIN 15
#define CONNECT_LED_PIN 14
#define SERVO_PIN 13
#define WIFI_RESET_BUTTON_PIN 12

#define LED_LEDC_GPIO 4

#define NUM_THREADS 4

#include "camera_pins.h"

bool isResetButtonPressed = false;

struct BroadcastParams
{
  int start;
  int end;
  String baseIP;
  String localIP;
};

void startCameraServer();
void setupLedFlash();
void setupBuzzer();
void setupServo();

WiFiManager wm;
void setup()
{

  Serial.begin(115200);
  pinMode(WIFI_RESET_BUTTON_PIN, INPUT);
  pinMode(CONNECT_LED_PIN, OUTPUT);

  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG; // for streaming
  // config.pixel_format = PIXFORMAT_RGB565; // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // if PSRAM IC present, init with UXGA resolution and higher JPEG quality
  //                      for larger pre-allocated frame buffer.
  if (config.pixel_format == PIXFORMAT_JPEG)
  {
    if (psramFound())
    {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    }
    else
    {
      // Limit the frame size when PSRAM is not available
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  }

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK)
  {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  // initial sensors are flipped vertically and colors are a bit saturated
  if (s->id.PID == OV3660_PID)
  {
    s->set_vflip(s, 1);       // flip it back
    s->set_brightness(s, 1);  // up the brightness just a bit
    s->set_saturation(s, -2); // lower the saturation
  }
  // drop down frame size for higher initial frame rate
  if (config.pixel_format == PIXFORMAT_JPEG)
  {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

  // WiFi.begin(ssid, password);
  // WiFi.setSleep(false);

  // custom parameters ip address for python face recognition server
  // WiFiManagerParameter custom_ip("server", "Server IP", "192.168.0.51:8000", 40);
  // wm.addParameter(&custom_ip);

  // set timeouit
  wm.setConnectTimeout(20);

  bool res = wm.autoConnect("Home Security Camera", "home@123");
  if (!res)
  {
    Serial.println("Failed to connect to WiFi, restarting in 3 seconds");
    delay(3000);
    ESP.restart();
  }

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  // Print MAC Address
  Serial.print("MAC Address: ");
  Serial.println(WiFi.macAddress());

  startCameraServer();
  setupBuzzer();
  setupLedFlash();
  setupServo();

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
}

void loop()
{

  if (WiFi.status() == WL_CONNECTED)
  {
    digitalWrite(CONNECT_LED_PIN, HIGH);
  }
  else
  {
    digitalWrite(CONNECT_LED_PIN, LOW);
  }

  if (digitalRead(WIFI_RESET_BUTTON_PIN) == HIGH)
  {
    Serial.println("Resetting WiFi");
    WiFi.disconnect();
    delay(1000);
    wm.resetSettings();
    ESP.restart();
  }

  delay(100);
}
