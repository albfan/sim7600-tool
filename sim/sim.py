import time
import serial


class Sim:

    def __init__(self, port):
        self.modem = serial.Serial(port, 115200)

    def write_text(self, text):
        self.__write_text(text + "\r")

    def __write_text(self, text):
        self.modem.write(str.encode(text))
        time.sleep(1)

    def __send_command(self, command):
        self.write_text(command)
        ret = []
        while self.modem.inWaiting() > 0:
            msg = self.modem.readline().strip().decode("UTF-8")
            msg = msg.replace("\r", "").replace("\n", "")
            if msg != "":
                ret.append(msg)
        return ret

    def ok(self):
        result = self.__send_command("AT")
        return len(result) == 1 and result[0] == 'OK'

    def send_command(self, command):
        result = self.__send_command("AT+"+command)
        return result

    def send_text(self, text):
        result = self.__send_command(text)
        return result

    def send_command_no_wait(self, command):
        self.write_text("AT+"+command)

    def close(self):
        self.modem.close()
