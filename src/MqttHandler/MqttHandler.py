import os
import csv
import threading
from datetime import datetime, timezone
from dotenv import load_dotenv
from paho.mqtt import client as mqtt

class MissingEnvironmentVariableError(Exception):
    """Custom exception for missing or empty environment variables."""
    pass

class MqttHandler:
    _instance = None

    def __new__(cls, env: str = '.env', temp_csv_file: str = './log/temp.csv'):
        if cls._instance is None:
            cls._instance = super(MqttHandler, cls).__new__(cls)
            cls._instance._initialize(env, temp_csv_file)  # Initialize the instance
        return cls._instance

    def _initialize(self, env: str, temp_csv_file: str):
        load_dotenv(env)
        self.temp_csv_file: str = temp_csv_file
        self.mqtt_client: mqtt = mqtt.Client()
        self.broker_addr: tuple[str, int] = tuple((self.__get_env_var('MQTTBROKER').split(":")[0], int(
            self.__get_env_var('MQTTBROKER').split(":")[1])))
        self.search_key = self.__get_env_var('TAVILY_API_KEY')
        self._topics: dict = {
            "temp": self.__get_env_var('TEMP'),
            "disp": self.__get_env_var('DISPLAY'),
            "device1": self.__get_env_var('DEVICE1'),
            "device2": self.__get_env_var('DEVICE2'),
        }
        self.temperature_buf: float
        self.__initialize_csv(self.temp_csv_file)
        self.__setup()

    @staticmethod
    def __get_env_var(var_name: str) -> str:
        """Retrieves and checks that an environment variable is set and not empty."""
        value = os.getenv(var_name)
        if not value:
            raise MissingEnvironmentVariableError(f"Environment variable '{var_name}' is not set or is empty.")
        return value

    @staticmethod
    def __initialize_csv(temp_csv_file):
        try:
            with open(temp_csv_file, "x", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Temperature (°C)"])
        except FileExistsError:
            pass

    def __setup(self):
        self.mqtt_client.enable_logger()
        self.mqtt_client.on_connect = self.__on_connect
        self.mqtt_client.on_message = self.__on_message
        self.mqtt_client.connect(self.broker_addr[0], port=self.broker_addr[1])
        self.mqtt_client.loop_start()

    def __on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            print(f"Connected to MQTT broker at {self.broker_addr[0]}:{self.broker_addr[1]}")
            self.mqtt_client.subscribe(self._topics["temp"])  # Subscribe to the topic
        else:
            print(f"Failed to connect, return code {rc}")

    def __on_message(self, client, userdata, message):
        if message.topic == self._topics["temp"]:
            temperature = message.payload.decode("utf-8")
            self.temperature_buf = float(temperature)
            timestamp = datetime.now(timezone.utc).isoformat()
            with open(self.temp_csv_file, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, temperature])
            # print(f"Logged: {timestamp}, {temperature}°C")

    def get_temperature(self) -> float:
        return self.temperature_buf

    def set_display(self, char: str) -> None:
        # print(f"Sending the letter '{char}' to the topic '{self._topics['disp']}'.")
        self.mqtt_client.publish("esp32/display", char, qos=1)

    def device1(self, state: bool, **kwargs) -> bool:
        payload = "on" if state else "off"
        self.mqtt_client.publish(self._topics['device1'], payload, qos=1)
        return False if state else True

    def device2(self, state: bool, **kwargs) -> bool:
        payload = "on" if state else "off"
        self.mqtt_client.publish(self._topics['device2'], payload, qos=1)
        return state