from redlock import Redlock
import json
from kafka import KafkaProducer, KafkaConsumer
from logging_config import logger
import threading

class AdvancedClusterManager:
    def __init__(self, brokers=["kafka:9092"], topic="engine_state", group_id="engine_cluster"):
        self.brokers = brokers
        self.topic = topic
        self.group_id = group_id
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.brokers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.brokers,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            logger.info("KafkaProducer e KafkaConsumer inizializzati.")
        except Exception as e:
            logger.error("Errore nell'inizializzazione di Kafka: %s", e)
            self.producer = None
            self.consumer = None
        self.running = False
        self.thread = None

    def broadcast_state(self, state):
        if self.producer:
            try:
                self.producer.send(self.topic, state)
                self.producer.flush()
                logger.info("Stato inviato al cluster tramite Kafka: %s", state)
            except Exception as e:
                logger.error("Errore nell'invio dello stato tramite Kafka: %s", e)
        else:
            logger.info("Fallback cluster: stato: %s", state)

    def listen_cluster(self, callback):
        if not self.consumer:
            logger.error("KafkaConsumer non inizializzato.")
            return
        for message in self.consumer:
            try:
                logger.info("Messaggio ricevuto dal cluster: %s", message.value)
                callback(message.value)
            except Exception as e:
                logger.error("Errore nel processing del messaggio: %s", e)
            if not self.running:
                break

    def start_listening(self, callback):
        self.running = True
        self.thread = threading.Thread(target=self.listen_cluster, args=(callback,), daemon=True)
        self.thread.start()

    def stop_listening(self):
        self.running = False
        if self.thread:
            self.thread.join()

advanced_cluster_manager = AdvancedClusterManager()
# Leader election stub using Redis lock
from redis import Redis
redis_client = Redis()

def elect_leader():
    lock = redis_client.lock("engine_leader", timeout=60)
    if lock.acquire(blocking=False):
        return True
    return False
