"""
Основной ETL-конвейер: объединяет все источники, трансформирует и загружает.
Включает массовый сбор (Bulk) и сохранение метаданных статей в JSON.
"""
import json
import time
import re
import logging
import os
from config import (
    RFAM_FAMILIES, NCBI_QUERIES, EUROPEPMC_QUERIES, 
    BULK_RNACENTRAL_QUERIES, API_DELAY, BASE_DIR
)
from db_manager import get_connection, create_schema, insert_record, migrate_csv, count_records
from calculators import calculate_rna_properties, calculate_peptide_properties
from seed_data import get_seed_records
from sources import (
    fetch_rnacentral_by_rfam, fetch_rnacentral_paginated, 
    fetch_ncbi_sequences, search_europepmc
)

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────────────
#  Трансформация
# ───────────────────────────────────────────────────────

def transform_rnacentral_hit(hit: dict, rfam_id: str, rfam_info: dict) -> dict | None:
    """Преобразует сырой хит RNAcentral в запись для БД."""
    seq = hit.get("sequence", "")
    if not seq or not seq.strip():
        return None  # КРИТИЧНО: пропускаем записи без последовательности

    rid = hit["rnacentral_id"]
    seq_type = "RNA"
    props = calculate_rna_properties(seq)

    # Извлечение регулируемого гена из описания
    reg_gene = "unknown"
    m = re.search(r"regulates?\s+([a-zA-Z0-9_,]+)", hit.get("description", ""), re.I)
    if m:
        reg_gene = m.group(1).split(",")[0].strip()

    details = {
        "rnacentral_id": rid,
        "rfam_family_id": rfam_id,
        "attenuator_name": rfam_info["name"],
        "known_elements": rfam_info["name"],
        "sequentional_elements": f"Ligand: {rfam_info['ligand']}",
        "ligand": rfam_info["ligand"],
        "element_class": rfam_info["type"],
        "source_api": "RNAcentral",
        "rnacentral_url": f"https://rnacentral.org/rna/{rid}",
        "pmid": rfam_info.get("pmid", ""),
        **props,
    }

    return {
        "element_id": f"RNAC_{rid}",
        "species": hit.get("species", "Unknown"),
        "gene_family": rfam_info["name"],
        "regulated_gene": reg_gene,
        "sequence_type": seq_type,
        "sequence": seq,
        "details_json": json.dumps(details, ensure_ascii=False),
        "source_db": "RNAcentral",
        "confidence": "curated",
    }


def transform_ncbi_hit(hit: dict) -> dict | None:
    """Преобразует NCBI FASTA-запись в формат БД."""
    seq = hit.get("sequence", "")
    if not seq or not seq.strip():
        return None  # КРИТИЧНО: пропускаем записи без последовательности
        
    seq_type = "RNA"
    props = calculate_rna_properties(seq)

    details = {
        "ncbi_accession": hit["ncbi_accession"],
        "description": hit.get("description", ""),
        "source_api": "NCBI_Entrez",
        **props,
    }

    return {
        "element_id": f"NCBI_{hit['ncbi_accession']}",
        "species": hit.get("species", "Unknown"),
        "gene_family": "ncRNA",
        "regulated_gene": "unknown",
        "sequence_type": seq_type,
        "sequence": seq,
        "details_json": json.dumps(details, ensure_ascii=False),
        "source_db": "NCBI",
        "confidence": "predicted",
    }


# ───────────────────────────────────────────────────────
#  ETL-этапы
# ───────────────────────────────────────────────────────

def etl_seed_data(conn):
    """Загружает курированные данные из seed_data.py."""
    logger.info("═══ Этап 1: Загрузка seed-данных из литературы ═══")
    records = get_seed_records()
    new = 0
    for r in records:
        # Если последовательность отсутствует, record будет пропущен в insert_record
        if r.get("sequence"):
            if r["sequence_type"] == "RNA":
                props = calculate_rna_properties(r["sequence"])
            else:
                props = calculate_peptide_properties(r["sequence"])
            details = json.loads(r["details_json"])
            details.update(props)
            r["details_json"] = json.dumps(details, ensure_ascii=False)
        if insert_record(conn, r):
            new += 1
    logger.info(f"Seed: загружено {new} новых из {len(records)}")


