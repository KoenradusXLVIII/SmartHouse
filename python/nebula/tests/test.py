import nebula

nebula_client = nebula.Client('http://www.joostverberk.nl')
nebula_client.set_meas(3, 19.99)
meas = nebula_client.get_meas()
for item in meas:
    print('%s: %.2f [%s]' % (item['quantity'], float(item['value']), item['uom']))

