from datetime import datetime
from pythonosc import dispatcher, osc_server
import numpy as np
from scipy.signal import welch
from collections import deque
import threading
import time

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

# Buffers for storing last 10 seconds of band averages
alpha_buffer = deque(maxlen=10)
beta_buffer = deque(maxlen=10)
theta_buffer = deque(maxlen=10)

def eeg_handler(address: str, *args):
    # Assuming TP9 data is the first value in args
    tp9_data = args[0]
    eeg_buffer.append(tp9_data)

def normalize(value, min_value, max_value):
    # Scale ICE to 0-100 range
    return 100 * (value - min_value) / (max_value - min_value)

def process_eeg_data():
    last_print_time = time.time()
    # min_ice = # Define the minimum expected ICE value
    # max_ice = # Define the maximum expected ICE value

    while True:
        if len(eeg_buffer) == n_samples:
            segment = np.array(list(eeg_buffer))
            # Apply FFT
            freqs, psd = welch(segment, sampling_rate, nperseg=n_samples)

            band_powers = {}
            for band in eeg_bands:
                freq_ix = np.where((freqs >= eeg_bands[band][0]) &
                                   (freqs <= eeg_bands[band][1]))[0]
                band_power = np.sum(psd[freq_ix])
                band_power_dB = 10 * np.log10(band_power / 1)  # Reference power is 1 μV²/Hz
                band_powers[band] = band_power_dB

            # Update alpha, beta, and theta buffers
            alpha_buffer.append(band_powers['Alpha'])
            beta_buffer.append(band_powers['Beta'])
            theta_buffer.append(band_powers['Theta'])

            current_time = time.time()
            if current_time - last_print_time >= 10:
                if len(alpha_buffer) == alpha_buffer.maxlen:
                    avg_alpha = np.mean(alpha_buffer)
                    avg_beta = np.mean(beta_buffer)
                    avg_theta = np.mean(theta_buffer)

                    # Calculate ICE
                    ice = avg_beta / (avg_alpha + avg_theta)

                    # Normalize ICE
                    # normalized_ice = normalize(ice, min_ice, max_ice)
                    # normalized_ice = max(0, min(100, normalized_ice))  # Clamping to 0-100 range

                    # print(f"Normalized Index of Cognitive Engagement (ICE): {normalized_ice}")
                    print(f"Index of Cognitive Engagement (ICE) over previous 10 seconds: {ice}")
                    last_print_time = current_time

if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/muse/eeg", eeg_handler)

    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    print("Listening on UDP port " + str(port))

    # Start a separate thread to process EEG data
    processing_thread = threading.Thread(target=process_eeg_data)
    processing_thread.start()

    server.serve_forever()
