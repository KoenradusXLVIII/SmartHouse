class OutOfRangeError(Exception): pass
class NotIntegerError(Exception): pass
class InvalidFilename(Exception): pass

def diff(cur, name):
    # Parse input
    if cur < 0:
        raise OutOfRangeError
    if not cur == int(cur):
        raise NotIntegerError
    if not name:
        raise InvalidFilename

	# TODO: PICKLE THIS
    # Read old value from data file
    try:
        fp = open(name + '.dat','r')
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
    fp = open(name + '.dat', 'w')
    fp.write(str(cur))
    fp.close

    # Return difference
    return diff
