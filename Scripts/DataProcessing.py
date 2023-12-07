import csv
import numpy as np

def calculate_ice_and_stress(input_file, output_file):
    with open("ABTData/" +input_file, mode='r') as infile, open(output_file, mode='w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)

        # Write headers to the output file
        writer.writerow(['Timestamp', 'Engagement Index', 'Stress Level'])

        for row in reader:
            try:
                alpha = float(row['Alpha'])
                beta = float(row['Beta'])
                theta = float(row['Theta'])

                # Calculate ICE and Stress Level
                ice = beta / (alpha + theta) if (alpha + theta) != 0 else 0
                stress_level = beta - alpha

                # Write the calculated values to the output file
                writer.writerow([row['Timestamp'], ice, stress_level])
            except ValueError:
                # Handle the exception if the data is not a valid float
                print(f"Invalid data encountered in row: {row}")

if __name__ == "__main__":
    input_csv = input("Enter the name of the input CSV file: ")
    output_csv = input("Enter the name of the output CSV file: ")
    calculate_ice_and_stress(input_csv, output_csv)
