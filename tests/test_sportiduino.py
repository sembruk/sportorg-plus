import os
import platform
import time
import subprocess
import serial
from threading import Thread, Event
from sportorg.models.memory import race
from PySide2.QtCore import QObject, Slot, Signal, QCoreApplication, QTimer
import pytest

from sportorg.modules.sportiduino.sportiduino import SportiduinoClient

known_msgs = {
    b'\xfe\x46\x00\x46': [b'\xfe\x66\x03\x01\x09\x00\x73'],
    b'\xfe\x4b\x00\x4b': [
        b'\xfe\x63\x1e\x01\x90\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x67\x2f\xaf\xe0\x25\x67\x2f\xb4\xcf\x26\x67\x2f\xbc\x92\x23\x67\x2f\x28',
        b'\xfe\x63\x1f\xbf\x63\x24\x67\x2f\xc1\x24\x34\x67\x2f\xc4\x5d\x31\x67\x2f\xc6\x90\x30\x67\x2f\xc9\x27\x22\x67\x2f\xd0\xb0\x21\x5a',
        b'\xfe\x63\x18\x67\x2f\xd7\x09\x20\x67\x2f\xdd\xb1\x1f\x67\x2f\xdf\x28\x35\x67\x2f\xe5\x63\xf5\x67\x2f\xe7\xd9\x4f',
    ],
}

class SportiduinoEmulator(Thread):
    def __init__(self, link, stop_event):
        super().__init__()
        self.link = link
        self.stop_event = stop_event
        self.daemon = True
        self.start()

    def run(self):
        ser = serial.Serial(self.link, baudrate=38400, timeout=1)
        print(f"Emulating sportiduino on {self.link}...")
        repled = set()
        while not self.stop_event.is_set():
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                #print('<='+' '.join(format(x, '02x') for x in data))

                if data in known_msgs and data not in repled:
                    for msg in known_msgs[data]:
                        ser.write(msg)
                        #print('=>'+' '.join(format(x, '02x') for x in msg))
                        time.sleep(0.01)
                    repled.add(data)
        ser.close()

def start_socat():
    link1 = '/tmp/pty0'
    link2 = '/tmp/pty1'
    socat_command = f'socat pty,raw,echo=0,link={link1} pty,raw,echo=0,link={link2}'
    print(f"Starting socat process: {socat_command}")
    process = subprocess.Popen(socat_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    time.sleep(1)  # Allow time for the PTYs to be created
    return process, link1, link2

def stop_socat(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        print("Socat process terminated.")


class ResultHandler(QObject):
    def __init__(self):
        super().__init__()
        self.results = []

    @Slot(object)
    def add_result_from_reader(self, result):
        self.results.append(result)

@pytest.fixture
def socat():
    socat_process, link1, link2 = start_socat()
    yield socat_process, link1, link2
    stop_socat(socat_process)

@pytest.fixture
def result_handler():
    return ResultHandler()

@pytest.fixture
def app():
    app = QCoreApplication([])  # For event loop
    yield app
    app.quit()

@pytest.fixture
def set_utc_timezone():
    # Save the current TZ environment variable to restore it later
    original_tz = os.environ.get("TZ")

    # Set the desired timezone to UTC
    os.environ["TZ"] = "UTC"

    # Apply the change
    time.tzset()

    yield

    # Restore the original timezone
    if original_tz is not None:
        os.environ["TZ"] = original_tz
    else:
        del os.environ["TZ"]

    # Reapply the original timezone
    time.tzset()


@pytest.mark.skipif(platform.system() != 'Linux', reason="This test only works on Linux")
def test_sportiduino(app, result_handler, socat, set_utc_timezone):
    _, link1, link2 = socat

    stop_event = Event()
    emulator_thread = SportiduinoEmulator(link1, stop_event)

    race().set_setting('system_port', link2)

    SportiduinoClient().set_call(result_handler.add_result_from_reader)
    SportiduinoClient().start()

    # Run the event loop for a few seconds to allow the signal to be processed
    QTimer.singleShot(5000, app.quit)
    app.exec_()

    SportiduinoClient().stop()
    stop_event.set()
    #emulator_thread.quit()
    emulator_thread.join()

    assert len(result_handler.results) == 1
    result = result_handler.results[0]
    assert result.card_number == 400
    assert str(result.start_time) == '18:54:24'
    assert str(result.finish_time) == '22:53:13'

    expected = [
        (37, '19:15:27'),
        (38, '19:48:34'),
        (35, '20:00:35'),
        (36, '20:08:04'),
        (52, '20:21:49'),
        (49, '20:31:12'),
        (48, '20:42:15'),
        (34, '21:14:24'),
        (33, '21:41:29'),
        (32, '22:09:53'),
        (31, '22:16:08'),
        (53, '22:42:43'),
    ]

    for i, split in enumerate(result.splits):
        assert (int(split.code), str(split.time)) == expected[i]

