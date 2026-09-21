"""
Аудит качества данных: валидация JSON, последовательностей, поиск дубликатов.
"""
import sqlite3
import json
import re
import logging
from db_manager import get_connection, hash_sequence

logger = logging.getLogger(__name__)

VALID_RNA = re.compile(r"^[ACGUacgu]+$")
VALID_DNA = re.compile(r"^[ACGTacgt]+$")
VALID_PEP = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY\*]+$")


def validate_sequence(seq: str, seq_type: str) -> bool:
    if not seq:
        return False
    if seq_type == "RNA":
        return bool(VALID_RNA.match(seq))
    elif seq_type == "DNA":
        return bool(VALID_DNA.match(seq))
    elif seq_type == "peptide":
        return bool(VALID_PEP.match(seq))
    return False


def run_audit():
    """Запускает полный аудит качества."""
    conn = get_connection()
    cur = conn.execute("""
        SELECT element_id, sequence_type, sequence, seq_hash, details_json, source_db
        FROM regulatory_elements
    """)

    issues = {
        "invalid_json": [], 
        "empty_sequence": [], 
        "bad_sequence": [], 
        "duplicate_seq": [], 
        "logic_warnings": []
    }
    
    seen_hashes = {}  # Для поиска дубликатов по хешу
    total = 0

    for row in cur.fetchall():
        total += 1
        eid, stype, seq, seq_hash, dj, src = row

        # 1. Валидность JSON
        try:
            details = json.loads(dj) if dj else {}
        except json.JSONDecodeError:
            issues["invalid_json"].append(eid)
            continue

        # 2. Проверка на пустую последовательность
        if not seq or not seq.strip():
            issues["empty_sequence"].append(eid)
            continue

        # 3. Проверка на дубликаты по хешу
        if seq_hash:
            if seq_hash in seen_hashes:
                issues["duplicate_seq"].append(f"{eid} (дублирует {seen_hashes[seq_hash]})")
            else:
                seen_hashes[seq_hash] = eid
        else:
            # Если хеша нет, но последовательность есть — пересчитываем
            calc_hash = hash_sequence(seq)
            if calc_hash in seen_hashes:
                issues["duplicate_seq"].append(f"{eid} (дублирует {seen_hashes[calc_hash]}, нет хеша в БД)")

        # 4. Валидность символов последовательности
        if not validate_sequence(seq, stype):
            issues["bad_sequence"].append(eid)

        # 5. Логические проверки
        if stype == "RNA":
            u_tract = details.get("u_rich_tract")
            element_class = details.get("element_class", "")
            if element_class == "riboswitch" and u_tract is not None and u_tract > 8:
                issues["logic_warnings"].append(
                    f"{eid}: unusually long U-tract ({u_tract}) for riboswitch"
                )

    # Отчёт
    logger.info(f"═══ Аудит качества: {total} записей проверено ═══")
    logger.info(f"  Некорректный JSON:         {len(issues['invalid_json'])}")
    logger.info(f"  Пустые последовательности: {len(issues['empty_sequence'])}")
    logger.info(f"  Плохие последовательности: {len(issues['bad_sequence'])}")
    logger.info(f"  Дубликаты по последовательности: {len(issues['duplicate_seq'])}")
    logger.info(f"  Логические предупреждения: {len(issues['logic_warnings'])}")

    for cat, items in issues.items():
        for item in items[:10]:  # показываем максимум 10
            logger.warning(f"  [{cat}] {item}")

    conn.close()
    return issues