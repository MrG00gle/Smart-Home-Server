import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from src.MqttHandler.MqttHandler import MqttHandler

mqtt = MqttHandler()
device_flags =[False, False]

def toggle_ui_device1() -> None:
    device_flags[0] = False if device_flags[0] else True
    mqtt.device1(state=device_flags[0])

def toggle_ui_device2() -> None:
    device_flags[1] = False if device_flags[1] else True
    mqtt.device2(state=device_flags[1])

def filter_data(time_range):
    # Predefined path to the CSV file
    csv_path = './log/temp.csv'

    # Load the CSV data
    df = pd.read_csv(csv_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Remove timezone information from 'Timestamp' column to make it naive
    df['Timestamp'] = df['Timestamp'].dt.tz_localize(None)

    now = datetime.now()  # Get the current naive datetime
    if time_range == "Last 1 Hour":
        start_time = now - timedelta(hours=1)
    elif time_range == "Last 6 Hours":
        start_time = now - timedelta(hours=6)
    elif time_range == "Last 12 Hours":
        start_time = now - timedelta(hours=12)
    else:
        start_time = now - timedelta(hours=1)  # Default to last 1 hour

    # Filter the data based on the selected time range
    filtered_df = df[df['Timestamp'] >= start_time]
    return filtered_df


def update_plot(time_range):
    filtered_df = filter_data(time_range)

    # Create a matplotlib plot
    fig, ax = plt.subplots()
    ax.plot(filtered_df['Timestamp'], filtered_df['Temperature (°C)'], label="Temperature")

    ax.set_title(f"Temperature Over Time ({time_range})")
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Temperature (°C)')
    ax.legend()

    # Return the figure to gr.Plot()
    return fig