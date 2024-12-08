import configparser

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import requests

# Config
config_file = "config.ini"
config = configparser.ConfigParser()
config.read(config_file)


# Define URLs
main_url = "https://portal.dhivehinet.net.mv"
login_url = "https://portal.dhivehinet.net.mv/adsls/login_api"
daily_url = "https://portal.dhivehinet.net.mv/adsl/g/daily"
hourly_url = "https://portal.dhivehinet.net.mv/adsl/g/hourly"

# Define form data
form_data = {
    "_method": "POST",
    "data[adsl][username]": config.get('dhiraagu', 'username'),
    "data[adsl][password]": config.get('dhiraagu', 'password'),
}

# Telegram API
bot_token = config.get('telegram', 'bot_token')
chat_id = config.get('telegram', 'chat_id')
telegram_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"


def plot_data_transfer(json_data, output_file="data_transfer_overview.png"):
    # Convert JSON to DataFrame
    df = pd.DataFrame(json_data['data'])
    df['day'] = pd.to_datetime(df['day'])

    # Ensure numeric conversion
    df['o'] = pd.to_numeric(df['o'], errors='coerce')
    df['i'] = pd.to_numeric(df['i'], errors='coerce')
    df['hour'] = df['day'].dt.hour
    df['hour_formatted'] = df['hour'].apply(lambda x: f"{x:02d}:00")

    # Define function to format Y-axis
    def human_readable_size(y, _):
        if y >= 1_000:
            return f'{y / 1_000:.1f} GB'
        return f'{y:.1f} MB'

    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(df['hour'], df['o'], label='Download (o)', marker='o')
    plt.plot(df['hour'], df['i'], label='Upload (i)', marker='o')

    # Format x-axis with alternating labels
    alternate_labels = [label if idx % 2 == 0 else "" for idx, label in enumerate(df['hour_formatted'])]
    plt.xticks(df['hour'], alternate_labels, rotation=45)

    # Apply human-readable formatting to Y-axis
    plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(human_readable_size))

    # Chart details
    plt.title("Data Transfer Overview")
    plt.xlabel("Hour of the Day")
    plt.ylabel("Data Transferred")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xlim(0, 23)
    plt.ylim(0, max(df[['o', 'i']].max()) + 100)
    plt.legend()
    plt.tight_layout()

    # Save the plot to file
    plt.savefig(output_file, dpi=300)
    with open(output_file, 'rb') as photo:
        response = requests.post(telegram_url, data={'chat_id': chat_id}, files={'photo': photo})


def plot_daily_data(json_data, output_file="daily_data_overview.png"):
    # Convert JSON to DataFrame
    df = pd.DataFrame(json_data['data'])
    df['day'] = pd.to_datetime(df['day'])

    # Ensure numeric conversion
    df['o'] = pd.to_numeric(df['o'], errors='coerce')
    df['i'] = pd.to_numeric(df['i'], errors='coerce')

    # Define function to format Y-axis
    def human_readable_size(y, _):
        if y >= 1_000:
            return f'{y / 1_000:.1f} GB'
        return f'{y:.1f} MB'

    # Create the plot
    plt.figure(figsize=(12, 6))

    # Ensure graph starts from (0,0)
    plt.plot([df['day'].min()] + df['day'].tolist(), [0] + df['o'].tolist(), label='Download (o)', marker='o')
    plt.plot([df['day'].min()] + df['day'].tolist(), [0] + df['i'].tolist(), label='Upload (i)', marker='o')

    # Apply human-readable formatting to Y-axis
    plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(human_readable_size))

    # Chart details
    plt.title("Daily Data Transfer Overview")
    plt.xlabel("Date")
    plt.ylabel("Data Transferred")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(df['day'], df['day'].dt.strftime("%d %b"), rotation=45)

    # Add goal line if available
    if "goals" in json_data:
        goal = float(json_data["goals"])
        plt.axhline(goal, color='r', linestyle='--', label=f"Goal: {goal:,.1f} MB")

    plt.ylim(0, max(df[['o', 'i']].max()) + 1000)  # Add padding on y-axis
    plt.legend()
    plt.tight_layout()

    # Save the plot to file
    plt.savefig(output_file, dpi=300)
    # Send the image
    with open(output_file, 'rb') as photo:
        response = requests.post(telegram_url, data={'chat_id': chat_id}, files={'photo': photo})


# Create a session to persist cookies
session = requests.Session()

# Custom headers to simulate a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
}

session.get(main_url, headers=headers)


def get_hourly_data():
    data_response = session.get(hourly_url, headers=headers)

    if data_response.status_code == 200:
        print("Data fetched successfully.")
        data = data_response.json()
        plot_data_transfer(data)
    else:
        print("Failed to fetch data:", data_response.status_code)
    pass


def get_daily_data():
    data_response = session.get(daily_url, headers=headers)

    if data_response.status_code == 200:
        print("Data fetched successfully.")
        data = data_response.json()
        plot_daily_data(data)
    else:
        print("Failed to fetch data:", data_response.status_code)
    pass


if __name__ == "__main__":
    # Send login request
    login_response = session.post(login_url, data=form_data, headers=headers)

    # Check if login was successful
    if login_response.status_code == 200:
        print("Login successful.")
    else:
        print("Login failed:", login_response.status_code)
        print("Response:", login_response.text)

    get_hourly_data()
    get_daily_data()