def etl_rnacentral(conn):
    """Извлекает данные из RNAcentral по Rfam-семействам (лимит 100 на семейство)."""
    logger.info("═══ Этап 2: Извлечение из RNAcentral по Rfam ID ═══")
    new_total = 0
    for rfam_id, info in RFAM_FAMILIES.items():
        logger.info(f"🔍 {rfam_id} — {info['name']}")
        hits = fetch_rnacentral_by_rfam(rfam_id, page_size=100)
        for hit in hits:
            record = transform_rnacentral_hit(hit, rfam_id, info)
            if record and insert_record(conn, record):
                new_total += 1
        time.sleep(API_DELAY)
    logger.info(f"RNAcentral (Rfam): загружено {new_total} новых записей")


def etl_bulk_rnacentral(conn):
    """Массовая выкачка данных из RNAcentral по широким запросам с пагинацией."""
    logger.info("═══ Этап 2.5: МАССОВЫЙ СБОР из RNAcentral (Bulk) ═══")
    new_total = 0
    for query in BULK_RNACENTRAL_QUERIES:
        hits = fetch_rnacentral_paginated(query, max_records=500)
        for hit in hits:
            seq = hit.get("sequence")
            if not seq or not seq.strip():
                continue
                
            rid = hit["rnacentral_id"]
            details = {
                "rnacentral_id": rid,
                "description": hit.get("description", ""),
                "source_api": "RNAcentral_Bulk",
                "search_query": query,
                **calculate_rna_properties(seq)
            }
            record = {
                "element_id": f"RNAC_BULK_{rid}",
                "species": hit.get("species", "Unknown"),
                "gene_family": "ncRNA_bulk",
                "regulated_gene": "unknown",
                "sequence_type": "RNA",
                "sequence": seq,
                "details_json": json.dumps(details, ensure_ascii=False),
                "source_db": "RNAcentral_Bulk",
                "confidence": "predicted",
            }
            if insert_record(conn, record):
                new_total += 1
        time.sleep(2) # Пауза между массовыми запросами
    logger.info(f"RNAcentral Bulk: загружено {new_total} новых записей")


def etl_ncbi(conn):
    """Извлекает последовательности из NCBI (лимит 100 на запрос)."""
    logger.info("═══ Этап 3: Извлечение из NCBI Entrez ═══")
    new_total = 0
    for query in NCBI_QUERIES:
        hits = fetch_ncbi_sequences(query, retmax=100)
        for hit in hits:
            record = transform_ncbi_hit(hit)
            if record and insert_record(conn, record):
                new_total += 1
        time.sleep(API_DELAY * 2)  # NCBI строже к лимитам
    logger.info(f"NCBI: загружено {new_total} новых записей")


def etl_europepmc():
    """
    Ищет статьи в Europe PMC. 
    Так как статьи не содержат последовательностей, они сохраняются в JSON-файл
    для последующего скачивания PDF и обработки через pdf_extractor.py.
    """
    logger.info("═══ Этап 4: Поиск статей в Europe PMC ═══")
    all_articles = []
    
    for query in EUROPEPMC_QUERIES:
        articles = search_europepmc(query, page_size=20)
        all_articles.extend(articles)
        time.sleep(API_DELAY)
        
    # Удаляем дубликаты по PMID
    unique_articles = {art["pmid"]: art for art in all_articles if art.get("pmid")}.values()
    
    # Сохраняем в JSON
    out_path = os.path.join(BASE_DIR, "found_articles.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(list(unique_articles), f, ensure_ascii=False, indent=2)
        
    logger.info(f"EuropePMC: найдено {len(unique_articles)} уникальных статей. Сохранено в {out_path}")


# ───────────────────────────────────────────────────────
#  Главный запуск
# ───────────────────────────────────────────────────────

def run_full_etl(migrate: bool = False):
    """Запускает полный ETL-конвейер."""
    conn = get_connection()
    create_schema(conn)

    if migrate:
        logger.info("Миграция из CSV...")
        migrate_csv(conn)

    etl_seed_data(conn)
    etl_rnacentral(conn)
    etl_bulk_rnacentral(conn)
    etl_ncbi(conn)
    
    # EuropePMC не пишет в БД, а сохраняет список статей в JSON
    etl_europepmc()

    total = count_records(conn)
    logger.info(f"🎉 ETL завершён. Всего уникальных последовательностей в БД: {total}")
    conn.close()