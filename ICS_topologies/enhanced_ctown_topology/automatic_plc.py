import subprocess
import time
import sys
import argparse
import signal

class NodeControl():

    def sigint_handler(self, sig, frame):
        self.terminate()
        sys.exit(0)

    def terminate(self):
        print "Stopping Tcp dump process on PLC..."
        self.process_tcp_dump.kill()

        print "Stopping PLC..."
        self.plc_process.send_signal(signal.SIGINT)
        self.plc_process.wait()
        if self.plc_process.poll() is None:
            self.plc_process.terminate()
        if self.plc_process.poll() is None:
            self.plc_process.kill()

    def main(self):
        args = self.get_arguments()
        self.process_arguments(args)

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.interface_name = self.name + '-eth0'
        #self.configure_routing() # In enhanced ctown topology, this is handled by automatic_run.py
        self.delete_log()

        self.process_tcp_dump = self.start_tcpdump_capture()
        self.plc_process = self.start_plc()

        while self.plc_process.poll() is None:
            pass

        self.terminate()

    def process_arguments(self,arg_parser):
        if arg_parser.name:
            self.name = arg_parser.name
            print self.name
        else:
            self.name = 'plc1'

    def delete_log(self):
        subprocess.call(['rm', '-rf', self.name + '.log'])

    def start_tcpdump_capture(self):
        pcap = self.interface_name+'.pcap'
        tcp_dump = subprocess.Popen(['tcpdump', '-i', self.interface_name, '-w', 'output/'+pcap], shell=False)
        return tcp_dump

    def start_plc(self):
        plc_process = subprocess.Popen(['python', self.name + '.py'], shell=False)
        return plc_process

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script of a node in Minicps')
        parser.add_argument("--name", "-n",help="Name of the mininet node and script to run")
        return parser.parse_args()

if __name__=="__main__":
    node_control = NodeControl()
    node_control.main()