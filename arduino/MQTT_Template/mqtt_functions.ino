//
// MQTT functions
//

// MQTT configuration
char node_uuid[UUID_LENGTH];
int rssi_buf[BUF_LENGTH];

// MQTT callback triggered on message received
void callback(char* topic, byte* payload, unsigned int length) {
  char charPayload[length];
  char charTopicType[TOPIC_LENGTH];

  // Convert payload to character array
  for (int i = 0; i < length; i++)
    charPayload[i] = (char)payload[i];

  // Parse incoming to handle /
  for (int i = 0; i < strlen(topic); i++ )
    if (topic[i] == '/')
      topic[i] = ' ';

  // Extract topic type
  sscanf(topic, "%*s %*s %*s %s %*s", charTopicType);

  // Handle different topic types
  if (strcmp(charTopicType, (char*) F("io")) == 0)
  {
    int intSensorID;
    int intValue;
    sscanf(topic, "%*s %*s %*s %*s %d", intSensorID);  
    sscanf(charPayload, "%d", intValue);
    Serial.print(F("Received IO message for :"));
    Serial.print(intSensorID);
    Serial.print(F(" => "));
    Serial.println(intValue);    
    for (int i = 0; i < IO_COUNT; i++) 
    {
      if (IO_ID[i] == intSensorID)
      {
        digitalWrite(IO_pin[i], intValue);
        break;
      }
    }
  }
  else if (strcmp(charTopicType, (char*) F("update")) == 0)
  {
    char charBinID[OTA_BIN_FILE_LENGTH+1];
    sscanf(charPayload, "%s", charBinID);
    charBinID[OTA_BIN_FILE_LENGTH] = '\0';
    if (strcmp(charBinID, OTA_VERSION) != 0)
      update_OTA(charBinID);
  }
}

void set_uuid(void)
{
  int len = 6;
  byte mac[len];
  WiFi.macAddress(mac);
  for (unsigned int i = 0; i < len; i++)
    {
        byte nib1 = (mac[i] >> 4) & 0x0F;
        byte nib2 = (mac[i] >> 0) & 0x0F;
        node_uuid[i*2+0] = nib1  < 0xA ? '0' + nib1  : 'A' + nib1  - 0xA;
        node_uuid[i*2+1] = nib2  < 0xA ? '0' + nib2  : 'A' + nib2  - 0xA;
    }
  node_uuid[len*2] = '\0';
}

char* get_uuid()
{
  return node_uuid;
}

void mqtt_subscribe(void)
{
    char charTopicSub[TOPIC_LENGTH];

    // Subscribe to my IO topic
    strcpy(charTopicSub, "nodes/");
    strcat(charTopicPub, (const char *) MQTT_USER);
    strcat(charTopicPub, (const char *) F("/"));
    strcat(charTopicSub, node_uuid);
    strcat(charTopicSub, "/io/+");
    mqtt_client.subscribe(charTopicSub);

    // Subscribe to my update topic
    strcpy(charTopicSub, "nodes/");
    strcat(charTopicPub, (const char *) MQTT_USER);
    strcat(charTopicPub, (const char *) F("/"));
    strcat(charTopicSub, node_uuid);
    strcat(charTopicSub, "/update");
    mqtt_client.subscribe(charTopicSub);
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
      mqtt_subscribe();
    } else {
      Serial.println(F(" try again in 5 seconds"));
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void mqtt_publish(int sensor_id, float value, int io_id, char* topic, int interval) {
  unsigned long longNow = millis();
  
  if (longNow - longPrevious[io_id] >= (interval*60000)) {
    // Reset ticker
    longPrevious[io_id] = longNow;
    
    // MQTT client connection
    if (!mqtt_client.connected())  // Reconnect if connection is lost
      mqtt_reconnect();
  
    // Prepare topic
    char charTopicPub[TOPIC_LENGTH];
    char charID[MAX_LENGTH_SIGNED_INT];
    char charValue[6];
    strcpy(charTopicPub, (const char *) F("nodes/"));
    strcat(charTopicPub, (const char *) MQTT_USER);
    strcat(charTopicPub, (const char *) F("/"));
    strcat(charTopicPub, node_uuid);
    if (strcmp(topic, "") == 0)
      strcat(charTopicPub, (const char *) F("/sensors/"));
    else
      strcat(charTopicPub, topic);
    if (strcmp(topic, "") == 0)
    {
      itoa(sensor_id, charID, 10);
      strcat(charTopicPub, charID);
    }
    dtostrf(value, 1, 2, charValue);
  
    Serial.print(F("MQTT upload on topic: "));
    Serial.print(charTopicPub);
    Serial.print(F(" => "));
    Serial.println(charValue);
    mqtt_client.publish(charTopicPub, charValue, true);
  }
}

void mqtt_publish(int io_id, float value, int interval) {
  // Publish float with io_id and interval, without io_pin
  mqtt_publish(io_id, value, 0, "", interval);
}

void mqtt_publish(int io_id, float value) {
  // Publish float with io_id, without id_pin and interval
  mqtt_publish(io_id, value, 0, "", 0);
}

void mqtt_publish(int io_id, int value, int io_pin) {
  // Publish int with io_id and io_pin, without interval
  mqtt_publish(io_id, (float) value, io_pin, "", 0);
}

void mqtt_publish(int io_id, int value, int io_pin, int interval) {
  // Publish int with io_id, io_pin and interval
  mqtt_publish(io_id, (float) value, io_pin, "", interval);
}

void mqtt_publish(int value, int counter_id, char* topic, int interval) {
  // Publish integer with counter_id to topic with interval
  mqtt_publish(0, (float) value, counter_id, topic, interval);
}

void mqtt_rssi(bool timed) {
    int rssi;
    char* topic = "/rssi";
    
    np.add_to_buffer((int) WiFi.RSSI(), rssi_buf, BUF_LENGTH);
    rssi = np.filt_mean(rssi_buf, BUF_LENGTH, 1);  
    if (timed)
      mqtt_publish(rssi, IO_COUNT, topic, 1);   // Publish RSSI to last IO position
    else
      mqtt_publish(rssi, IO_COUNT, topic, 0);   // Publish RSSI to last IO position
}
