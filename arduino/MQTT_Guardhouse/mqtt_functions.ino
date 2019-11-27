//
// MQTT functions
//

// MQTT configuration

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
  sscanf(topic, "%*s %*s %s %*s", charTopicType);

  // Handle different topic types
  if (strcmp(charTopicType, "io") == 0)
  {
    int intSensorID;
    int intValue;
    sscanf(topic, "%*s %*s %*s %d", &intSensorID);  
    sscanf(charPayload, "%d", &intValue);
    Serial.print(F("Received IO message for: "));
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
}

void mqtt_subscribe(void)
{
    char charTopicSub[TOPIC_LENGTH];

    // Subscribe to my IO topic
    strcpy(charTopicSub, "nodes/");
    strcat(charTopicSub, UUID);
    strcat(charTopicSub, "/io/+");
    mqtt_client.subscribe(charTopicSub);
}

// Reconnect to client
void mqtt_reconnect() {
  // Loop until we're reconnected
  while (!mqtt_client.connected()) {
    Serial.print(F("Attempting MQTT connection..."));
    // Attempt to connect
    if (mqtt_client.connect(UUID, MQTT_USER, MQTT_API_KEY)) {
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

void mqtt_topic(char* topic, int io_id, char* pub_topic) {
    char charID[MAX_LENGTH_SIGNED_INT];
    strcpy(pub_topic, "nodes/");
    strcat(pub_topic, UUID);
    if (strcmp(topic, "") == 0)
      strcat(pub_topic, "/sensors/");
    else
      strcat(pub_topic, topic);
    if (strcmp(topic, "") == 0)
    {
      itoa(io_id, charID, 10);
      strcat(pub_topic, charID);
    }
}

void mqtt_publish(int io_id, float value, int timer_id, char* topic, int interval) {
  unsigned long longNow = millis();
  
  if (longNow - longPrevious[timer_id] >= (interval*60000)) {
    // Reset ticker
    longPrevious[timer_id] = longNow;
    
    // MQTT client connection
    if (!mqtt_client.connected())  // Reconnect if connection is lost
      mqtt_reconnect();
  
    // Prepare topic
    char pub_topic[TOPIC_LENGTH];
    mqtt_topic(topic, io_id, pub_topic);

    // Prepare value
    char charValue[6];
    dtostrf(value, 1, 2, charValue);

    // Publish
    Serial.print(F("MQTT upload on topic: "));
    Serial.print(pub_topic);
    Serial.print(F(" => "));
    Serial.println(charValue);
    mqtt_client.publish(pub_topic, charValue, true);
  }
}

void mqtt_publish(int io_id, float value) {
  // Publish float with io_id, without timer_id and interval
  mqtt_publish(io_id, value, 0, "", 0);
}

void mqtt_publish(int io_id, float value, int timer_id, int interval) {
  // Publish float with io_id, timer_id and interval
  mqtt_publish(io_id, value, timer_id, "", interval);
}

void mqtt_publish(int io_id, int value) {
  // Publish int with io_id, without timer_id and interval
  mqtt_publish(io_id, value, 0, "", 0);
}

void mqtt_publish(int io_id, int value, int timer_id, int interval) {
  // Publish int with io_id, timer_id and interval
  mqtt_publish(io_id, (float) value, timer_id, "", interval);
}

void mqtt_publish(int value, int timer_id, char* topic, int interval) {
  // Publish integer to topic with timer_id and interval
  mqtt_publish(0, (float) value, timer_id, topic, interval);
}
