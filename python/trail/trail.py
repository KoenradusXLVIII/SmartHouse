import time

f = open('/var/log/syslog', 'r')
while True:
    line = ''
    while len(line) == 0 or line[-1] != '\n':
        tail = f.readline()
        if tail == '':
            time.sleep(1)          # avoid busy waiting
            continue
        line += tail
    print(line)