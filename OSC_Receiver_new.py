from datetime import datetime
from pythonosc import dispatcher, osc_server
import numpy as np
from scipy.signal import welch
from collections import deque
import threading

# Configuration
ip = "0.0.0.0"
port = 5000
sampling_rate = 256  # Adjust this based on your device's specifications
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

def eeg_handler(address: str, *args):
    eeg_buffer.extend(args)

def process_eeg_data():
    while True:
        if len(eeg_buffer) == n_samples:
            segment = np.array(list(eeg_buffer))
            # Apply FFT
            freqs, psd = welch(segment, sampling_rate, nperseg=n_samples)

            band_powers = {}
            # for band in eeg_bands:
            #     freq_ix = np.where((freqs >= eeg_bands[band][0]) &
            #                        (freqs <= eeg_bands[band][1]))[0]
            #     band_powers[band] = np.sum(psd[freq_ix])
            for band in eeg_bands:
                freq_ix = np.where((freqs >= eeg_bands[band][0]) &
                                   (freqs <= eeg_bands[band][1]))[0]
                band_power = np.sum(psd[freq_ix])
                band_power_dB = 10 * np.log10(band_power / 1)  # Reference power is 1 μV²/Hz
                band_powers[band] = band_power_dB
            print(f"Band powers: {band_powers}")

if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/muse/eeg", eeg_handler)

    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    print("Listening on UDP port "+str(port))

    # Start a separate thread to process EEG data
    processing_thread = threading.Thread(target=process_eeg_data)
    processing_thread.start()

    server.serve_forever()
