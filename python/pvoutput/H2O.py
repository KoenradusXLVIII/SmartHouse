
def diff(cur):
    # Read old value from data file
    try:
        fp = open('H2O.dat','r')
        old = int(fp.read())
        fp.close()
    except:
        old = 0

    # Compute difference
    diff = cur - old
    if (diff < 0):
        # Catch any Arduino reset
        diff = 0

    # Write new data to data file
    fp = open('H2O.dat', 'w')
    fp.write(str(cur))
    fp.close

    # Return difference
    return diff
