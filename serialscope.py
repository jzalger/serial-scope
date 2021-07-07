# This module defines functionality for the deepsix interface device
import getopt
import serial
import threading
import pandas as pd
import pylab as plt
from sys import argv, exit


class SerialScope:

    def __init__(self, serial_port='/dev/tty.usbserial-0221E24A', serial_baud=9600, headers=None, serial_log_limit=1000) -> None:
        self.serial_port = serial_port
        self.serial_baud = serial_baud
        self._monitoring_serial = False
        self._serial_thread = None
        self._x_axis_header = headers[0]
        self._headers = headers
        self._data_headers = headers[1:]
        self._buffer = pd.DataFrame(columns=headers)

    def start_monitoring_serial(self):
        self.serial_thread = threading.Thread(target=self._monitor_serial).start()
        self._monitoring_serial = True
        
    def stop_monitoring_serial(self):
        self.serial_thread.join()
        self._monitoring_serial = False

    def flush_serial_log(self):
        self.serial_log = list()

    def _monitor_serial(self, msg_handlers) -> None:
        while True:
            with serial.Serial(self.serial_port, self.serial_baud, timeout=5) as hardware_serial:
                msg = hardware_serial.readline()
                data = self._parse_msg(msg)
                self.add_data(data)
                self.update_plot()
                if len(self.serial_log) > self.serial_log_limit:
                    self.flush_serial_log()
    
    def _parse_msg(self, msg) -> list:
        # FIXME: manage this more generically
        parts = msg.split(":")
        data = parts[1].split(",")
        return data

    def add_data(self, data):
        new_df = pd.DataFrame(data, columns=self._headers)
        pd.concat([self._buffer, new_df])

    def create_plot(self):
        plt.ion()
        X = self._buffer([self._x_axis_header])
        for header, values in self._buffer(self._data_headers).iteritems():
            plt.plot(X, values.values(), label=header)

    def update_plot(self):
        # self.graph.set_y_data(self.buffer)
        plt.draw()
        plt.pause(0.01)


def parse_opts(args):
    try:
        opts, args = getopt.getopt(args, "p:b:", ["headers="])
    except getopt.GetoptError:
        print_help
        exit(2)
    parsed = dict()
    for opt, arg in opts:
        if opt == '-p':
            parsed["port"] = arg
        elif opt == '-b':
            parsed["baud"] = arg
        elif opt == '--headers':
            parsed["headers"] = arg
        else:
            print_help
            exit(2) 
    return parsed

def print_help():
    print('serialscope.py -p <serial_port> -b <serial_baud> -h <header1,header2,..,headern>. Assumes value in first index is X axis.')

def main(args):
    parsed = parse_opts(args)
    scope = SerialScope(serial_port=parsed["port"], serial_baud=parsed["baud"], headers=parsed["headers"])
    scope.start_monitoring_serial()

if __name__ == "__main__":
    main(argv[1:])

    
    