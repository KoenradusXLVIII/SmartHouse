# Public imports
import logging
import os
from datetime import datetime

def init_log(log_title):
    """ Initialize log file with provided title and optional COM port """
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_path = os.path.dirname(os.path.realpath(__file__))
    log_path = os.path.join(script_path, 'logs')
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    logfileName = '%s_%s.log' % (now, log_title)
    logging.basicConfig(filename=os.path.join(script_path, 'logs', logfileName), filemode='w',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    talk_log('Start of log \'%s\'' % os.path.join(script_path, 'logs', logfileName))

def talk_log(msg, SNR='', level='info', verbose=True):
    """ Function to write to log and to screen simultaneously """
    if SNR:
        SNR = '[%s] ' % SNR
    if verbose:
        print('%s%s' % (SNR, msg))
    if level == 'info':
        logging.info('%s%s' % (SNR, msg))
    elif level == 'warning':
        logging.warning('%s%s' % (SNR, msg))
    logger = logging.getLogger()
    logger.handlers[0].flush()