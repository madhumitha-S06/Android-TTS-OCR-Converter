
import os
import threading

import pytesseract
from PIL import Image, ImageOps, ImageEnhance

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

Window.size = (430, 760)

# Tesseract installation path on Windows
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

KV = """
BoxLayout:
    orientation: "vertical"
    padding: 16
    spacing: 10

    Label:
        text: "TTS & OCR Converter"
        font_size: "24sp"
        bold: True
        size_hint_y: None
        height: "55dp"

    Label:
        text: "Extract text from printed documents"
        size_hint_y: None
        height: "30dp"

    Button:
        text: "Upload Image"
        size_hint_y: None
        height: "48dp"
        on_release: app.upload_image()

    TextInput:
        id: extracted_text
        hint_text: "Extracted text will appear here..."
        multiline: True

    Spinner:
        id: language
        text: "English"
        values: ["English", "Hindi", "Tamil", "French", "Spanish"]
        size_hint_y: None
        height: "48dp"

    Button:
        text: "Read Aloud"
        size_hint_y: None
        height: "48dp"
        on_release: app.read_aloud()

    Button:
        text: "Stop Speech"
        size_hint_y: None
        height: "48dp"
        on_release: app.stop_speech()

    Label:
        id: status
        text: "Ready"
        size_hint_y: None
        height: "45dp"
"""

class TTSOCRApp(App):

    def build(self):
        self.speech_engine = None
        return Builder.load_string(KV)

    def upload_image(self):
        chooser = FileChooserListView(
            filters=["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif"]
        )

        layout = BoxLayout(
            orientation="vertical",
            spacing=8,
            padding=8
        )

        layout.add_widget(chooser)

        buttons = BoxLayout(
            size_hint_y=None,
            height="48dp",
            spacing=8
        )

        popup = Popup(
            title="Select an image",
            content=layout,
            size_hint=(0.95, 0.9)
        )

        cancel = Button(text="Cancel")
        select = Button(text="Select")

        cancel.bind(on_release=popup.dismiss)

        def choose_file(_):
            if chooser.selection:
                path = chooser.selection[0]
                popup.dismiss()
                self.extract_text(path)

        select.bind(on_release=choose_file)

        buttons.add_widget(cancel)
        buttons.add_widget(select)
        layout.add_widget(buttons)

        popup.open()

    def extract_text(self, path):
        self.root.ids.status.text = "Extracting text..."

        threading.Thread(
            target=self._ocr_worker,
            args=(path,),
            daemon=True
        ).start()

    def _ocr_worker(self, path):
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source)
                image = image.convert("RGB")
                image = ImageOps.grayscale(image)
                image = ImageEnhance.Contrast(image).enhance(1.5)

                text = pytesseract.image_to_string(
                    image,
                    lang="eng"
                ).strip()

            Clock.schedule_once(
                lambda dt: self.show_result(text), 0
            )

        except Exception as exc:
            message = str(exc)
            Clock.schedule_once(
                lambda dt: self.show_error(message), 0
            )

    def show_result(self, text):
        self.root.ids.extracted_text.text = text
        self.root.ids.status.text = (
            "Text extracted successfully."
            if text else "No text found. Try a clearer image."
        )

    def show_error(self, message):
        self.root.ids.status.text = "OCR error: " + message

    def read_aloud(self):
        text = self.root.ids.extracted_text.text.strip()

        if not text:
            self.root.ids.status.text = "Extract text first."
            return

        try:
            import pyttsx3

            if self.speech_engine is None:
                self.speech_engine = pyttsx3.init()

            self.speech_engine.say(text)
            self.speech_engine.runAndWait()
            self.root.ids.status.text = "Speech completed."

        except Exception as exc:
            self.root.ids.status.text = "Speech error: " + str(exc)

    def stop_speech(self):
        if self.speech_engine:
            self.speech_engine.stop()

        self.root.ids.status.text = "Speech stopped."

    def on_stop(self):
        if self.speech_engine:
            self.speech_engine.stop()


if __name__ == "__main__":
    TTSOCRApp().run()
