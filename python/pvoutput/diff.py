import pickle
import os
import time


def dxdt(x1, name):
    # Parse input
    if x1 < 0:
        raise ValueError
    if not x1 == float(x1):
        raise ValueError
    if not name:
        raise NameError

    t1 = time.time()

    # Read previous value from data file
    path = os.path.dirname(os.path.realpath(__file__))
    filename = path + '/' + name + '.pickle'
    try:
        with open(filename, 'rb') as fp:
            [x2, t2] = pickle.load(fp)
    except FileNotFoundError:
        [x2, t2] = [0,0]

    # Compute difference
    dx = x1 - x2
    dt = t1 - t2       # dt in seconds
    dxdt = dx/dt

    # Write new data to data file
    with open(filename, 'wb') as fp:
        pickle.dump([x1, t1], fp)

    # Return difference
    return dxdt

def dx(x1, name):
    # Parse input
    if x1 < 0:
        raise ValueError
    if not x1 == float(x1):
        raise ValueError
    if not name:
        raise NameError

    # Read previous value from data file
    path = os.path.dirname(os.path.realpath(__file__))
    filename = path + '/' + name + '.pickle'
    try:
        with open(filename, 'rb') as fp:
            x2 = pickle.load(fp)
    except FileNotFoundError:
        x2 = 0

    # Compute difference
    dx = x1 - x2

    # Write new data to data file
    with open(filename, 'wb') as fp:
        pickle.dump(x1, fp)

    # Return difference
    return dx


if __name__ == "__main__":
    # Testing
    # Stage test data
    x1 = 10
    t1 = time.time()-10
    x2 = 350
    t2 = time.time()
    dx = x1 - x2
    dt = t1 - t2       # dt in seconds
    expected_result = dx/dt

    # Stage envirnoment
    path = os.path.dirname(os.path.realpath(__file__))
    filename = path + '\\' + 'test' + '.pickle'
    with open(filename, 'wb') as fp:
        pickle.dump([x1, t1], fp)

    # Run function
    print('Expected output: %.2f' % (expected_result))
    result = dxdt(x2,'test')
    print('Actual value: %.2f' % (result))
    if result > .95*expected_result and result < 1.05*expected_result:
        print('Test SUCCES')
    else:
        print('Test FAILED')
