"""class for demonization process"""
import os
import time
import sys
import atexit
from signal import SIGTERM
try:
    from config import PID_FILE
except ImportError:
    PID_FILE = '/tmp/atc_daemon.pid '


class Daemon:
    """class for demonization process"""
    def __init__(self, pidfile, loger, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.loger = loger

    def daemonize(self):
        """do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16"""
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            self.loger.critical('fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent enviroment
        os.chdir('/')
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            self.loger.critical('fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standart file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        umask_original = os.umask(0)
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as fd:
            fd.write('%s\n' % pid)
        os.chmod(self.pidfile, 0o666)
        self.loger.debug('AtcDaemon start with pid: %s' % pid)
        os.umask(umask_original)

    def delpid(self):
        """remove pidfile"""
        os.remove(self.pidfile)

    def start(self):
        """Start the daemon"""
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = 'pidfile %s already exist. Daemon already running?\n'
            self.loger.warning(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """Stop the daemon"""
        self.loger.debug('AtcDaemon stop')
        # Get the pid from pid file
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = 'pidfile %s does not exist. Daemon not running?\n'
            self.loger.warning(message % self.pidfile)
            return

        # Try killing the daemon process
        try:
            os.remove(self.pidfile)
        except OSError:
            with open(self.pidfile, 'w') as fd:
                fd.write('')
                # if err.find("No such process") > 0:
                #    if os.path.exists(self.pidfile):
                #        os.remove(self.pidfile)
                # else:
                #    sys.exit(1)

    def restart(self):
        """Restart the daemon"""
        self.stop()
        time.sleep(1)
        self.start()

    def run(self):
        """You should override this method when you subclass Daemon.
        It will be called after the process has been
        daemonized by start() or restart()."""
        pass
