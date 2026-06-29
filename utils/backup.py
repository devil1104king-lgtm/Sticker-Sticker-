import os
import shutil
import time
from telegram.ext import ContextTypes
from config import Config
from utils.logger import log

async def backup_database_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job to automatically backup the SQLite database every 12 hours."""
    try:
        if not os.path.exists(Config.DATABASE_NAME):
            return
            
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{backup_dir}/backup_{timestamp}.sqlite"
        
        shutil.copy2(Config.DATABASE_NAME, backup_filename)
        log.info(f"Automatic backup created: {backup_filename}")
        
        # Keep only last 5 backups
        backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.sqlite')])
        while len(backups) > 5:
            os.remove(os.path.join(backup_dir, backups.pop(0)))
            
    except Exception as e:
        log.error(f"Error during automatic backup: {e}")
      
