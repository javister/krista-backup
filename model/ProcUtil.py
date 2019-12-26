import os


class CapturedProcess:
    def __init__(self):
        pid = None
        name = None
        cmdline = None


# Возвращает генератор CapturedProcess
def process_iter():
    pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
    for pid in pids:
        try:
            cmdline = (
                open(os.path.join("/proc", pid, "cmdline"), "rb")
                .read()
                .decode("utf-8")
                .split("\0")
            )

            process = CapturedProcess()
            process.pid = int(pid)
            process.name = cmdline[0]
            process.cmdline = " ".join(cmdline)

            yield process
        except IOError:  # proc has already terminated
            continue

