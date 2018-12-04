import arduino

my_arduino = arduino.Client('http://192.168.1.112/')

print('Welcome to SmartHouseController')
while True:
    command = input('Please input your command: ')
    if command == 'l':
        print('[r] Read value')
        print('[w] Write value')
        print('[q] Exit program')
        print('[l] List of commands')
    elif command == 'r':
        vars = my_arduino.get_all()
        i = 0
        for var in sorted(vars):
            i += 1
            print('[%d] %s (%.2f)' % (i, var, vars[var]))
    elif command == 'w':
        vars = my_arduino.get_all()
        i = 0
        for var in sorted(vars):
            i += 1
            print('[%d] %s (%.2f)' % (i, var, vars[var]))
        id = input('Which variable do you want to write? ')
        if id == 0:
            print(my_arduino.get_all())
        else:
            new_value = input('What value do you want to write? ')
            my_arduino.set_value(list(vars)[int(id)-1],new_value)
    elif command == 'q':
        break;
    else:
        print('Command unknown. Type [l] for a list of commands.')