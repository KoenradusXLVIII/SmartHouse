//
// WiFi functions
//

char ssid[MAX_WIFI_LENGTH];
char pass[MAX_WIFI_LENGTH];

// Connect to WiFi network
bool setup_WiFi() {
  int i = 0;
  
  // Report SSID
  Serial.print(F("Connecting to: "));
  Serial.print(ssid);
  Serial.print(F(" "));

  // Connect to WiFi network
  WiFi.mode(WIFI_STA);
  //WiFi.config(ip, gateway, subnet, dns);
  WiFi.begin(ssid, pass);
  
  while ((WiFi.status() != WL_CONNECTED) and (i < MAX_WIFI_WAITS)) {
    delay(WIFI_WAIT);
    Serial.print(F("."));
    i++;
  }

  if (WiFi.status() != WL_CONNECTED)
    return false;

  // Report the IP address
  Serial.println(F(""));
  Serial.print(F("IP Address: "));
  Serial.println(WiFi.localIP());
  Serial.print(F("MAC: "));
  Serial.println(WiFi.macAddress());

  return true;
}

void init_WiFi()
{
  // Read SSID/pass from EEPROM
  char data[MAX_WIFI_LENGTH];
  read_EEPROM(1, data);
  strcpy(ssid, data);
  read_EEPROM(1 + MAX_WIFI_LENGTH, data);
  strcpy(pass, data);

  // Actively disconnect from any connected WiFi
  WiFi.disconnect();
  delay(100);
  
  if (setup_WiFi()) 
  {
    // Toggle valid WiFi data bit in EEPROM
    EEPROM.write(0, 'W');
    EEPROM.commit();  
      
    // Connect MQTT client
    mqtt_client.setServer(broker, port);
    
    // Update blink interval
    blink.set_interval(BLINK_CONFIGURED);
    
    // Report success to Python
    Serial.println(F("OK"));  
  } else {
    // Report error to Python
    Serial.println(F("E1: Unable to establish WiFi connection"));
  }
}

char* get_ssid()
{
  return ssid;
}


char* get_pass()
{
  return pass;
}
