import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# Define overall min and max values
ice_min = 0.0535073855075483
ice_max = 5.797174348220309
stress_min = -222.45067603158407
stress_max = 4877.199612025589

ice_min = 0.148615902667383 
ice_max = 4.0031659201573895 
stress_min = 160.67041584039157 
stress_max =  5599.420633107831 

ice_min = 0.0225544175730969 
ice_max = 2
stress_min = -100000
stress_max =  533330


def process_ice_stress_data(input_file):
    # Read the CSV file using Pandas
    data = pd.read_csv("Cleaned/" +input_file)

    # Extract ICE and Stress Level columns as NumPy arrays
    ice_values = data['Engagement Index'].to_numpy()
    stress_values = data['Stress Level'].to_numpy()

    # Calculate statistics using NumPy
    if ice_values.size > 0 and stress_values.size > 0:
        ice_avg, ice_min, ice_max = np.mean(ice_values), np.min(ice_values), np.max(ice_values)
        stress_avg, stress_min, stress_max = np.mean(stress_values), np.min(stress_values), np.max(stress_values)

        # Print the statistics
        print(f"ICE - Average: {ice_avg}, Min: {ice_min}, Max: {ice_max}")
        print(f"Stress Level - Average: {stress_avg}, Min: {stress_min}, Max: {stress_max}")
    else:
        print("No valid data found in file.")

def normalize_values(input_file, output_file, ice_min, ice_max, stress_min, stress_max):
    # Read the CSV file
    data = pd.read_csv("Cleaned/" +input_file)

    # Normalization function scaled to 0-100
    def normalize(value, min_value, max_value):
        return 100 * (value - min_value) / (max_value - min_value) if max_value != min_value else 0

    # Normalize ICE and Stress Level columns
    data['Normalized ICE'] = data['Engagement Index'].apply(lambda x: normalize(x, ice_min, ice_max))
    data['Normalized Stress Level'] = data['Stress Level'].apply(lambda x: normalize(x, stress_min, stress_max))

    # Write the results to a new CSV file
    data.to_csv(output_file, index=False)

def plot_engagement_and_stress(input_file):
    # Read the CSV file
    data = pd.read_csv(input_file)

    # Convert 'Timestamp' to datetime for better plotting
    data['Timestamp'] = pd.to_datetime(data['Timestamp'])

    # Set the 'Timestamp' as the index of the dataframe
    data.set_index('Timestamp', inplace=True)

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(data['Normalized ICE'], label='Engagement Index', color='blue')
    plt.plot(data['Normalized Stress Level'], label='Stress Level', color='red')

    # Adding title and labels
    plt.title('Engagement Index and Stress Level Over Time')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()

    # Set Y-axis limits
    plt.ylim(0, 100)

    # Show plot
    plt.show()


    

if __name__ == "__main__":
    # input_csv = input("Enter the name of the input CSV file: ")
    # process_ice_stress_data(input_csv)
    input_csv = input("Enter the name of the input CSV file: ")

    output_csv = input_csv[0:-4]+'_normalized.csv'
    normalize_values(input_csv, output_csv, ice_min, ice_max, stress_min, stress_max)
    
    plot_engagement_and_stress(output_csv)
