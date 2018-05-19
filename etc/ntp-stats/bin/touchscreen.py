#!/usr/bin/python
import argparse
import os
import select, signal, struct, subprocess, sys
import time


backlight_file = "/sys/class/backlight/soc:backlight/brightness"
image_file = "/dev/shm/ntp/localhost-{0}-ntp-{1}.png"
framebuffer_file = "/dev/fb1"
touch_timeout = 1
backlight_timeout = 60
graph_types = [ "offset", "temp", "loadavg", "wantder", "clkjit", "sysjit", "disp", "freq" ]
graph_ranges = [ "hour", "day", "week", "fortnight", "month" ]



in_file = False
null_file = False
edge_raise = False
graph_type_index = 0
graph_range_index = 0


def daemonize(pid_file):
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError as err:
        sys.stderr.write('_Fork #1 failed: {0}\n'.format(err))
        sys.exit(1)
    # decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)
    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            sys.exit(0)
    except OSError as err:
        sys.stderr.write('_Fork #2 failed: {0}\n'.format(err))
        sys.exit(1)
    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.devnull, 'r')
    so = open(os.devnull, 'w')
    se = open(os.devnull, 'w')
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    if pid_file:
        p_f = open(pid_file, 'w')
        p_f.write("{}".format(os.getpid()))
        p_f.close()

def exit_handler(signum, frame):
    print 'Exiting...'
    if in_file:
        in_file.close()

    if null_file:
        null_file.close()

    if os.path.isfile(args.pid_file):
        os.remove(args.pid_file)

    exit(1)

def get_backlight():
    backlight = open(backlight_file, "r")
    state = backlight.read(1)
    backlight.close()
    return state


def set_backlight(val):
    if val != 0 and val != 1:
        return 1

    if val == 1:
        print "Turning light ON"
    if val == 0:
        print "Turning light OFF"

    backlight = open(backlight_file, "wb")
    backlight.write("{}".format(val))
    backlight.close()

def update_screen(img, timeout):
    subprocess.call([ "/usr/bin/fbi",
        "-T", "2",
        "--once", "-t", "{}".format(backlight_timeout+2),
        "--nocomments", "--noedit", "--noverbose",
        "-d", framebuffer_file,
        "-a", img ], 
        )
    time.sleep(0.4)
    print "Screen refreshed"

def convert_arg_line_to_args(arg_line):
    for arg in arg_line.split():
        if not arg.strip():
            continue
        yield arg


# ---- MAIN ---- #
parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
            description="Read touchscreen incoming event to turn the backlight ON and refresh the screen",
            epilog="You can use '@filename' to read arguments from a file.")

parser.convert_arg_line_to_args = convert_arg_line_to_args

parser.add_argument("--event-device", metavar="<filename>", dest="event_dev", default="/dev/input/event0", help="Device to read input events from")
parser.add_argument("--show-events", action='store_true', dest="show_evt", default=False, help="Show event information when running in the foreground (requires '--foreground')")
parser.add_argument("--foreground", action='store_true', dest="foreground", default=False, help="Do not daemonize and keep running the process in the foreground")
parser.add_argument("--pid-file", metavar="<filename>", dest="pid_file", default="/var/run/touchscreen.pid", help="File that contains the progran PID for process management")


args = parser.parse_args()

if args.foreground == False:
    daemonize(args.pid_file)

null_file = open(os.devnull, 'w')

# set signal handlers
signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

infile_path = args.event_dev

FORMAT = 'llHHI' #long int, long int, unsigned short, unsigned short, unsigned int
EVENT_SIZE = struct.calcsize(FORMAT)

in_file = open(infile_path, "rb")

b_t = backlight_timeout

while True:
    r, w, e = select.select([ in_file ], [], [], touch_timeout)
    if in_file in r:
        event = in_file.read(EVENT_SIZE)

        if args.show_evt == True and args.foreground == True:
            (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)

            if type != 0 or code != 0 or value != 0:
                print("Event type %u, code %u, value %u at %d.%d" % (type, code, value, tv_sec, tv_usec))
            else:
                # Events with code, type and value == 0 are "separator" events
                print("===========================================")

        # reset backlight timeout
        b_t = backlight_timeout

        if edge_raise == False:
            edge_raise = True
            i = image_file.format(graph_ranges[graph_range_index], graph_types[graph_type_index])
            update_screen(i, backlight_timeout)

            graph_range_index = graph_range_index + 1

            if graph_range_index >= len(graph_ranges):
                graph_range_index = 0
                graph_type_index = graph_type_index + 1

            if graph_type_index >= len(graph_types):
                graph_type_index = 0

            if get_backlight() == "0":
                set_backlight(1)


    else:
        edge_raise = False
        print "backlight state: '" + get_backlight() + "'"

    print "Backlight time: {}".format(b_t)

    if b_t <= 0 and get_backlight() == "1":
        print "Backlight timeout reached"
        set_backlight(0)
    else:
        if b_t > 0:
            b_t = b_t - touch_timeout
