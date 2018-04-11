import re
from PyCRC.CRC16 import CRC16

def read_telegram(ser, logger, port):
    # Smart meter configuration
    serial_number = 'XMX5LGBBFG1009050373'
    eot_char = '!' # End of transmission character
    CRC_length = 4 # 4 byte hexadecimal CRC16 value
    telegram_length = 23 # lines
    OBIS = [
        ['Energy import [low]', '1-0:1.8.1','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
        ['Energy import [high]', '1-0:1.8.2','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
        ['Energy export [low]', '1-0:2.8.1','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
        ['Energy export [high]', '1-0:2.8.2','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)']
    ]

    # Initialize local variables
    itt = 0
    CRC_data = ''
    data = []

    # Start receiving raw data
    try:
        data_raw = str(ser.readline())
    except:
        logger.error('Unable to read from serial port: %s' % port)
        sys.exit()

    while (serial_number not in data_raw):
        try:
            data_raw = str(ser.readline())
        except:
            logger.error('Unable to read from serial port: %s' % port)
            sys.exit()
        itt += 1
        if (itt >= telegram_length):
            logger.warning('Invalid telegram')
            return -1

    # Start of transmission detected
    logger.info('Start of transmission detected')
    data.append(data_raw.strip())
    logger.debug('Data received: %s' % data_raw.strip())
    CRC_data += data_raw

    # Read appropriate amount of lines
    while (data_raw.startswith(eot_char) == False):
        try:
            data_raw = str(ser.readline())
        except:
            logger.error('Unable to read from serial port: %s' % port)
            sys.exit()
        data.append(data_raw.strip())
        if (data_raw.startswith(eot_char)):
            logger.info('End of transmission detected')
        else:
            CRC_data += data_raw

    # Verify CRC
    CRC_rec = data[len(data)-1]
    CRC_data += '!'
    if(CRC_rec.startswith(eot_char)):
        CRC = "0x{:04x}".format(CRC16().calculate(CRC_data))
        CRC = CRC[2:].upper()
        CRC_rec = CRC_rec[1:] # Remove '!' for displayed CRC

        if (CRC == CRC_rec):
            logger.info('Valid data, CRC match: 0x%s' % CRC)

            # Parse data and compute net energy usage
            energy = 0.0
            for line in range (1,len(data)):
                for desc, ref, regex in OBIS:
                    if(data[line].startswith(ref)):
                        m = re.search(regex,data[line])
                        logger.debug('%s: %s' % (desc,m.group(3)))
                        if(data[line].startswith('1-0:1.')):
                            energy += float(m.group(3))
                        else:
                            energy -= float(m.group(3))

            # Return energy value [Wh]
            energy *= 1000
            logger.info('Valid energy value received: %f Wh' % energy)
            return int(energy)
        else:
            # Message incorrect, CRC mismatch
            logger.warning('CRC mismatch: 0x%s / 0x%s' % (CRC,CRC_rec))
            return -1
