#!/usr/bin/env python2
"""tool/daemon for work read data from atc"""
import sys
from tools import conf_log, test_log, read_buff, check_conf
from daemon import Daemon
try:
    from config import SRV_ADDR
except ImportError:
    SRV_ADDR = '127.0.0.1'
try:
    from config import SRV_PORT
except ImportError:
    SRV_PORT = 5100
try:
    from config import LOG_FILE
except ImportError:
    LOG_FILE = '/tmp/logfile.log'
try:
    from config import PID_FILE
except ImportError:
    PID_FILE = '/tmp/atc_daemon.pid'


class AtcDaemon(Daemon):
    """daemon for read data from atc"""
    def run(self):
        """in this func must read data from atc"""
        read_buff(SRV_ADDR, SRV_PORT, self.loger)


def using(loger):
    """help for using"""
    loger.info('Unknown command: %s' % ' '.join(sys.argv))
    loger.info('usage: %s start|stop|restart' % sys.argv[0])
    sys.exit(2)


def arg_parsing(atc_daemon, loger):
    """parsing input parameters"""
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            atc_daemon.start()
        elif 'stop' == sys.argv[1]:
            atc_daemon.stop()
        elif 'restart' == sys.argv[1]:
            atc_daemon.restart()
        else:
            using(loger)
        sys.exit(0)
    else:
        using(loger)


if __name__ == '__main__':
    check_conf()
    loger = conf_log(logfile=LOG_FILE)
    atc_daemon = AtcDaemon(PID_FILE, loger)
    arg_parsing(atc_daemon, loger)

    # test_log(loger)
