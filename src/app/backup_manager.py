import hashlib
import os
import shutil
import time
import threading
from logging_config import logger

class BackupManager:
    def __init__(self, db_path="states.db", backup_interval=3600, backup_folder="backups"):
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
        """
        Inizializza il BackupManager.
        
        :param db_path: percorso del database da salvare
        :param backup_interval: intervallo in secondi per eseguire il backup (default: 3600 secondi = 1 ora)
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
        :param backup_folder: cartella dove salvare i backup
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
        """
        self.db_path = db_path
        self.backup_interval = backup_interval
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
        self.backup_folder = backup_folder
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
        self.running = False
        self.thread = None

    def start(self):
        """Avvia il processo di backup periodico in un thread separato."""
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("BackupManager avviato.")

    def _run(self):
        """Loop interno per eseguire i backup a intervalli regolari."""
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
        while self.running:
            timestamp = int(time.time())
            backup_file = f"{self.backup_folder}/states_{timestamp}.db"
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
            try:
                shutil.copy(self.db_path, backup_file)
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
                logger.info("Backup creato: %s", backup_file)
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
            except Exception as e:
                logger.error("Errore nel backup del database: %s", e)
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
            time.sleep(self.backup_interval)
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()

    def stop(self):
        """Ferma il processo di backup."""
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("BackupManager fermato.")

if __name__ == '__main__':
    # Esempio di test: avvia il BackupManager per 5 secondi
    bm = BackupManager(db_path="states.db", backup_interval=3600)
            # TODO: compute checksum and implement retention policy
            # checksum = hashlib.md5(open(backup_path,'rb').read()).hexdigest()
    bm.start()
    time.sleep(5)
    bm.stop()