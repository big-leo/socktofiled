'''tools for atc daemon'''
import os
import sys
import time
import logging
from socket import socket, AF_INET, SOCK_STREAM, error as SocketError
import re
from datetime import date
try:
    from config import BUFF_SIZE
except ImportError:
    BUFF_SIZE = 1024
try:
    from config import PATH_FILES
except ImportError:
    PATH_FILES = '/tmp/'


def create_conf():
    '''create default config.py file'''
    with open('config.py', 'w') as fd:
        fd.write("BUFF_SIZE = 1024\n")
        fd.write("PATH_FILES = '/tmp/'\n")
        fd.write("SRV_ADDR = '127.0.0.1'\n")
        fd.write("SRV_PORT = 5100\n")
        fd.write("LOG_FILE = '/tmp/logfile.log'\n")


def check_conf():
    '''check elements in config.py'''
    try:
        from config import BUFF_SIZE as par1
        from config import PATH_FILES as par2
        from config import SRV_ADDR as par3
        from config import SRV_PORT as par4
        from config import LOG_FILE as par5
        del(par1, par2, par3, par4, par5)
    except ImportError:
        create_conf()


def save_buff(buff, loger):
    '''save buff in file'''
    for line in buff.split('\n'):
        file_head = 'other' + str(date.today().day)
        try:
            date_line = re.search('(\d{2})/(\d{2})', line).group()
            date_line = '_'.join(date_line.split('/'))
            time_line = re.search('(\d{2}):', line).group().split(':')[0]
            file_head = '%s_%s' % (date_line, time_line)
        except AttributeError as e:
            pass
            #loger.debug(e)
        #print(line)
        filename = PATH_FILES + file_head + '.atc'
        try:
            with open(filename, 'a+') as fd:
                fd.write((line + '\n').encode('utf8'))
        except IOError as e:
            loger.error('%s: %d (%s)\n' % (filename, e.errno, e.strerror))


def read_buff(srv_addr, srv_port, loger):
    '''read buff from server'''
    sock = socket(AF_INET, SOCK_STREAM)
    try:
        sock.connect((srv_addr, srv_port))
        loger.info('connected on %s:%d' % (srv_addr, srv_port))
    except SocketError as e: # when cant connect to server
        loger.error('%s: Not connected on %s:%d' % (e, srv_addr, srv_port))
        time.sleep(10)
        read_buff(srv_addr, srv_port, loger)

    buff = ''
    data_tmp = b''
    while True:
        data = sock.recv(BUFF_SIZE)
        if len(data) == 0: # if connect lost
            read_buff(srv_addr, srv_port, loger)
        try:
            data = data_tmp + data
            data = data.decode('utf8')
            data_tmp = b''
        except UnicodeDecodeError as e:
            data_tmp = data
            continue
        buff += data
        endline = buff.rfind('\n')
        if endline != -1:
            endline += 1 #for get '\n' into line
            save_buff(buff[:endline], loger)
            buff = buff[endline:]
        #print('after:\n', buff)


def conf_log(logfile='/tmp/atcreadd.log'):
    '''config logging'''
    loger = logging.getLogger(__name__)
    loger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(message)s')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    filehandler = logging.FileHandler(logfile)
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(formatter)

    loger.addHandler(console)
    loger.addHandler(filehandler)

    return loger


def test_log(loger):
    '''test func fro log'''
    loger.debug('from debug level')
    loger.info('from info level')
    loger.warning('from warning level')
    loger.error('from error level')
    loger.critical('from critical level')
