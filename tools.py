"""tools for atc daemon"""
import os
import time
import logging
from socket import socket, AF_INET, SOCK_STREAM, error as SocketError
import re
from datetime import date

try:
    from config import BUFF_SIZE
except ImportError:
    BUFF_SIZE = 4096
try:
    from config import PATH_FILES
except ImportError:
    PATH_FILES = '/tmp/'
try:
    from config import PID_FILE
except ImportError:
    PID_FILE = '/tmp/atc_daemon.pid'


def create_conf():
    """create default config.py file"""
    with open('config.py', 'w') as fd:
        fd.write("BUFF_SIZE = 4096\n")
        fd.write("PATH_FILES = '/tmp/'\n")
        fd.write("SRV_ADDR = '127.0.0.1'\n")
        fd.write("SRV_PORT = 5100\n")
        fd.write("LOG_FILE = '/tmp/logfile.log'\n")
        fd.write("PID_FILE = '/tmp/atc_daemon.pid'\n")


def check_conf():
    """check elements in config.py"""
    try:
        from config import BUFF_SIZE as par1
        from config import PATH_FILES as par2
        from config import SRV_ADDR as par3
        from config import SRV_PORT as par4
        from config import LOG_FILE as par5
        from config import PID_FILE as par6
        del (par1, par2, par3, par4, par5, par6)
    except ImportError:
        create_conf()


def check_pid(pidfile):
    result = False
    if os.path.exists(pidfile):
        with open(pidfile, 'r') as fd:
            pid = int(fd.read().strip())
            if pid == os.getpid():
                result = True
        if not result:
            os.remove(pidfile)
    return result


def save_buff(buff, loger):
    """save buff in file"""
    umask_original = os.umask(0)
    for line in buff.split('\n'):
        filename = 'other' + str(date.today().day)
        try:
            if re.search('\w{3}/', line):
                # for pass in line 'SMDR REPORT FOR [ ] Sep/05/2016 10:20'
                raise AttributeError
            date_line = re.search('(\d{2})/(\d{2})', line).group()
            date_line = '_'.join(date_line.split('/'))
            time_line = re.search('(\d{2}):', line).group().split(':')[0]
            filename = '%s_%s' % (date_line, time_line)
        except AttributeError as atrEr:
            loger.debug('%s' % (atrEr,))
        filename = PATH_FILES + filename + '.atc'
        try:
            with open(filename, 'a+') as fd:
                fd.write((line + '\n').encode('utf8'))
                os.chmod(filename, 0o666)
        except IOError as ioEr:
            loger.error('%s: %d (%s)\n' % (filename, ioEr.errno, ioEr.strerror))
        except OSError as osEr:
            loger.error('%s: %d (%s)\n' % (filename, osEr.errno, osEr.strerror))
    os.umask(umask_original)


def read_buff(srv_addr, srv_port, loger):
    """read buff from server"""
    step = 0
    running = True
    while running:
        sock = None
        step += 1
        loger.info('step: %d' % (step,))
        try:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((srv_addr, srv_port))
            loger.info('connected on %s:%d' % (srv_addr, srv_port))
        except SocketError as sockEr:  # when cant connect to server
            loger.error('%s: Not connected on %s:%d' % (sockEr, srv_addr, srv_port))
            time.sleep(10)
            sock.close()
            continue

        buff = ''
        data_tmp = b''
        while running:
            if not check_pid(PID_FILE):
                loger.info('not found %s or other pid in %s' % (PID_FILE, PID_FILE))
                running = False

            data = sock.recv(BUFF_SIZE)
            if len(data) == 0:  # if connect lost
                loger.error('len = 0 reconect')
                time.sleep(10)
                sock.close()
                break
            try:
                data = data_tmp + data
                data = data.decode('iso8859_5')
                data_tmp = b''
            except UnicodeDecodeError:
                data_tmp = data
                continue
            buff += data
            end_line = buff.rfind('\n')
            if end_line != -1:
                end_line += 1  # for get '\n' into line
                save_buff(buff[:end_line], loger)
                buff = buff[end_line:]


def conf_log(logfile='/tmp/atcreadd.log'):
    """config logging"""
    loger = logging.getLogger(__name__)
    loger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(message)s')

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)

    file_handle = logging.FileHandler(logfile)
    file_handle.setLevel(logging.INFO)
    file_handle.setFormatter(formatter)

    loger.addHandler(console)
    loger.addHandler(file_handle)

    umask_original = os.umask(0)
    try:
        os.chmod(logfile, 0o666)
    except OSError as osEr:
        loger.error('%s: %d (%s)\n' % (logfile, osEr.errno, osEr.strerror))
    os.umask(umask_original)

    return loger


def test_log(loger):
    """test func fro log"""
    loger.debug('from debug level')
    loger.info('from info level')
    loger.warning('from warning level')
    loger.error('from error level')
    loger.critical('from critical level')
