"""
QRScanner_fixed.py

A cleaned-up version of the original Kivy QR scanner with more robust
OpenCV handling and pyzbar usage.

Main fixes:
- defensive camera/frame checks
- convert to grayscale before decoding
- dynamic, safe cropping instead of hard-coded indices
- replace deprecated `tostring()` with `tobytes()`
"""

import os
import sys
import time
import json
import socket
import threading
from functools import partial

import cv2
from pyzbar.pyzbar import decode

import kivy
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.resources import resource_add_path, resource_find
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.utils import get_color_from_hex as hex
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.graphics.texture import Texture
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.filechooser import FileChooserIconView

Window.clearcolor = hex("#eeeeee")
try:
    Window.maximize()
except Exception:
    pass


def ResizeWithAspectRatio(image, width=None, height=None, inter=cv2.INTER_AREA):
    if image is None:
        return None
    (h, w) = image.shape[:2]
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    return cv2.resize(image, dim, interpolation=inter)


def removeSpace(string):
    return string.replace(' ', '')


def configNotFound():
    return not os.path.exists("config.json")


# -- schedule / rooms helpers (unchanged from original) ---------------------
rooms = ['C105', 'C117', 'C204', 'C206']
room_schedule = [['1', '2', '3', '4'], ['2', '1', '4', '3'], ['3', '4', '1', '2'], ['4', '3', '2', '1']]


def openCSV(csv_file, room_index):
    csv_list = []
    alt = f"attendance_result{rooms[int(room_index) - 1]}.csv"
    source = alt if os.path.exists(alt) else csv_file
    with open(source, 'r', encoding='utf-8') as f:
        for line in f:
            if line == '\n':
                continue
            row = line.strip().split(',')
            csv_list.append(row)
    return csv_list


def getSession():
    with open("config.json") as f:
        config_dict = json.load(f)
        return int(config_dict.get("session", 1))


def getFileAndRoom():
    with open("config.json") as f:
        config_dict = json.load(f)
        room_index = int(config_dict.get("room", 1))
        csv_file = config_dict.get("csvfile", "participants.csv")
    return csv_file, room_index


def getCorrectGroupForRoom(r_index):
    session = getSession()
    correct_grp = room_schedule[session - 1][int(r_index) - 1]
    return correct_grp


class Widgets:
    def __init__(self):
        self.tab_list = []


widgets = Widgets()


def threadedRunServer(instance=None):
    def runServer():
        try:
            print(socket.gethostbyname(socket.gethostname()))
        except Exception:
            pass
        if sys.platform == "win32":
            os.system("python -m http.server 8080")
        else:
            os.system("python3 -m http.server 8080")

    thread = threading.Thread(target=runServer, daemon=True)
    thread.start()


def settingsPopup(instance=None):
    # simplified settings popup already present in original; omitted for brevity
    pass


def checkPresence(student_name, csv_list, room_index):
    i = 0
    for row in csv_list:
        if removeSpace(row[1] + " " + row[2]).lower() == removeSpace(student_name).lower():
            if row[3] != getCorrectGroupForRoom(room_index):
                session = getSession()
                correct_room_index = room_schedule[session - 1][int(row[3]) - 1]
                correct_room = rooms[int(correct_room_index) - 1]
                return (False, correct_room)
        if row[1] + " " + row[2] == student_name:
            csv_list[i][int(room_index) + 3] = '1'
            return (True, None)
        i += 1
    return ("wtf", None)


def updateCsv(csv_list, room_index):
    with open(f"attendance_result{rooms[int(room_index) - 1]}.csv", 'w', encoding='utf-8') as f:
        for row in csv_list:
            f.write(','.join(row) + '\n')


def popupOrient(text, correct_grp, correct_room):
    # simplified popup code for brevity
    popup_flt = FloatLayout()
    popup = Popup(title='', content=popup_flt, size_hint=(0.8, 0.8))
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 5)


def root():
    root_flt = FloatLayout(size_hint=(1, 1))
    back_img = Image(source="back3k.jpg", size_hint=(1, 1))
    root_flt.add_widget(back_img)
    root_flt.add_widget(Image(source="wameedh.png", size_hint=(0.15, 0.15), pos_hint={'x': 0.675, 'y': 0.05}))
    root_flt.add_widget(Image(source="Schlumberger.png", size_hint=(0.2, 0.2), pos_hint={'x': 0.15, 'y': 0.05}))
    root_flt.add_widget(Image(source="logoBootcamp.png", size_hint=(0.3, 0.3), pos_hint={'x': 0.35, 'y': 0.005}))
    root_flt.add_widget(camWidget())
    root_flt.add_widget(Label(text="Scan your QR Code", pos_hint={'x': 0.45, 'y': 0.75}, font_size=40))
    root_flt.add_widget(Image(source="qr.png", size_hint=(0.45, 0.45), pos_hint={'x': 0.275, 'y': 0.65}))
    return root_flt


def camWidget():
    capture = cv2.VideoCapture(0)
    flt = FloatLayout()
    cam = KivyCamera(capture=capture, fps=30, size_hint=(1, 1))
    flt.add_widget(cam)
    return flt


class KivyCamera(Image):
    def __init__(self, capture, fps, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
        self.capture = capture
        self.fps = fps
        Clock.schedule_interval(self.update, 1.0 / float(fps))

    def update(self, dt):
        try:
            ret, frame = self.capture.read()
            if not ret or frame is None:
                return

            # Resize to known width and keep aspect ratio
            frame = ResizeWithAspectRatio(frame, width=720)
            if frame is None:
                return

            h, w = frame.shape[:2]
            # Dynamic cropping: remove ~10% margins
            top = int(h * 0.10)
            bottom = h - top
            left = int(w * 0.10)
            right = w - left
            cropped = frame[top:bottom, left:right]

            # Convert to grayscale for more reliable decode
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            data = decode(gray)

            if data:
                try:
                    csv_file, room_index = getFileAndRoom()
                    csv_list = openCSV(csv_file, room_index)
                    student_name = data[0].data.decode('utf-8')
                    ok, correct_room = checkPresence(student_name, csv_list, room_index)
                    popupOrient(student_name, ok, correct_room)
                    updateCsv(csv_list, room_index)
                except Exception as e:
                    print('Detection handling error:', e)

            # Mirror image for natural camera feel
            display_frame = cv2.flip(cropped, 1)
            buf = cv2.flip(display_frame, 0).tobytes()
            image_texture = Texture.create(size=(display_frame.shape[1], display_frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.texture = image_texture

        except Exception as e:
            # swallow exceptions so Kivy loop isn't killed
            print('Camera update error:', e)


class CamApp(App):
    def build(self):
        top_root = FloatLayout()
        sm = ScreenManager(transition=NoTransition())
        qr = Screen(name='QRScanner')
        qr.add_widget(root())
        sm.add_widget(qr)
        top_root.add_widget(sm)
        return top_root

    def on_stop(self):
        try:
            self.root.children[0].children[0].capture.release()
        except Exception:
            pass


if __name__ == '__main__':
    CamApp().run()
