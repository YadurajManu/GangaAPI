/*
 * ESP32-CAM Image Upload to Render.com
 * 
 * This code captures images from the ESP32-CAM and sends them to your deployed API
 * 
 * Hardware: ESP32-CAM
 * Libraries: WiFi, HTTPClient, camera
 * 
 * Setup:
 * 1. Install ESP32 board in Arduino IDE
 * 2. Install required libraries
 * 3. Update WiFi credentials and server URL
 * 4. Upload to ESP32-CAM
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi credentials - UPDATE THESE
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server configuration - UPDATE WITH YOUR RENDER URL
const char* serverURL = "https://gangaapi.onrender.com/upload";
// Replace with your actual Render URL

// Camera configuration
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// Upload settings
const int uploadInterval = 60000; // Upload every 60 seconds (60000ms)
const int maxRetries = 3;
const int retryDelay = 2000; // 2 seconds

// Image settings
const int imageQuality = 10; // 0-63, lower = better quality
const int imageWidth = 800;
const int imageHeight = 600;

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32-CAM Image Uploader Starting...");
  
  // Initialize camera
  if (!initCamera()) {
    Serial.println("Camera initialization failed!");
    while (true) {
      delay(1000);
    }
  }
  
  // Connect to WiFi
  connectToWiFi();
  
  Serial.println("Setup complete. Starting image capture loop...");
}

void loop() {
  // Capture and upload image
  captureAndUploadImage();
  
  // Wait before next capture
  delay(uploadInterval);
}

bool initCamera() {
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
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Frame size and quality
  if (psramFound()) {
    config.frame_size = FRAMESIZE_SVGA; // 800x600
    config.jpeg_quality = imageQuality;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_VGA; // 640x480
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return false;
  }
  
  Serial.println("Camera initialized successfully");
  return true;
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    while (true) {
      delay(1000);
    }
  }
}

void captureAndUploadImage() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    connectToWiFi();
    return;
  }
  
  // Capture image
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }
  
  Serial.printf("Captured image: %dx%d, %d bytes\n", fb->width, fb->height, fb->len);
  
  // Upload image
  bool uploadSuccess = uploadImage(fb->buf, fb->len);
  
  // Release frame buffer
  esp_camera_fb_return(fb);
  
  if (uploadSuccess) {
    Serial.println("Image uploaded successfully!");
  } else {
    Serial.println("Image upload failed!");
  }
}

bool uploadImage(uint8_t* imageData, size_t imageSize) {
  HTTPClient http;
  
  // Prepare multipart form data
  String boundary = "----WebKitFormBoundary" + String(random(0xffffffff), HEX);
  
  http.begin(serverURL);
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
  
  // Create multipart body
  String body = "";
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"file\"; filename=\"esp32_cam_" + String(millis()) + ".jpg\"\r\n";
  body += "Content-Type: image/jpeg\r\n\r\n";
  
  String bodyEnd = "\r\n--" + boundary + "\r\n";
  bodyEnd += "Content-Disposition: form-data; name=\"description\"\r\n\r\n";
  bodyEnd += "ESP32-CAM Image " + String(millis()) + "\r\n";
  bodyEnd += "--" + boundary + "\r\n";
  bodyEnd += "Content-Disposition: form-data; name=\"location\"\r\n\r\n";
  bodyEnd += "ESP32-CAM Location\r\n";
  bodyEnd += "--" + boundary + "--\r\n";
  
  // Send request
  int httpResponseCode = http.POST((uint8_t*)body.c_str(), body.length(), imageData, imageSize, (uint8_t*)bodyEnd.c_str(), bodyEnd.length());
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("HTTP Response Code: %d\n", httpResponseCode);
    Serial.printf("Response: %s\n", response.c_str());
    
    if (httpResponseCode == 200) {
      // Parse JSON response
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, response);
      
      if (doc["message"] == "Image uploaded successfully") {
        Serial.printf("Image ID: %d\n", doc["image_id"].as<int>());
        return true;
      }
    }
  } else {
    Serial.printf("HTTP Error: %s\n", http.errorToString(httpResponseCode).c_str());
  }
  
  http.end();
  return false;
}

// Alternative simple upload function
bool uploadImageSimple(uint8_t* imageData, size_t imageSize) {
  HTTPClient http;
  
  http.begin(serverURL);
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("Content-Length", String(imageSize));
  
  int httpResponseCode = http.POST(imageData, imageSize);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("HTTP Response Code: %d\n", httpResponseCode);
    Serial.printf("Response: %s\n", response.c_str());
    
    if (httpResponseCode == 200) {
      return true;
    }
  } else {
    Serial.printf("HTTP Error: %s\n", http.errorToString(httpResponseCode).c_str());
  }
  
  http.end();
  return false;
}
