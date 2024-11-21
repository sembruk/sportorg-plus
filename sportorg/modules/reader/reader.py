import logging
import time

from queue import Queue, Empty
from threading import main_thread, Event
from PySide2.QtCore import QThread, Signal

from sportorg.models import memory
from sportorg.modules.reader.backup import CardDataBackuper
from sportorg.utils.time import time_to_otime

class ReaderCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data


class ReaderBase(QThread):
    #data_sender = Signal(object)

    def __init__(self, port, queue, stop_event, logger):
        super().__init__()
        self.port = port
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        raise NotImplementedError("Derived classes must implement this method.")

    def _check_data(self, card_data):
        return card_data

    @staticmethod
    def _get_result(card_data, result_type):
        result = memory.race().new_result(result_type)
        result.card_number = card_data.get('bib') or card_data.get('card_number')

        for punch in card_data['punches']:
            t = punch[1]
            if t:
                split = memory.Split()
                split.code = str(punch[0])
                split.time = time_to_otime(t)
                split.days = memory.race().get_days(t)
                result.splits.append(split)

        result.start_time = time_to_otime(card_data['start']) if 'start' in card_data else None
        result.finish_time = time_to_otime(card_data['finish']) if 'finish' in card_data else None

        return result

class ResultThreadBase(QThread):
    data_sender = Signal(object)

    def __init__(self, queue, stop_event, backuper, logger):
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._backuper = backuper
        self._logger = logger or logging.root

    def run(self):
        time.sleep(3)
        while not self._stop_event.is_set():
            try:
                cmd = self._queue.get(timeout=2)
                if cmd.command in ('card_data', 'backup_card_data'):
                    result = self._get_result(self._check_data(cmd.data))
                    self.data_sender.emit(result)
                    if cmd.command == 'card_data':
                        self._backuper.backup_card_data(cmd.data)
                    elif cmd.command == 'backup_card_data':
                        # Run backup process for writing SAVE in backup file
                        self._backuper.ensure_backup_process_started()
                        self._logger.info(f'Card No. {cmd.data["card_number"]} has been restored from backup')
            except Empty:
                if not main_thread().is_alive():
                    break
            except Exception as e:
                self._logger.error(str(e))
        self._logger.debug(f'Stop {self.__class__.__name__}')

    def _check_data(self, card_data):
        return card_data

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result()
        result.card_number = int(card_data['card_number'])

        for i in range(len(card_data['punches'])):
            t = card_data['punches'][i][1]
            if t:
                split = memory.Split()
                split.code = str(card_data['punches'][i][0])
                split.time = time_to_otime(t)
                split.days = memory.race().get_days(t)
                result.splits.append(split)

        if 'start' in card_data:
            result.start_time = time_to_otime(card_data['start'])
        if 'finish' in card_data:
            result.finish_time = time_to_otime(card_data['finish'])

        return result


class ReaderClientBase(object):
    def __init__(self, reader_thread_class, result_thread_class):
        self.port = None
        self.is_need_check_backup = True
        self._queue = Queue()
        self._stop_event = Event()
        self._reader_thread = None
        self._result_thread = None
        self._logger = logging.root
        self._call_back = None
        self._backuper = CardDataBackuper(self.log_file_prefix())

        self._reader_thread_class = reader_thread_class
        self._result_thread_class = result_thread_class

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _is_thread_not_started(self, thread_instance):
        if thread_instance is None or thread_instance.isFinished():
            return True
        return False

    def _start_reader_thread(self):
        if self._is_thread_not_started(self._reader_thread):
            self._reader_thread = self._reader_thread_class(
                self.port,
                self._queue,
                self._stop_event,
                self._logger
            )
            self._reader_thread.start()

    def _start_result_thread(self):
        if self._is_thread_not_started(self._result_thread):
            self._result_thread = self._result_thread_class(
                self._queue,
                self._stop_event,
                self._backuper,
                self._logger,
            )
            if self._call_back:
                self._result_thread.data_sender.connect(self._call_back)
            self._result_thread.start()
        # elif not self._result_thread.is_alive():
        elif self._result_thread.isFinished():
            self._result_thread = None
            self._start_result_thread()

    def start(self):
        """Start the reader and result threads."""
        self._stop_event.clear()
        self._start_reader_thread()
        self._start_result_thread()
        self._logger.debug(f'{self.__class__.__name__} started')

    def stop(self):
        """Stop the reader and result threads."""
        self._stop_event.set()
        if self._reader_thread is not None:
            self._reader_thread.quit()
            self._reader_thread.wait()
        if self._result_thread is not None:
            self._result_thread.quit()
            self._result_thread.wait()
        self._backuper.stop()

    def toggle(self):
        """Toggle the client between start and stop states."""
        if self.is_alive():
            self.stop()
        else:
            self.start()

    def inject_backup_card_data(self, entries):
        """Inject backup card data into the queue."""
        for entry in entries:
            self._queue.put(ReaderCommand('backup_card_data', entry), timeout=1)

    def save_event(self):
        self._backuper.save_event()

    def is_alive(self):
        """Check if the client is running."""
        if self._reader_thread and not self._reader_thread.isFinished():
            return self.is_result_thread_alive()
        return False
    
    def is_result_thread_alive(self):
        if self._result_thread:
            return not self._result_thread.isFinished()
        return False

    @classmethod
    def log_file_prefix(cls):
        return cls.__name__.lower().replace('client', '').replace('base', '')


