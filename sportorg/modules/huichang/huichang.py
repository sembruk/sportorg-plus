import logging
from threading import main_thread

import time
import serial
from sportorg.libs.huichang.huichang import Huichang, HuichangException, HuichangTimeout

from sportorg.common.singleton import singleton
from sportorg.models import memory
from sportorg.modules.reader.reader import ReaderCommand, ReaderBase, ResultThreadBase, ReaderClientBase


class HuichangReaderThread(ReaderBase):
    def _wait_card_data(self, hc):
        while not (card_data := hc.wait_card_data()):
            time.sleep(0.5)
            if not main_thread().is_alive() or self._stop_event.is_set():
                return
        self._queue.put(ReaderCommand('card_data', card_data), timeout=1)

    def run(self):
        try:
            hc = Huichang(port=self.port, logger=logging.root)
        except Exception as e:
            self._logger.error(str(e))
            return

        while not self._stop_event.is_set():
            try:
                self._wait_card_data(hc)
            except HuichangException as e:
                self._logger.error(str(e))
            except serial.serialutil.SerialException as e:
                self._logger.error(str(e))
                break
            except Exception as e:
                self._logger.error(str(e))
                break
        hc.disconnect()
        self._logger.debug('Stop huichang reader')


class HuichangResultThread(ResultThreadBase):
    def _check_data(self, card_data):
        return card_data

    @staticmethod
    def _get_result(card_data):
        result = ResultThreadBase._get_result(card_data)
        if 'battery_level' in card_data and card_data['battery_level'] is not None:
            result.card_battery_level = max(0, min(100, card_data['battery_level']))
        return result

@singleton
class HuichangClient(ReaderClientBase):
    def __init__(self):
        super().__init__(reader_thread_class=HuichangReaderThread, result_thread_class=HuichangResultThread)

    def start(self):
        self.port = self.choose_port()
        super().start()

    def choose_port(self):
        return memory.race().get_setting('system_port', None)

