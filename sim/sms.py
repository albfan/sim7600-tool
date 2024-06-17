import json
import sys
from enum import Enum
from messaging.sms import SmsDeliver
from . import Sim
from .output import Output
import re


class Sms:
    class SmsStatus(Enum):
        UNREAD = 0
        READ = 1
        ALL = 4

    class OperationMode(Enum):
        PDU = 0
        TEXT = 1

    class Message:
        text = ""
        sender = ""
        number = ""
        date = ""

        def __init__(self, text="", sender="", number="", date=""):
            self.text = text
            self.sender = sender
            self.number = number
            self.date = date

        @property
        def data(self):
            return {
                'text': self.text,
                'sender': self.sender,
                'number': self.number,
                'date': self.date
            }

    def __init__(self, port, out=Output(), mode=OperationMode.PDU ):
        self.sim = Sim(port)
        self.out = out
        if self.sim.ok():
            self.out.verbose("Successful init of SMS")
            if self.__set_operation_mode(mode):
                self.out.verbose("Operation mode set successfully")
            else:
                self.out.output("Could not set Operation mode for SMS")
                sys.exit(2)
        else:
            self.out.output("Could not init SMS")
            sys.exit(2)

    def __set_operation_mode(self, operation_mode=OperationMode.PDU):
        self.out.verbose("Setting Operation Mode to " + str(operation_mode))
        result = self.sim.send_command("CMGF=" + str(operation_mode.value))
        return len(result) == 1 and result[0] == "OK"

    def __parse_message(self, sms):
        text = sms.text
        number = sms.csca
        sender = sms.number
        date = sms.date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        return Sms.Message(text=text, sender=sender, number=number, date=date)

    def read_sms(self, status=SmsStatus.UNREAD):
        self.out.verbose("Reading SMS of status " + str(status))
        list = self.sim.send_command("CMGL=" + str(status.value))
        ret = []
        for item in list:
            if not item.startswith("AT+") and not item.startswith("+CMGL") and not item == "OK":
                ret.append(self.__parse_message(SmsDeliver(item)))
        return ret

    def send_sms(self, phone_number, text):
        self.out.verbose("Sending SMS")
        self.sim.send_command_no_wait('CMGS="' + str(phone_number) + '"')
        ctrl_z = '\x1a'
        list = self.sim.send_text(str(text)+ctrl_z)
        ret = []
        for item in list:
            if item.startswith("+CMGS:"):
                ret.append(re.match('\+CMGS: (\d+)', item).group(1))
                return ret
        return -1

    def print_read_sms(self, status=SmsStatus.UNREAD):
        sms_list = self.read_sms(status)
        data_list = map(lambda x: x.data, sms_list)
        sms_json = json.dumps(data_list)
        self.out.output(sms_json)

    def delete_sms(self):
        self.out.verbose("Deleting all messages")
        result = self.sim.send_command("CMGD=1,1")
        return len(result) == 2 and result[1] == "OK"

    def print_delete_sms(self):
        result = self.delete_sms()
        self.out.output(json.dumps({'deleteSms': {'successful': result}}))

    def close(self):
        self.sim.close()


if __name__ == "__main__":
    port = "/dev/ttyS0" # Raspberry Pi 3
    sms = Sms(port)
    sms.read_sms()
    sms.close()
