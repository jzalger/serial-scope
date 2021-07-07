# This module defines functionality for the deepsix interface device
import getopt
from numpy import ceil, mod
import serial
import threading
import pandas as pd
import pylab as plt
from sys import argv, exit
from serial.serialutil import SerialException


class SerialScope:

    def __init__(self, serial_port=None, serial_baud=None, headers=None, serial_log_limit=1000) -> None:
        parsed_headers = headers.split(",")
        self.indicies = None
        self.serial_port = serial_port
        self.serial_baud = serial_baud
        self.serial_log_limit = serial_log_limit
        self._monitoring_serial = False
        self._serial_thread = None
        self._x_axis_header = parsed_headers[0]
        self._headers = parsed_headers
        self._data_headers = parsed_headers[1:]
        self._buffer = pd.DataFrame(columns=parsed_headers)
        
        plt.ion()
        if len(self._data_headers) <= 3:
            rows, cols = 1, len(self._data_headers)
        else:
            rows, cols = int(ceil(len(self._data_headers)/3)), 3
        self.fig, self.axes = plt.subplots(rows, cols)
        plots = [p.plot([],[])[0] for p in self.axes.flat]
        self._header_plot_map = {h:i for h,i in zip(self._data_headers, plots)}
        plt.show()

    def start_monitoring_serial(self):
        # self.serial_thread = threading.Thread(target=self._monitor_serial).start()
        self._monitor_serial()
        self._monitoring_serial = True
        
    def stop_monitoring_serial(self):
        self.serial_thread.join()
        self._monitoring_serial = False

    def flush_serial_log(self):
        pass

    def _monitor_serial(self) -> None:
        try:
            with serial.Serial(self.serial_port, self.serial_baud, timeout=1) as hardware_serial:
                while True:
                    msg = hardware_serial.readline()
                    data = self._parse_msg(msg.decode('utf-8'))
                    self.add_data(data)
                    self.update_plot()
        except SerialException:
            print("Could not open that serial port (%s) or baud (%s)", self.serial_port, self.serial_baud)
            exit(2)
    
    def _parse_msg(self, msg) -> list:
        # FIXME: manage this more generically
        parts = msg.split(":")
        data = parts[1].replace("\r\n","").split(",")
        return data

    def add_data(self, data):
        new_df = pd.DataFrame([data], columns=self._headers)
        self._buffer = pd.concat([self._buffer, new_df])

    def update_plot(self):
        X = self._buffer[self._x_axis_header]
        for header, values in self._buffer[self._data_headers].iteritems():
            axis = self._header_plot_map[header]
            axis.set_data(X, values)
            plt.draw()
        plt.pause(0.01)
        plt.show()


def parse_opts(args):
    try:
        opts, args = getopt.getopt(args, "p:b:", ["headers=","indicies="])
        parsed = dict()
        for opt, arg in opts:
            if opt == '-p':
                parsed["port"] = arg
            elif opt == '-b':
                parsed["baud"] = arg
            elif opt == '--headers':
                parsed["headers"] = arg         
            # TODO: Add verification for parameters
        return parsed
    except getopt.GetoptError:
        print_help()
        exit(2)

def print_help():
    print('serialscope.py -p <serial_port> -b <serial_baud> --headers <header1,header2,..,headern> Assumes value in first index is X axis.')

def main(args):
    parsed = parse_opts(args)
    scope = SerialScope(serial_port=parsed["port"], serial_baud=parsed["baud"], headers=parsed["headers"])
    scope.start_monitoring_serial()

if __name__ == "__main__":
    main(argv[1:])

    
    