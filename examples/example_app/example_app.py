import random
import PyQt5.QtCore
from PyQt5 import QtWidgets, uic
import adv_prodcon
import matplotlib
from matplotlib import animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
import time
import math

Ui_MainWindow, QMainWindow = uic.loadUiType("example_app_layout.ui")


class DataProducer(adv_prodcon.Producer):
    @staticmethod
    def work(shared_var, state, message_pipe, *args):
        data = (math.sin(time.time()*10) + 1)/2 + random.random()/10
        timestamp = time.time()
        return {"data": data, "timestamp": timestamp}


# Data consumer acts as a buffer so we can pass new data to our UI process at our leisure
class DataConsumer(adv_prodcon.Consumer, PyQt5.QtCore.QObject):
    new_data = PyQt5.QtCore.pyqtSignal(list)

    def __init__(self, *args, **kwargs):
        PyQt5.QtCore.QObject.__init__(self)
        adv_prodcon.Consumer.__init__(self, *args, **kwargs)

    @staticmethod
    def work(items, shared_var, state, message_pipe, *args):
        return items

    def on_result_ready(self, result):
        self.new_data.emit(result)


plot_config = {
    "num_points": 300
}


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.plot_axes = None
        self.ani = None
        self.plot_data = {"data": [], "times": []}
        self.add_plot()

        self.producer = DataProducer(work_timeout=0.00001)
        self.consumer = DataConsumer(work_timeout=0.01, max_buffer_size=1000, lossy_queue=True)
        self.producer.set_subscribers([self.consumer.get_work_queue()])

        self.startButton.clicked.connect(self.start)
        self.stopButton.clicked.connect(self.stop)

        self.consumer.new_data.connect(lambda result: self.update_plot_data(result))

        self.start_time = time.time()

    def start(self):
        self.startButton.setVisible(False)
        self.stopButton.setVisible(True)

        self.clear_plot()

        self.producer.start_new()
        self.consumer.start_new()
        self.ani = animation.FuncAnimation(self.plot_axes.figure, update_plot,
                                           fargs=(self.plot_data, self.plot_axes), interval=50)
        self.plot_axes.figure.canvas.draw()

    def stop(self):
        self.startButton.setVisible(True)
        self.stopButton.setVisible(False)

        self.producer.set_stopped()
        self.consumer.set_stopped()
        self.ani.pause()
        self.ani = None

    def add_plot(self):
        self.placeholderWidget.setParent(None)
        self.placeholderWidget.deleteLater()

        canvas = FigureCanvas(matplotlib.figure.Figure())
        self.plot_axes = canvas.figure.subplots()

        self.verticalLayout.addWidget(canvas)

    def clear_plot(self):
        for line in self.plot_axes.lines:
            line.remove()
        self.plot_data = {"data": [], "times": []}
        self.plot_axes.figure.canvas.draw()

    def update_plot_data(self, items):
        new_data = [item["data"] for item in items]
        new_times = [item["timestamp"]-self.start_time for item in items]

        data = self.plot_data["data"]
        times = self.plot_data["times"]

        for d in new_data:
            data.append(d)

        for t in new_times:
            times.append(t)

        self.plot_data["data"] = data[-1 * plot_config["num_points"]:]
        self.plot_data["times"] = times[-1 * plot_config["num_points"]:]


def update_plot(i, data, axes):
    axes.clear()
    line = axes.plot(data["times"], data["data"])
    axes.set_ylim(0, 1.1)
    return line


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    main_window = MainWindow()
    main_window.setWindowTitle("Example App")
    main_window.show()
    app.exec()
