import uuid
import requests
import threading
import time

class UserTracker:
    """
    Manages user tracking, including sending heartbeats to a server to monitor online status.
    """
    def __init__(self, config_manager, logger):
        self.config_manager = config_manager
        self.logger = logger
        self.user_id = self.get_or_create_user_id()
        
        config = self.config_manager.load_config()
        self.base_url = config.get("base_url", "https://violetwing.vercel.app/api")
        self.heartbeat_interval = config.get("heartbeat_interval", 120)
        
        self.session = requests.Session()
        self.heartbeat_thread = None
        self.stop_event = threading.Event()

    def get_or_create_user_id(self):
        try:
            config = self.config_manager.load_config()
            user_id = config.get("user_id")
            if not user_id:
                user_id = str(uuid.uuid4())
                config["user_id"] = user_id
                self.config_manager.save_config(config)
                self.logger.info(f"Generated new user_id: {user_id}")
            return user_id
        except Exception as e:
            self.logger.error(f"Error getting or creating user_id: {e}")
            return str(uuid.uuid4())

    def send_heartbeat(self):
        while not self.stop_event.is_set():
            try:
                response = self.session.post(f"{self.base_url}/heartbeat", json={"user_id": self.user_id}, timeout=10)
                if response.status_code == 200:
                    self.logger.debug("Heartbeat sent successfully.")
                else:
                    self.logger.warning(f"Failed to send heartbeat. Status: {response.status_code}, Response: {response.text}")
            except requests.RequestException as e:
                self.logger.error(f"Error sending heartbeat: {e}")
                time.sleep(1)
            
            self.stop_event.wait(self.heartbeat_interval)

    def get_online_users(self):
        if not self.base_url:
            return None
        
        try:
            response = self.session.get(f"{self.base_url}/online-users", timeout=5)
            if response.status_code == 200:
                return response.json().get("count")
            else:
                self.logger.warning(f"Failed to get online users. Status: {response.status_code}")
                return None
        except requests.RequestException as e:
            self.logger.error(f"Error getting online users: {e}")
            return None

    def start_heartbeat(self):
        if self.heartbeat_thread is None or not self.heartbeat_thread.is_alive():
            if not hasattr(self.session, 'adapters') or not self.session.adapters:
                self.session = requests.Session()
            
            self.stop_event.clear()
            self.heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
            self.heartbeat_thread.start()
            self.logger.debug("Heartbeat thread started.")

    def stop_heartbeat(self):
        self.stop_event.set()
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)
        self.session.close()
        self.logger.debug("Heartbeat thread stopped.")
