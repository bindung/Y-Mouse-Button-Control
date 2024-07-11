import sys
import multiprocessing
from threading import Thread

from PySide6.QtWidgets import QApplication, QStyleFactory

from config import Config
from mkb.mkb_controller import MKBController
from process_monitor import ProcessMonitor
from load_profiles import get_profiles
from UI.views.main_view import MainView
from globals import mouse_handler
from globals import mouse_controller, keyboard_controller
from pynput import keyboard
from time import sleep

class KeyBoardRepeatAction:
    def __init__(self, key):
        self._my_thread = None
        self._state = False
        self._key = key

    def start(self):
        if self._state:
            return

        self._state = True
        self._my_thread = Thread(target=self._actually_run, args=(), daemon=True)
        self._my_thread.start()

    def stop(self):
        self._state = False

    def _actually_run(self):
        while True:
            if self._state:
                sleep(0.1)
                keyboard_controller.tap(self._key)
            else:
                return

class KeyActionRegister:
    def __init__(self):
        self._actions = {}

    def register(self, key, action):
        self._actions[key] = action

    def stop_all(self):
        for x in self._actions.values():
            x.stop()

    def press(self, key):
        if key in self._actions:
            self.stop_all()
            self._actions[key].start()

KEY_ACTION_REGISTER = KeyActionRegister()
KEY_ACTION_REGISTER.register(keyboard.Key.f5, KeyBoardRepeatAction("x"))
KEY_ACTION_REGISTER.register(keyboard.Key.f6, KeyBoardRepeatAction("y"))
KEY_ACTION_REGISTER.register(keyboard.Key.f7, KeyBoardRepeatAction("z"))
KEY_ACTION_REGISTER.register(keyboard.Key.f8, KeyBoardRepeatAction("w"))


def key_on_press(key):
    if key in [keyboard.Key.esc, keyboard.Key.backspace]:
        KEY_ACTION_REGISTER.stop_all()
    else:
        KEY_ACTION_REGISTER.press(key)


class App(QApplication):
    def __init__(self, app_config, sys_argv):
        super(App, self).__init__(sys_argv)

        self._mutex = multiprocessing.Lock()
        self._running_processes = multiprocessing.Manager().dict()
        ProcessMonitor(self._mutex, self._running_processes)
        self._profiles = get_profiles(app_config.profile_location)
        self._profiles.current_profile = self._profiles.profiles[0]
        MKBController(mouse_handler, self._profiles, self._mutex, self._running_processes)
        self.main_view = MainView(app_config, self._profiles)
        self.setQuitOnLastWindowClosed(False)
        self.setStyle(QStyleFactory.create('Fusion'))
        self.main_view.show()


if __name__ == "__main__":
    if sys.platform.startswith('win'):
        multiprocessing.freeze_support()

    key_listener = keyboard.Listener(on_press=key_on_press)
    key_listener.start()

    config = Config()

    app = App(config, sys.argv)
    sys.exit(app.exec())
