//
// Serial communcation functions
//

void listen_serial(void)
{
  char c;
  while(Serial.available())
  {
    c = Serial.read();
    if (c != '\n')
    {
      // Add to buffer
      serial_buf[sp++] = c; 
    } else {
      // EOL character received, process command
      serial_buf[sp] = '\0';
      process_serial();
      reset_serial_buffer();
    } 
  }
}

void process_serial()
{
  if (strcmp(serial_buf, (char*) F("list_ssid")) == 0)
    list_SSID();
  else if (strcmp(serial_buf, (char*) F("set_ssid")) == 0)
    store_WiFi(1);
  else if (strcmp(serial_buf, (char*) F("set_pass")) == 0)
    store_WiFi(1 + MAX_WIFI_LENGTH);
  else if (strcmp(serial_buf, (char*) F("init_wifi")) == 0)
    init_WiFi();
  else if (strcmp(serial_buf, (char*) F("reset")) == 0)
    EEPROM_reset();
  else if (strcmp(serial_buf, (char*) F("get_uuid")) == 0)
    Serial.println(get_uuid());
  else if (strcmp(serial_buf, (char*) F("get_ssid")) == 0)
    Serial.println(get_ssid());
  else if (strcmp(serial_buf, (char*) F("get_wifi_status")) == 0)
    Serial.println(WiFi.status());
  else if (strcmp(serial_buf, (char*) F("get_ip")) == 0)
    Serial.println(WiFi.localIP());
  else
    Serial.println(F("E0: Unknown command"));
}

void reset_serial_buffer(void)
{
  sp = 0;
  for(int i=0; i<SERIAL_BUF_LENGTH; i++)
  { // Initialize serial buffer
    serial_buf[i] = '\0';
  }
}

void list_SSID() 
{
  int numberOfNetworks = WiFi.scanNetworks();
  Serial.print(F("{"));
  for(int i =0; i<numberOfNetworks; i++)
  {
    Serial.print(F("\""));
    Serial.print(WiFi.SSID(i));
    Serial.print(F("\":\""));
    Serial.print(WiFi.RSSI(i));
    Serial.print(F("\""));
    if (i < numberOfNetworks - 1) 
      Serial.print(F(","));
  }
  Serial.println(F("}"));
}

void store_WiFi(int loc)
{
  Serial.println(F("OK"));
  char c;
  while (!Serial.available()) 
  { // Wait for SSID data to arrive
  }

  reset_serial_buffer();
  while (Serial.available())
  {
    c = Serial.read();
    // Serial.print(c);
    if (c != '\n')
    {
      // Add to buffer
      serial_buf[sp++] = c; 
    } else {
      // EOL character received, process command
      write_EEPROM(loc, sp, serial_buf);
      // Report success to Python
      Serial.println(serial_buf);
      // Reset serial buffer
      reset_serial_buffer();
    } 
    // Wait for next character
    delay(1);
  } 
}

void EEPROM_reset(void)
{
  for (int i = 0 ; i < EEPROM.length() ; i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
  EEPROM_initialized = false;

  // Disconnect WiFi
  WiFi.disconnect();

  // Set blink to unconfigured
  blink.set_interval(BLINK_UNCONFIGURED);

  // Report to Python
  Serial.println(F("OK"));
}
