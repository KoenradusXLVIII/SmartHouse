import pickle
import os


def diff(value, name):
    # Parse input
    if value < 0:
        raise ValueError
    if not value == float(value):
        raise ValueError
    if not name:
        raise NameError

    # Read previous value from data file
    path = os.path.dirname(os.path.realpath(__file__))
    filename = path + '/' + name + '.pickle'
    try:
        with open(filename, 'rb') as fp:
            prev_value = pickle.load(fp)
    except IOError:
        prev_value = 0

    # Compute difference
    diff_value = value - prev_value
    if diff_value < 0:
        # Catch unexpected negative difference
        diff_value = 0

    # Write new data to data file
    with open(filename, 'wb') as fp:
        pickle.dump(value, fp)

    # Return differenceW
    return diff_value


'''
if __name__ == "__main__":
    # Testing
    path = os.path.dirname(os.path.realpath(__file__))
    filename = path + '\\' + 'test' + '.pickle'
    with open(filename, 'rb') as fp:
        prev_value = pickle.load(fp)

    test_value = 10
    new_value = prev_value + test_value
    print('Expected output: %d' % (test_value))
    output = diff(new_value,'test')
    print('Actual value: %d' % (output))
    if output == test_value:
        print('Test SUCCES')
    else:
        print('Test FAILED')
'''