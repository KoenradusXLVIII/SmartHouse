//
// MQTT functions
//

// MQTT callback triggered on message received
void callback(char* topic, byte* payload, unsigned int length) {
  int intValue;
  char charPayload[length];

  for (int i = 0; i < length; i++)
    charPayload[i] = (char)payload[i];

  sscanf(charPayload, "%d", &intValue);
  Serial.print("Received message on topic: ");
  Serial.print(topic);
  Serial.print(" => ");
  Serial.println(intValue);
  process_cmd(sensor_id(topic), intValue);
}

// Control IO based on MQTT command
void process_cmd(int intSensorID, int intValue) {
  for (int i = 0; i < IO_COUNT; i++) {
    if (IO_ID[i] == intSensorID)
      digitalWrite(IO_pin[i], intValue);
  }
}

// Extract sensor ID from topic
int sensor_id(char* topic) {
  int intSensorID;

  for (int i = 0; i < strlen(topic); i++ )
    if (topic[i] == '/')
      topic[i] = ' ';

  sscanf(topic, "%*s %*s %*s %d", &intSensorID);

  return intSensorID;
}

// Reconnect to client
void mqtt_reconnect() {
  // Loop until we're reconnected
  while (!mqtt_client.connected()) {
    Serial.print(F("Attempting MQTT connection..."));
    // Attempt to connect
    if (mqtt_client.connect(node_uuid, MQTT_USER, MQTT_API_KEY)) {
      Serial.println(F("connected"));
      // Resubscribe to topic after disconnect
      mqtt_client.subscribe(charTopic);
    } else {
      Serial.println(F(" try again in 5 seconds"));
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void mqtt_publish(int id, float value, int interval) {
  unsigned long longNow = millis();
  
  if (longNow - longPrevious >= (interval*60000)) {
    // Reset ticker
    longPrevious = longNow;
    
    // MQTT client connection
    if (!mqtt_client.connected())  // Reconnect if connection is lost
      mqtt_reconnect();
  
    // Publish value
    char charTopic[TOPIC_LENGTH];
    char charID[MAX_LENGTH_SIGNED_INT];
    char charValue[6];
    strcpy(charTopic, (const char *) F("nodes/"));
    strcat(charTopic, node_uuid);
    strcat(charTopic, (const char *) F("/sensors/"));
    itoa(id, charID, 10);
    strcat(charTopic, charID);
    dtostrf(value, 1, 2, charValue);
  
    Serial.print(F("MQTT upload on topic: "));
    Serial.print(charTopic);
    Serial.print(F(" => "));
    Serial.println(charValue);
    mqtt_client.publish(charTopic, charValue, true);
  }
}

void mqtt_publish(int id, float value) {
  // Publish float without interval
  mqtt_publish(id, value, 0);
}

void mqtt_publish(int id, int value, int interval) {
  // Publish int with interval
  mqtt_publish(id, (float) value, interval);
}

void mqtt_publish(int id, int value) {
  // Publish int without interval
  mqtt_publish(id, (float) value, 0);
}

void mqtt_rssi(void) {
    int rssi;
    
    np.add_to_buffer((int) WiFi.RSSI(), rssi_buf, BUF_LENGTH);
    rssi = np.filt_mean(rssi_buf, BUF_LENGTH, 1);  
  
    if (rssi != prev_rssi) 
    {
      // MQTT client connection
      if (!mqtt_client.connected())  // Reconnect if connection is lost
        mqtt_reconnect();
    
      // Publish value
      char charTopic[TOPIC_LENGTH];
      char charID[MAX_LENGTH_SIGNED_INT];
      char charValue[6];
      strcpy(charTopic, (const char *) F("nodes/"));
      strcat(charTopic, node_uuid);
      strcat(charTopic, (const char *) F("/rssi"));
      dtostrf(rssi, 1, 2, charValue);
    
      Serial.print(F("MQTT upload on topic: "));
      Serial.print(charTopic);
      Serial.print(F(" => "));
      Serial.println(charValue);
      mqtt_client.publish(charTopic, charValue, true);  
    }
}
