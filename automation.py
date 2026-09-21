"""
Планировщик автоматического запуска ETL и бэкапов.
"""
import schedule
import time
import shutil
import os
import logging
from datetime import datetime
from config import DB_PATH, BACKUP_DIR, LOG_PATH
from etl_pipeline import run_full_etl
from quality_control import run_audit

logger = logging.getLogger(__name__)


def job_etl():
    logger.info("═══ АВТОЗАПУСК ETL ═══")
    try:
        run_full_etl(migrate=False)
        run_audit()
    except Exception as e:
        logger.error(f"Ошибка в ETL: {e}", exc_info=True)


def job_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"attenuators_{ts}.db")
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, dst)
        logger.info(f"Бэкап создан: {dst}")


def start_scheduler():
    logger.info("Планировщик запущен.")
    schedule.every().day.at("02:00").do(job_etl)
    schedule.every().sunday.at("03:00").do(job_backup)
    # Для тестирования: schedule.every(60).seconds.do(job_etl)

    while True:
        schedule.run_pending()
        time.sleep(60)