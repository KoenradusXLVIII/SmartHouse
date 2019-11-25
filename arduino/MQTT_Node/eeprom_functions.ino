//
// EEPROM functions
// 

bool check_EEPROM_init(void)
{
  char data[MAX_WIFI_LENGTH];
  char c = EEPROM.read(0);
  if (c == 'W') 
  {
    // Read data from EEPROM
    read_EEPROM(1, data);
    strcpy(get_ssid(), data);
    read_EEPROM(1 + MAX_WIFI_LENGTH, data);
    strcpy(get_pass(), data);
    return true;
  }
  else
    return false;
}

void write_EEPROM(int loc, int len, char* data)
{
  // Valid data key on first bit
  for (int i=0; i<len; i++)
    EEPROM.write(loc+i, data[i]);
  EEPROM.write(loc+len, '\0');
  EEPROM.commit();
}

void read_EEPROM(int loc, char* data)
{
  int i = 0;
  char c;
  // Valid data in EEPROM, read and return
  while(c != '\0')
  {
    c = EEPROM.read(loc+i);
    data[i++] = c;
  }
  data[i] = '\0'; 
}
