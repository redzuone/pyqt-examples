from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout
import pyqtgraph as pg
import sys

class GraphWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.resize(640, 480)
        self.setWindowTitle('Graph')
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        self.plot_widget = pg.PlotWidget()
        main_layout.addWidget(self.plot_widget)
        self.region = pg.LinearRegionItem([5, 7])
        self.plot_widget.addItem(self.region)
        
        self.plot_locked = False
        self.plot_widget.setXRange(0, 10)
        self.region.sigRegionChanged.connect(self.region_changed)
        self.previous_region = self.region.getRegion()

        self.show()

    def region_changed(self) -> None:
        if self.plot_locked:
            return
        self.plot_locked = True
        region = self.region.getRegion()
        print(f'New region input: {region}')
        left_handle, right_handle = region
        previous_left_handle, previous_right_handle = self.previous_region
        left_handle_changed = (left_handle != previous_left_handle)
        right_handle_changed = (right_handle != previous_right_handle)
        # Only resize symmetrically if one side changed
        if ((not left_handle_changed) and right_handle_changed):
            # Right handle changed, changing left handle
            self.new_region = (left_handle - (right_handle - previous_right_handle), right_handle)
            self.region.setRegion(self.new_region)
        elif (left_handle_changed and (not right_handle_changed)):
            # Left handle changed, changing right handle
            self.new_region = (left_handle, right_handle + (previous_left_handle - left_handle))
            self.region.setRegion(self.new_region)
        self.previous_region = region
        self.plot_locked = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GraphWidget()
    sys.exit(app.exec())
