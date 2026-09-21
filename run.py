#!/usr/bin/env python3
"""
Точка входа. Запуск:
  python run.py migrate    — создать схему + мигрировать CSV
  python run.py etl        — запустить полный ETL
  python run.py audit      — аудит качества
  python run.py seed       — загрузить только seed-данные
  python run.py stats      — статистика по БД
  python run.py auto       — запустить планировщик
  python run.py pdf <file> — извлечь данные из PDF
"""
import sys
import os
import logging

# Настраиваем логирование
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import LOG_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("run")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "migrate":
        from db_manager import get_connection, create_schema, migrate_csv, count_records
        conn = get_connection()
        create_schema(conn)
        n = migrate_csv(conn)
        logger.info(f"Мигрировано {n} записей. Всего: {count_records(conn)}")
        conn.close()

    elif cmd == "etl":
        from etl_pipeline import run_full_etl
        run_full_etl(migrate=False)

    elif cmd == "seed":
        from etl_pipeline import etl_seed_data
        from db_manager import get_connection, create_schema
        conn = get_connection()
        create_schema(conn)
        etl_seed_data(conn)
        conn.close()

    elif cmd == "audit":
        from quality_control import run_audit
        run_audit()

    elif cmd == "stats":
        from db_manager import get_connection, count_records, count_by_source
        conn = get_connection()
        print(f"Всего записей: {count_records(conn)}")
        print("По источникам:")
        for src, cnt in count_by_source(conn).items():
            print(f"  {src}: {cnt}")
        conn.close()

    elif cmd == "auto":
        from automation import start_scheduler
        start_scheduler()

    elif cmd == "pdf":
        if len(sys.argv) < 3:
            print("Использование: python run.py pdf <path_to_file.pdf>")
            return
        from pdf_extractor import process_pdf
        import json
        result = process_pdf(sys.argv[2])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Неизвестная команда: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()