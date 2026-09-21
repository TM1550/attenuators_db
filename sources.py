"""
API-клиенты для извлечения данных из RNAcentral, NCBI Entrez и Europe PMC.
Поддерживает пагинацию и массовый сбор данных.
"""
import requests
import json
import time
import re
import logging
from config import (
    RNACENTRAL_API, RNACENTRAL_RFAM_API, EBI_SEARCH_API,
    NCBI_ESEARCH, NCBI_EFETCH, EUROPEPMC_API,
    HEADERS, API_DELAY, RFAM_FAMILIES,
)

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────────────
#  RNAcentral
# ───────────────────────────────────────────────────────

def fetch_rnacentral_paginated(query: str, max_records: int = 500) -> list:
    """
    Массовый поиск в RNAcentral с автоматической пагинацией.
    Выкачивает до max_records записей по широкому запросу.
    """
    results = []
    url = RNACENTRAL_API
    params = {"query": query, "page_size": 100, "format": "json"}
    
    logger.info(f"[RNAcentral Bulk] Начало массового сбора по запросу: '{query}' (лимит {max_records})")
    
    while url and len(results) < max_records:
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            if resp.status_code == 429:  # Rate limit
                logger.warning("Превышен лимит API RNAcentral. Пауза 15 сек...")
                time.sleep(15)
                continue
            resp.raise_for_status()
            data = resp.json()
            
            hits = data.get("results", [])
            if not hits:
                break
                
            for h in hits:
                parsed = _parse_rnacentral_hit(h, query)
                if parsed:
                    results.append(parsed)
            
            # Переход на следующую страницу
            url = data.get("next")
            params = {} # Для следующих страниц URL уже содержит параметры
            
            logger.info(f"  ... загружено {len(results)} записей")
            time.sleep(API_DELAY)
            
        except Exception as e:
            logger.error(f"[RNAcentral Bulk] Ошибка пагинации: {e}")
            break
            
    return results[:max_records]


def fetch_rnacentral_by_rfam(rfam_id: str, page_size: int = 100) -> list:
    """
    Поиск последовательностей в RNAcentral по конкретному Rfam ID.
    """
    results = []
    try:
        params = {"query": rfam_id, "page_size": page_size, "format": "json"}
        resp = requests.get(RNACENTRAL_API, params=params, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("results", [])
            if hits:
                logger.info(f"[{rfam_id}] Получено {len(hits)} записей")
                for h in hits:
                    parsed = _parse_rnacentral_hit(h, rfam_id)
                    if parsed:
                        results.append(parsed)
                return results
    except Exception as e:
        logger.debug(f"[{rfam_id}] Ошибка: {e}")
    return []


def _parse_rnacentral_hit(hit: dict, source_tag: str) -> dict | None:
    """Парсит один результат RNAcentral в унифицированный словарь."""
    rid = hit.get("id") or hit.get("rnacentral_id")
    seq = hit.get("sequence", "")
    
    # КРИТИЧНО: пропускаем записи без последовательности
    if not rid or not seq or not seq.strip():
        return None
        
    return {
        "rnacentral_id": rid,
        "description": hit.get("description", ""),
        "sequence": seq,
        "species": hit.get("species", "Unknown"),
        "length": hit.get("length", 0),
        "databases": hit.get("databases", []),
        "source_tag": source_tag,
    }


# ───────────────────────────────────────────────────────
#  NCBI Entrez (E-utilities)
# ───────────────────────────────────────────────────────

def fetch_ncbi_sequences(query: str, retmax: int = 100) -> list:
    """
    Ищет нуклеотидные последовательности в NCBI по текстовому запросу.
    Возвращает список распарсенных FASTA-записей.
    """
    results = []
    try:
        # Шаг 1: esearch → список ID
        params = {"db": "nucleotide", "term": query, "retmode": "json", "retmax": retmax}
        resp = requests.get(NCBI_ESEARCH, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        id_list = resp.json().get("esearchresult", {}).get("idlist", [])
        if not id_list:
            logger.info(f"[NCBI] По запросу '{query}' ничего не найдено")
            return []

        logger.info(f"[NCBI] Найдено {len(id_list)} ID по запросу '{query}'")
        time.sleep(API_DELAY)

        # Шаг 2: efetch → FASTA (NCBI позволяет запрашивать до 500 ID за раз)
        params2 = {"db": "nucleotide", "id": ",".join(id_list),
                    "rettype": "fasta", "retmode": "text"}
        resp2 = requests.get(NCBI_EFETCH, params=params2, headers=HEADERS, timeout=60)
        resp2.raise_for_status()
        fasta_text = resp2.text

        # Парсим FASTA
        for block in fasta_text.strip().split(">"):
            if not block.strip():
                continue
            lines = block.strip().split("\n")
            header = lines[0]
            seq = "".join(lines[1:]).replace(" ", "").replace("\n", "").replace("\r", "")
            
            if not seq:
                continue
                
            # Извлекаем species из заголовка
            species = "Unknown"
            m = re.search(r"\[([^\]]+)\]", header)
            if m:
                species = m.group(1)
            # Извлекаем accession
            acc = header.split()[0] if header else "unknown"

            results.append({
                "ncbi_accession": acc,
                "description": header,
                "sequence": seq,
                "species": species,
            })

    except Exception as e:
        logger.error(f"[NCBI] Ошибка: {e}")

    return results


# ───────────────────────────────────────────────────────
#  Europe PMC (поиск статей)
# ───────────────────────────────────────────────────────

def search_europepmc(query: str, page_size: int = 20) -> list:
    """
    Ищет научные статьи в Europe PMC.
    Возвращает метаданные статей (PMID, заголовок, авторы, DOI).
    """
    results = []
    try:
        params = {"query": query, "format": "json", "pageSize": page_size,
                  "resultType": "core"}
        resp = requests.get(EUROPEPMC_API, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("resultList", {}).get("result", [])
        for h in hits:
            results.append({
                "pmid": h.get("pmid", ""),
                "pmcid": h.get("pmcid", ""),
                "title": h.get("title", ""),
                "authors": h.get("authorString", ""),
                "doi": h.get("doi", ""),
                "journal": h.get("journalTitle", ""),
                "year": h.get("pubYear", ""),
                "has_fulltext": h.get("isOpenAccess", False),
                "query": query,
            })
        logger.info(f"[EuropePMC] По запросу '{query}' найдено {len(results)} статей")
    except Exception as e:
        logger.error(f"[EuropePMC] Ошибка: {e}")

    return results