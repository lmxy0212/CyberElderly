import sys
import numpy as np
from pythonosc import dispatcher, osc_server
import threading
from collections import deque
from scipy.signal import welch
import pyqtgraph as pg
from PyQt5 import QtWidgets

# Configuration
ip = "0.0.0.0"
port = 5000
sampling_rate = 256  # Adjust based on your device's specifications
segment_length = 1  # Length of each segment in seconds
n_samples = segment_length * sampling_rate  # Number of samples in each segment

# EEG bands
eeg_bands = {'Delta': (0.5, 4),
             'Theta': (4, 8),
             'Alpha': (8, 12),
             'Beta': (12, 30),
             'Gamma': (30, 45)}

# Circular buffer to store EEG data
eeg_buffer = deque(maxlen=n_samples)

# Initialize a dictionary to store band powers
band_powers_history = {band: [] for band in eeg_bands}
max_history = 50  # Maximum number of data points to display on the plot

def eeg_handler(address: str, *args):
    eeg_buffer.extend(args)

def process_eeg_data():
    while True:
        if len(eeg_buffer) == n_samples:
            segment = np.array(list(eeg_buffer))
            # Apply FFT
            freqs, psd = welch(segment, sampling_rate, nperseg=n_samples)

            for band in eeg_bands:
                freq_ix = np.where((freqs >= eeg_bands[band][0]) &
                                   (freqs <= eeg_bands[band][1]))[0]
                band_power = np.sum(psd[freq_ix])
                band_power_dB = 10 * np.log10(band_power / 1)  # Reference power is 1 μV²/Hz
                band_powers_history[band].append(band_power_dB)
                if len(band_powers_history[band]) > max_history:
                    band_powers_history[band].pop(0)

            # Update plot
            for band in eeg_bands:
                curves[band].setData(list(range(max_history)), band_powers_history[band])

# Setup PyQtGraph
app = QtWidgets.QApplication(sys.argv)
win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle('Real-time EEG Band Powers')
plots = {}
curves = {}

for i, band in enumerate(eeg_bands):
    plots[band] = win.addPlot(title=band, row=i, col=0)
    curves[band] = plots[band].plot(pen=pg.mkPen(width=3))
    plots[band].setYRange(-30, 30)  # Set the y-axis range
    plots[band].setXRange(0, max_history)  # Set the x-axis range

if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/muse/eeg", eeg_handler)

    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    print("Listening on UDP port "+str(port))

    # Start a separate thread to process EEG data
    processing_thread = threading.Thread(target=process_eeg_data, daemon=True)
    processing_thread.start()

    # Start Qt event loop
    sys.exit(app.exec_())
