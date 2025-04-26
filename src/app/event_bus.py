import threading

class EventBus:
    def __init__(self):
        self.listeners = {}
        self.lock = threading.Lock()

    def subscribe(self, event_name, callback):
        with self.lock:
            self.listeners.setdefault(event_name, []).append(callback)

    def publish(self, event_name, data=None):
        with self.lock:
            listeners = list(self.listeners.get(event_name, []))
        for callback in listeners:
            try:
                callback(data)
            except Exception as e:
                print(f"Errore nel listener per {event_name}: {e}")

event_bus = EventBus()