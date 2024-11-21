import logging
from threading import main_thread

import time
import serial
import termios

from sportorg.common.singleton import singleton
from sportorg.libs.sportiduino import sportiduino
from sportorg.models import memory
from sportorg.modules.reader.reader import ReaderCommand, ReaderBase, ResultThreadBase, ReaderClientBase


class SportiduinoReaderThread(ReaderBase):
    def _sportiduino_poll_card(self, sduino):
        while not sduino.poll_card():
            time.sleep(0.5)
            if not main_thread().is_alive() or self._stop_event.is_set():
                return
        card_data = sduino.card_data
        self._queue.put(ReaderCommand('card_data', card_data), timeout=1)
        sduino.beep_ok()

    def run(self):
        try:
            sduino = sportiduino.Sportiduino(port=self.port, logger=logging.root)
        except Exception as e:
            self._logger.error(str(e))
            return

        while not self._stop_event.is_set():
            try:
                self._sportiduino_poll_card(sduino)
            except sportiduino.SportiduinoException as e:
                self._logger.error(str(e))
            except (serial.serialutil.SerialException, termios.error) as e:
                self._logger.error(str(e))
                break
            except Exception as e:
                self._logger.error(str(e))
        sduino.disconnect()
        self._logger.debug('Stop sportiduino reader')


class SportiduinoResultThread(ResultThreadBase):
    def _check_data(self, card_data):
        return card_data


@singleton
class SportiduinoClient(ReaderClientBase):
    def __init__(self):
        super().__init__(reader_thread_class=SportiduinoReaderThread, result_thread_class=SportiduinoResultThread)

    def start(self):
        self.port = self.choose_port()
        super().start()

    def choose_port(self):
        return memory.race().get_setting('system_port', None)

