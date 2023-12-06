from datetime import datetime
from pythonosc import dispatcher, osc_server
import numpy as np
from scipy.signal import welch
from collections import deque
import threading
import time
import csv
import keyboard

# Configuration
ip = "0.0.0.0"
port = 5000
sampling_rate = 256  # Adjust this based on your device's specifications
segment_length = 5  # Length of each segment in seconds for sliding window
n_samples = segment_length * sampling_rate  # Number of samples in each segment
calc_interval = 15  # Interval for calculating normalized engagement score

# EEG bands
eeg_bands = {'Delta': (0.5, 4),
             'Theta': (4, 8),
             'Alpha': (8, 12),
             'Beta': (12, 30),
             'Gamma': (30, 45)}

# Circular buffer to store EEG data
eeg_buffer = deque(maxlen=n_samples)

# Buffers for storing last 15 seconds of band averages
alpha_buffer = deque(maxlen=calc_interval)
beta_buffer = deque(maxlen=calc_interval)
theta_buffer = deque(maxlen=calc_interval)

# Define min and max ICE values
min_ice = 0  # Update with appropriate value
max_ice = 1  # Update with appropriate value

# Prompt for file name
file_name = input("Enter the name of the file to save data: ")+".csv"
csv_file = open("ICEData/"+file_name, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Timestamp', 'Engagement Index'])

def eeg_handler(address: str, *args):
    # Assuming TP9 data is the first value in args
    tp9_data = args[0]
    eeg_buffer.append(tp9_data)

def normalize(value, min_value, max_value):
    # Scale value to 0-100 range
    return 100 * (value - min_value) / (max_value - min_value)

def process_eeg_data():
    last_band_calc_time = time.time()
    last_ice_calc_time = time.time()
    recording = True

    # Buffers for storing last 5 seconds of band averages
    short_term_alpha_buffer = deque(maxlen=5)
    short_term_beta_buffer = deque(maxlen=5)
    short_term_theta_buffer = deque(maxlen=5)

    while recording:
        if len(eeg_buffer) == n_samples:
            segment = np.array(list(eeg_buffer))
            # Apply FFT
            freqs, psd = welch(segment, sampling_rate, nperseg=n_samples)

            band_powers = {}
            for band in eeg_bands:
                freq_ix = np.where((freqs >= eeg_bands[band][0]) &
                                   (freqs <= eeg_bands[band][1]))[0]
                band_power = np.sum(psd[freq_ix])
                band_powers[band] = band_power

            # Update short term buffers
            short_term_alpha_buffer.append(band_powers['Alpha'])
            short_term_beta_buffer.append(band_powers['Beta'])
            short_term_theta_buffer.append(band_powers['Theta'])

            current_time = time.time()
            if current_time - last_band_calc_time >= 5:
                # Calculate 5-second average for each band
                avg_alpha_5s = np.mean(list(short_term_alpha_buffer))
                avg_beta_5s = np.mean(list(short_term_beta_buffer))
                avg_theta_5s = np.mean(list(short_term_theta_buffer))

                # Update the long-term buffers with the 5-second averages
                alpha_buffer.append(avg_alpha_5s)
                beta_buffer.append(avg_beta_5s)
                theta_buffer.append(avg_theta_5s)

                print(f"5-second average Alpha: {avg_alpha_5s}, Beta: {avg_beta_5s}, Theta: {avg_theta_5s}")
                last_band_calc_time = current_time

            if current_time - last_ice_calc_time >= calc_interval:
                # Calculate ICE based on 15-second averages
                avg_alpha_15s = np.mean(list(alpha_buffer))
                avg_beta_15s = np.mean(list(beta_buffer))
                avg_theta_15s = np.mean(list(theta_buffer))

                ice = avg_beta_15s / (avg_alpha_15s + avg_theta_15s)
                normalized_ice = normalize(ice, min_ice, max_ice)
                normalized_ice = max(0, min(100, normalized_ice))  # Clamping to 0-100 range

                print(f"Normalized Index of Cognitive Engagement (ICE) over previous 15 seconds: {normalized_ice}")
                csv_writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), normalized_ice])

                last_ice_calc_time = current_time

        if keyboard.is_pressed('enter'):
            print("Enter key pressed. Stopping recording.")
            recording = False
            break

        time.sleep(0.1)  # To avoid high CPU usage

    csv_file.close()
    

if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/muse/eeg", eeg_handler)

    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    print("Listening on UDP port " + str(port))

    # Start a separate thread to process EEG data
    processing_thread = threading.Thread(target=process_eeg_data)
    processing_thread.start()
    server.serve_forever()

    
