from minicps.devices import PLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import T_LVL, P1_STS, P2_STS,ATT_1, PLC1_ADDR,  \
    flag_attack_plc2, flag_attack_dos_plc2, TIME, CONTROL
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time

logging.basicConfig(filename='plc2_debug.log', level=logging.DEBUG)
logging.debug("testing")
plc2_log_path = 'plc2.log'


class PLC2(PLC):

    def pre_loop(self):
        print 'DEBUG: plc2 enters pre_loop'
        self.local_time = -1

    def main_loop(self):
        """plc2 main loop.
            - read flow level sensors #2
            - update interval enip server
        """

        saved_tank_levels = [["iteration", "timestamp", "TANK_LEVEL"]]
        print 'DEBUG: plc2 enters main_loop.'
        while True:

            master_time = int(self.get(TIME))
            while self.local_time < master_time:
                try:

                    self.tank_level = Decimal(self.receive(T_LVL, PLC1_ADDR))

                    print("master_time %d ------------- " % master_time)
                    print("ITERATION %d ------------- " % self.local_time)
                    print("Tank Level %f " % self.tank_level)
                    saved_tank_levels.append([self.local_time, datetime.now(), self.tank_level])
                    self.local_time += 1

                    if flag_attack_plc2:
                        if 300 <= self.local_time <= 450:
                            self.set(ATT_1, 1)
                            continue
                        else:
                            self.set(ATT_1, 0)

                    if flag_attack_dos_plc2:
                        self.set(ATT_1, 0)

                except Exception:
                    if flag_attack_dos_plc2:
                        self.set(ATT_1, 1)
                    continue

                except KeyboardInterrupt:
                    with open('output/plc2_saved_tank_levels_received.csv', 'w') as f:
                        writer = csv.writer(f)
                        writer.writerows(saved_tank_levels)
                    return

            if self.local_time == master_time:

                # CONTROL PUMP1
                print("Applying control")
                print("master_time %d ------------- " % master_time)
                print("ITERATION %d ------------- " % self.local_time)

                if self.tank_level < 4:
                    self.set(P1_STS, 1)

                if self.tank_level > 6.3:
                    self.set(P1_STS, 0)

                # CONTROL PUMP2
                if self.tank_level < 1:
                    self.set(P2_STS, 1)

                if self.tank_level > 4.5:
                    self.set(P2_STS, 0)

                self.set(CONTROL, 1)
                time.sleep(0.1)

if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)