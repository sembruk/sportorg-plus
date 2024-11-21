import datetime
import logging
from threading import main_thread

import time

from sportorg.common.singleton import singleton
from sportorg.language import _
from sportorg.libs.sfr import sfrreader
from sportorg.libs.sfr.sfrreader import SFRReaderException, SFRReaderCardChanged
from sportorg.models import memory
from sportorg.modules.reader.reader import ReaderCommand, ReaderBase, ResultThreadBase, ReaderClientBase


class SFRReaderThread(ReaderBase):

    POLL_TIMEOUT = 0.2

    def run(self):
        try:
            sfr = sfrreader.SFRReaderReadout(logger=logging.root)
        except Exception as e:
            self._logger.error(str(e))
            return
        while True:
            try:
                while not sfr.poll_card():
                    time.sleep(self.POLL_TIMEOUT)
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        sfr.disconnect()
                        self._logger.debug('Stop sfrreader')
                        return
                card_data = sfr.read_card()
                if sfr.is_card_connected():
                    self._queue.put(ReaderCommand('card_data', card_data), timeout=1)
                    sfr.ack_card()
            except SFRReaderException as e:
                self._logger.error(str(e))
            except SFRReaderCardChanged as e:
                self._logger.error(str(e))
            except Exception as e:
                self._logger.error(str(e))


class SFRResultThread(ResultThreadBase):
    def _check_data(self, card_data):
        if 'bib' in card_data:
            card_data['card_number'] = card_data['bib']  # SFR has no card id, only bib
        punches = []
        for p in card_data['punches']:
            if str(p[0]) != '0' and p[0] != '':
                punches.append(p)
        card_data['punches'] = punches
        return card_data


@singleton
class SFRReaderClient(ReaderClientBase):
    def __init__(self):
        super().__init__(reader_thread_class=SFRReaderThread, result_thread_class=SFRResultThread)

