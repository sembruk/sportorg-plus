import datetime
import logging
import os
import platform
import re
import time

import serial
from PySide2.QtCore import QThread, Signal
from sportident import SIReader, SIReaderReadout, SIReaderSRR, SIReaderControl, SIReaderException, SIReaderCardChanged

from sportorg.common.singleton import singleton
from sportorg.language import _
from sportorg.models import memory
from sportorg.modules.reader.reader import ReaderCommand, ReaderBase, ResultThreadBase, ReaderClientBase


class SIReaderThread(ReaderBase):
    def run(self):
        try:
            si = SIReaderReadout(port=self.port)
            if si.get_type() == SIReader.M_SRR:
                si.disconnect()  # release port
                si = SIReaderSRR(port=self.port)
            elif si.get_type() == SIReader.M_CONTROL or si.get_type() == SIReader.M_BC_CONTROL:
                si.disconnect()  # release port
                si = SIReaderControl(port=self.port)

            si.poll_sicard() # try to poll immediately to catch an exception
        except Exception as e:
            self._logger.debug(str(e))
            return

        max_error = 2000
        error_count = 0

        while not self._stop_event.is_set():
            try:
                while not si.poll_sicard():
                    time.sleep(0.2)
                    if not main_thread().is_alive():
                        break
                card_data = si.read_sicard()
                card_data['card_type'] = si.cardtype
                self._queue.put(ReaderCommand('card_data', card_data), timeout=1)
                si.ack_sicard()
            except SIReaderException as e:
                error_count += 1
                self._logger.error(str(e))
                if error_count > max_error:
                    return
            except SIReaderCardChanged as e:
                self._logger.error(str(e))
            except serial.serialutil.SerialException as e:
                self._logger.error(str(e))
                return
            except Exception as e:
                self._logger.exception(str(e))
        si.disconnect()
        self._logger.debug('Stop sireader')


class SIResultThread(ResultThreadBase):
    def _check_data(self, card_data):
        # TODO requires more complex checking for long starts > 12 hours
        start_time = self.get_system_zero_time()
        if start_time and card_data['card_type'] == 'SI5':
            start_time = self.time_to_sec(start_time)
            for i in range(len(card_data['punches'])):
                if self.time_to_sec(card_data['punches'][i][1]) < start_time:
                    new_datetime = card_data['punches'][i][1].replace(hour=(card_data['punches'][i][1].hour + 12) % 24)
                    card_data['punches'][i] = (card_data['punches'][i][0], new_datetime)

                # simple check for morning starts (10:00 a.m. was 22:00 in splits)
                if self.time_to_sec(card_data['punches'][i][1]) - 12 * 3600 > start_time:
                    new_datetime = card_data['punches'][i][1].replace(hour=card_data['punches'][i][1].hour - 12)
                    card_data['punches'][i] = (card_data['punches'][i][0], new_datetime)

        return card_data

    @staticmethod
    def time_to_sec(value, max_val=86400):
        if isinstance(value, datetime.datetime):
            ret = value.hour * 3600 + value.minute * 60 + value.second + value.microsecond / 1000000
            if max_val:
                ret = ret % max_val
            return ret

        return 0

    @staticmethod
    def get_system_zero_time():
        start_time = memory.race().get_setting('system_zero_time', (8, 0, 0))
        return datetime.datetime.today().replace(
            hour=start_time[0],
            minute=start_time[1],
            second=start_time[2],
            microsecond=0
        )


@singleton
class SIReaderClient(ReaderClientBase):
    def __init__(self):
        super().__init__(reader_thread_class=SIReaderThread, result_thread_class=SIResultThread)

    def start(self):
        self.port = self.choose_port()
        if self.port:
            self._logger.info(_('Opening port {}').format(self.port))
            super().start()
        else:
            self._logger.info(_('Cannot open port'))

    @staticmethod
    def get_ports():
        ports = []
        if platform.system() == 'Linux':
            scan_ports = [os.path.join('/dev', f) for f in os.listdir('/dev') if
                     re.match('ttyS.*|ttyUSB.*', f)]
        elif platform.system() == 'Windows':
            scan_ports = ['COM' + str(i) for i in range(48)]

        for p in scan_ports:
            try:
                com = serial.Serial(p, 38400, timeout=5)
                com.close()
                ports.append(p)
            except serial.SerialException:
                continue

        return ports

    def choose_port(self):
        si_port = memory.race().get_setting('system_port', '')
        if si_port:
            return si_port
        ports = self.get_ports()
        if len(ports):
            self._logger.info(_('Available Ports'))
            for i, p in enumerate(ports):
                self._logger.info("{} - {}".format(i, p))
            return ports[0]
        else:
            self._logger.info('No ports available')
            return None


class ScanPortsThread(QThread):
    result_signal = Signal(list)

    def run(self):
        result = SIReaderClient().get_ports()
        self.result_signal.emit(result)

