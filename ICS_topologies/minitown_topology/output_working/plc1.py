from minicps.devices import PLC
from utils import PLC1_DATA, STATE, PLC1_PROTOCOL
from utils import T_LVL, ATT_1, PLC1_ADDR, flag_attack_plc1, flag_attack_plc2, \
    flag_attack_communication_plc1_scada, flag_attack_communication_plc1_plc2, flag_attack_dos_plc2, CONTROL

import csv
from datetime import datetime
from decimal import Decimal

import time
import thread
import signal
import sys

tank_level=3.0
reader = 1

class PLC1(PLC):

    def write_output(self):
        print 'DEBUG plc1 shutdown'
        with open('output/plc1_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def sigint_handler(self, sig, frame):
        print "I received a SIGINT!"
        global reader
        reader = 0
        self.write_output()
        sys.exit(0)

    def get_tank_level(self, a, b):
        while reader:
            global tank_level
            tank_level = Decimal(self.get(T_LVL))

    def pre_loop(self):
        self.saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        print 'DEBUG: plc1 enters pre_loop'
        # threading
        self.reader = True
        self.local_time = 0
        self.tank_level = Decimal(self.get(T_LVL))
        #self.thread_id = thread.start_new_thread(self.get_tank_level, (0, 0))

    def main_loop(self):
        """plc1 main loop.
            - reads sensors value
            - drives actuators according to the control strategy
            - updates its enip server
        """
        fake_values = []
        while True:
            control = int(self.get(CONTROL))
            if control == 0:
                self.local_time += 1

                # non threading
                global tank_level
                tank_level = Decimal(self.get(T_LVL))
                self.saved_tank_levels.append([datetime.now(), tank_level])
                self.send(T_LVL, tank_level, PLC1_ADDR)

                if flag_attack_plc1:
                    if self.local_time in range(100, 200):
                        fake_values.append(tank_level)
                        self.set(ATT_1, 1)
                    elif self.local_time in range(250, 350):
                        self.set(ATT_1, 2)
                        tank_level = fake_values[self.local_time]
                        self.local_time += 1
                    else:
                        if flag_attack_plc2 == 0 and flag_attack_communication_plc1_scada == 0 and flag_attack_communication_plc1_plc2 == 0 and flag_attack_dos_plc2 == 0:
                            self.set(ATT_1, 0)


if __name__ == "__main__":
    plc1 = PLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)