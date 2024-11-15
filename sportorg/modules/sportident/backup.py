import sys
import os
import logging
from datetime import datetime
from multiprocessing import Process, Queue, Event


from sportorg import config
from sportorg.common.fake_std import FakeStd
from sportorg.common.singleton import singleton
from sportorg.utils.time import time_to_hhmmss, hhmmss_to_time, time_to_datetime


class BackupProcess(Process):
    def __init__(self, queue, stop_event):
        super().__init__()
        self.queue = queue
        self.stop_event = stop_event

    def run(self):
        logging.debug('Start backup process')
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = FakeStd()
        sys.stderr = FakeStd()
        while not self.stop_event.is_set():
            try:
                data = self.queue.get(timeout=1)  # wait for data from queue (1 sec timeout)
                self._write_to_log(data)
            except TimeoutError:
                pass
            except Exception as e:
                logging.error(f'Backup process error: {e}')
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        logging.debug('Stop backup process')

    def _write_to_log(self, data):
        log_file_path = config.log_dir(f'cards_{datetime.now().strftime("%Y-%m-%d")}.log')
        with open(log_file_path, 'a') as f:
            f.write(data)


@singleton
class CardDataBackuper(object):
    def __init__(self):
        self.queue = Queue()
        self.stop_event = Event()
        self.backup_process = None

    def _ensure_backup_process_started(self):
        if self.backup_process is None:
            self.backup_process = BackupProcess(self.queue, self.stop_event)
            self.stop_event.clear()
            self.backup_process.start()

    def backup_card_data(self, card_data):
        lines = [
            f"begin {datetime.now().strftime('%H:%M:%S')}",
            f"card: {card_data['card_number']}",
            f"start: {time_to_hhmmss(card_data['start']) if 'start' in card_data else ''}",
            f"finish: {time_to_hhmmss(card_data['finish']) if 'finish' in card_data else ''}",
            "split_begin"
        ]
        for punch_code, punch_time in card_data['punches']:
            lines.append(f"{punch_code} {time_to_hhmmss(punch_time)}")

        lines.extend([
            "split_end",
            "end\n"
        ])
        text = '\n'.join(lines)
        self._ensure_backup_process_started()
        self.queue.put(text)

    def save_event(self):
        if self.backup_process is not None:
            self.queue.put('SAVE')

    def stop(self):
        self.stop_event.set()
        if self.backup_process is not None:
            self.backup_process.join()


def find_last_save_position(file_path, chunk_size=1024):
    """Find the last occurrence of 'SAVE' in the file and return its position."""
    with open(file_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        buffer = b''
        position = file_size

        # Read the file in reverse chunks
        while position > 0:
            # Determine how far to jump back
            read_size = min(chunk_size, position)
            position -= read_size

            # Move back and read the chunk
            f.seek(position)
            chunk = f.read(read_size)
            buffer = chunk + buffer

            # Split the buffer into lines and process in reverse order
            lines = buffer.split(b'\n')
            if position > 0:
                buffer = lines.pop(0)  # Retain incomplete line for next iteration

            # Process lines from the end
            for line in reversed(lines):
                decoded_line = line.decode('utf-8').strip()
                if "SAVE" in decoded_line:
                    # Calculate the position of "SAVE"
                    save_position = position + sum(len(l) + 1 for l in lines[:lines.index(line) + 1])
                    return save_position

        # Check the first part of the file if no "SAVE" found
        if buffer:
            line = buffer.decode('utf-8').strip()
            if "SAVE" in line:
                return 0

    return None  # Return None if "SAVE" is not found


def parse_backup_from_last_save():
    """Parses the backup log from the last 'SAVE' entry to the end."""
    log_file_path = config.log_dir(f'cards_{datetime.now().strftime("%Y-%m-%d")}.log')
    if not os.path.exists(log_file_path):
        return []

    # Find the last occurrence of "SAVE"
    save_position = find_last_save_position(log_file_path)
    logging.debug(f"Last save position: {save_position}")

    entries = []
    entry = {}
    punches = []
    parsing_punches = False

    with open(log_file_path, 'r') as f:
        if save_position:
            # Seek to the position of the last occurrence of "SAVE"
            f.seek(save_position)

        for line in f:
            line = line.strip()

            if line.startswith("begin"):
                # Start a new entry
                entry = {"readout": line.split()[1]}  # Extract timestamp if needed
                punches = []
                parsing_punches = False

            elif line.startswith("card:"):
                # Extract card number
                entry["card_number"] = int(line.split(": ")[1])

            elif line.startswith("start:"):
                # Extract start time
                time = line.split(": ")[1]
                entry["start"] = time_to_datetime(hhmmss_to_time(time)) if time else None
            elif line.startswith("finish:"):
                # Extract finish time
                time = line.split(": ")[1]
                entry["finish"] = time_to_datetime(hhmmss_to_time(time)) if time else None

            elif line == "split_begin":
                # Begin parsing punches
                parsing_punches = True

            elif line == "split_end":
                # End parsing punches
                entry["punches"] = punches
                parsing_punches = False

            elif line == "end":
                # End of entry; add to entries list
                entries.append(entry)
                entry = {}
                punches = []

            elif parsing_punches:
                # Parse each punch
                punch_code, punch_time = line.split()
                punches.append((int(punch_code), time_to_datetime(hhmmss_to_time(punch_time))))

    return entries

