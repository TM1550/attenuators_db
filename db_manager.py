"""
Управление SQLite-базой данных: создание схемы, вставка, миграция из CSV.
Теперь с защитой от дубликатов по последовательности через MD5-хеш.
"""
import sqlite3
import json
import hashlib
import pandas as pd
import numpy as np
import os
import logging
from config import DB_PATH, CSV_PATH

logger = logging.getLogger(__name__)


def get_connection():
    """Возвращает соединение с БД."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def hash_sequence(seq: str) -> str | None:
    """
    Вычисляет MD5-хеш от нормализованной последовательности.
    Используется для предотвращения дубликатов на уровне СУБД.
    """
    if not seq or not seq.strip():
        return None
    # Нормализуем: верхний регистр, убираем пробелы и переносы строк
    clean = seq.upper().replace(" ", "").replace("\n", "").replace("\r", "")
    return hashlib.md5(clean.encode('utf-8')).hexdigest()


def create_schema(conn):
    """Создаёт гибкую схему БД с защитой от дубликатов по последовательности."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS regulatory_elements (
            element_id       TEXT PRIMARY KEY,
            species          TEXT,
            gene_family      TEXT,
            regulated_gene   TEXT,
            sequence_type    TEXT CHECK(sequence_type IN ('RNA','peptide','DNA')),
            sequence         TEXT,
            seq_hash         TEXT,
            details_json     TEXT CHECK(json_valid(details_json)),
            source_db        TEXT NOT NULL DEFAULT 'unknown',
            confidence       TEXT NOT NULL DEFAULT 'curated',
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_species ON regulatory_elements(species);
        CREATE INDEX IF NOT EXISTS idx_source  ON regulatory_elements(source_db);
        CREATE INDEX IF NOT EXISTS idx_type    ON regulatory_elements(sequence_type);
        
        -- Уникальный индекс по хешу последовательности (исключая пустые значения)
        CREATE UNIQUE INDEX IF NOT EXISTS idx_seq_hash 
            ON regulatory_elements(seq_hash) 
            WHERE seq_hash IS NOT NULL AND seq_hash != '';
    """)
    conn.commit()
    logger.info("Схема БД создана/проверена (с защитой от дубликатов по seq_hash).")


def insert_record(conn, record: dict) -> bool:
    """
    Вставляет одну запись. 
    Проверяет дубликаты как по element_id, так и по seq_hash.
    """
    seq = record.get("sequence", "")
    seq_hash = hash_sequence(seq)
    
    # Если последовательности нет, запись не имеет смысла — пропускаем
    if not seq_hash:
        logger.debug(f"⏩ Пропуск (нет последовательности): {record['element_id']}")
        return False

    # Проверяем, нет ли уже такой последовательности в БД (защита от дубликатов)
    cur = conn.execute("SELECT element_id FROM regulatory_elements WHERE seq_hash = ?", (seq_hash,))
    existing = cur.fetchone()
    if existing:
        logger.debug(f"⏩ Дубликат по последовательности: {record['element_id']} (уже есть как {existing[0]})")
        return False

    sql = """
        INSERT OR IGNORE INTO regulatory_elements
            (element_id, species, gene_family, regulated_gene,
             sequence_type, sequence, seq_hash, details_json, source_db, confidence, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """
    cur = conn.execute(sql, (
        record["element_id"],
        record.get("species", "Unknown"),
        record.get("gene_family", ""),
        record.get("regulated_gene", "unknown"),
        record.get("sequence_type", "RNA"),
        seq,
        seq_hash,
        record.get("details_json", "{}"),
        record.get("source_db", "unknown"),
        record.get("confidence", "curated"),
    ))
    conn.commit()
    
    inserted = cur.rowcount > 0
    if inserted:
        logger.info(f"✅ Новая запись: {record['element_id']}")
    else:
        logger.debug(f"⏩ Дубликат по ID пропущен: {record['element_id']}")
    return inserted


def insert_many(conn, records: list) -> int:
    """Вставляет список записей. Возвращает число новых."""
    count = sum(insert_record(conn, r) for r in records)
    logger.info(f"Загружено {count} новых записей из {len(records)}")
    return count


def migrate_csv(conn, csv_path=None):
    """Мигрирует данные из оригинального CSV в новую схему."""
    csv_path = csv_path or CSV_PATH
    if not os.path.exists(csv_path):
        logger.warning(f"CSV не найден: {csv_path}")
        return 0

    df = pd.read_csv(csv_path).replace({np.nan: None})
    main_cols = {"id", "species", "gene_family", "regulated_gene",
                 "sequence_type", "terminate_sequence"}
    json_cols = [c for c in df.columns if c not in main_cols]

    records = []
    for _, row in df.iterrows():
        seq = row.get("terminate_sequence", "")
        # Пропускаем записи без последовательности
        if not seq or str(seq).strip().lower() in ("null", "none", ""):
            continue
            
        details = {c: row[c] for c in json_cols}
        records.append({
            "element_id": f"CSV_{row['id']}",
            "species": row.get("species"),
            "gene_family": row.get("gene_family"),
            "regulated_gene": row.get("regulated_gene"),
            "sequence_type": row.get("sequence_type", "RNA"),
            "sequence": seq,
            "details_json": json.dumps(details, ensure_ascii=False),
            "source_db": "local_csv",
            "confidence": "curated",
        })
    return insert_many(conn, records)


def count_records(conn):
    """Возвращает общее число записей."""
    return conn.execute("SELECT COUNT(*) FROM regulatory_elements").fetchone()[0]


def count_by_source(conn):
    """Возвращает число записей по источникам."""
    rows = conn.execute(
        "SELECT source_db, COUNT(*) FROM regulatory_elements GROUP BY source_db"
    ).fetchall()
    return dict(rows)