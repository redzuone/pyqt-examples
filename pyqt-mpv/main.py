from PyQt6.QtCore import Qt, QObject, pyqtSlot, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QMainWindow, QApplication, QPushButton
from PyQt6.QtGui import QImage, QPixmap
import sys
# Add libmpv to path if needed
# import os
# os.environ['PATH'] = os.path.join('path', 'to', 'libmpv') + os.pathsep + os.environ['PATH']
import mpv

STREAM_URL = 'rtsp://192.168.0.2/stream'
FPS = 25


class MpvObject(QObject):
    def __init__(self, video_source: str) -> None:
        super().__init__()
        self.video_source = video_source
        self.is_playing = False

        self.main_widget = QWidget() # Need parent widget to hide/show MPV player
        self.main_widget.setWindowTitle('Embedded MPV Player')
        self.main_widget.resize(640, 480)
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        self.mpv_widget = QWidget()
        self.main_layout.addWidget(self.mpv_widget)
        self.mpv_widget.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.mpv_widget.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.main_widget.closeEvent = self.hide_widget

    def start(self) -> None:
        self.player = mpv.MPV(wid=str(int(self.mpv_widget.winId())),
            # These helps low-latency RTSP playback
            # profile='low-latency',
            # aid='no',
            # untimed=True,
            # speed=1.01,
            log_handler=print,)

        @self.player.property_observer('time-pos')
        def time_observer(_name, value):
            if value is None:
                self.is_playing = False
            else:
                self.is_playing = True
        self.player.play(self.video_source)

    def stop(self) -> None:
        if self.player is not None:
            self.player.terminate()
    
    def show_mpv_widget(self):
        self.main_widget.show()

    def hide_widget(self, event: None) -> None:
        self.main_widget.hide()
        event.ignore() # Prevent MainWindow from being uninteractable
    
    def screenshot_raw(self):
        """Modified function of MPV.screenshot_raw(). Returns res directly to skip color conversion."""
        res = self.player.command('screenshot-raw')
        if res['format'] != 'bgr0':
            raise ValueError('Screenshot in unknown format "{}". Currently, only bgr0 is supported.'
                    .format(res['format']))
        return res


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(640, 480)
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        
        self.mpv = MpvObject(STREAM_URL)
        self.play_btn = QPushButton('Play')
        self.main_layout.addWidget(self.play_btn)
        self.show_btn = QPushButton('Show')
        self.main_layout.addWidget(self.show_btn)
        self.capture_mpv_btn = QPushButton('Start capture')
        self.main_layout.addWidget(self.capture_mpv_btn)
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.label.setMinimumSize(1, 1)
        self.main_layout.addWidget(self.label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_screenshots)

        self.play_btn.clicked.connect(self.toggle_mpv_play)
        self.show_btn.clicked.connect(self.toggle_show_mpv)
        self.capture_mpv_btn.clicked.connect(self.toggle_capture)

    @pyqtSlot()
    def toggle_mpv_play(self) -> None:
        if self.mpv.is_playing:
            self.mpv.stop()
            self.play_btn.setText('Play')
        else:
            self.mpv.start()
            self.play_btn.setText('Stop')

    @pyqtSlot()
    def toggle_capture(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
            self.capture_mpv_btn.setText('Start capture')
        else:
            self.timer.start(1000 // FPS)
            self.capture_mpv_btn.setText('Stop capture')

    @pyqtSlot()
    def toggle_show_mpv(self) -> None:
        if self.mpv.main_widget.isVisible():
            self.mpv.main_widget.hide()
            self.show_btn.setText('Show')
        else:
            self.mpv.main_widget.show()
            self.show_btn.setText('Hide')
    
    def capture_screenshots(self):
        if not self.mpv.is_playing:
            return
        try:
            res = self.mpv.screenshot_raw()
        except Exception as e:
            return
        q_img = QImage(res['data'], res['stride'] // 4, res['h'], QImage.Format.Format_RGB32)
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(scaled_pixmap)

    def closeEvent(self, event) -> None:
        try:
            self.mpv.main_widget.close()
        except Exception as e:
            print(e)
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
