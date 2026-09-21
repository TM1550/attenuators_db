"""
Модуль извлечения данных из PDF-файлов научных статей.
Использует GROBID для предобработки и regex для извлечения сущностей.
"""
import re
import json
import os
import logging
import subprocess

logger = logging.getLogger(__name__)

# ── Регулярные выражения для извлечения ──────────────
PATTERNS = {
    "rna_sequence": re.compile(r"[ACGU]{20,}", re.IGNORECASE),
    "dna_sequence": re.compile(r"[ACGT]{20,}", re.IGNORECASE),
    "peptide_sequence": re.compile(r"[ACDEFGHIKLMNPQRSTVWY]{8,}"),
    "melting_temp": re.compile(r"T[mM]\s*[=≈]\s*([0-9]+\.?[0-9]*)\s*°?C?"),
    "free_energy": re.compile(r"ΔG\s*[=≈]\s*(-?[0-9]+\.?[0-9]*)\s*k(?:cal|J)/mol"),
    "molecular_weight": re.compile(r"(?:MW|molecular\s*weight)\s*[=≈]\s*([0-9]+\.?[0-9]*)\s*(?:Da|kDa)?", re.IGNORECASE),
    "gene_name": re.compile(r"\b(?:gene|operon)\s+([a-zA-Z]{2,5}[A-Z0-9]*)\b"),
    "rfam_id": re.compile(r"RF\d{5}"),
    "pmid": re.compile(r"PMID:\s*(\d+)"),
}


def extract_text_with_grobid(pdf_path: str, grobid_url: str = "http://localhost:8070") -> str:
    """
    Отправляет PDF в GROBID-сервер и получает структурированный текст.
    GROBID должен быть запущен через Docker:
      docker run -p 8070:8070 lfoppiano/grobid:0.8.0
    """
    try:
        import requests
        with open(pdf_path, "rb") as f:
            resp = requests.post(
                f"{grobid_url}/api/processFulltextDocument",
                files={"input": f},
                timeout=120,
            )
        if resp.status_code == 200:
            # GROBID возвращает TEI XML; для простоты извлекаем чистый текст
            text = resp.text
            # Удаляем XML-теги (упрощённо)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text
        else:
            logger.warning(f"GROBID вернул статус {resp.status_code}")
            return ""
    except Exception as e:
        logger.error(f"GROBID недоступен: {e}")
        return ""


def extract_text_fallback(pdf_path: str) -> str:
    """Простое извлечение текста через pdftotext (poppler-utils)."""
    try:
        result = subprocess.run(
            ["pdftotext", pdf_path, "-"],
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout
    except Exception as e:
        logger.error(f"pdftotext не сработал: {e}")
        return ""


def extract_entities(text: str) -> dict:
    """Извлекает структурированные данные из текста с помощью regex."""
    extracted = {}

    # Последовательности
    rna_seqs = PATTERNS["rna_sequence"].findall(text)
    if rna_seqs:
        extracted["rna_sequences"] = list(set(rna_seqs[:5]))  # до 5 уникальных

    pep_seqs = PATTERNS["peptide_sequence"].findall(text)
    if pep_seqs:
        extracted["peptide_sequences"] = list(set(pep_seqs[:5]))

    # Числовые значения
    tm = PATTERNS["melting_temp"].findall(text)
    if tm:
        extracted["melting_temperature"] = float(tm[0])

    energy = PATTERNS["free_energy"].findall(text)
    if energy:
        extracted["stem_energy"] = float(energy[0])

    mw = PATTERNS["molecular_weight"].findall(text)
    if mw:
        extracted["peptide_mw"] = float(mw[0])

    # Идентификаторы
    rfam = PATTERNS["rfam_id"].findall(text)
    if rfam:
        extracted["rfam_ids"] = list(set(rfam))

    genes = PATTERNS["gene_name"].findall(text)
    if genes:
        extracted["gene_names"] = list(set(genes[:10]))

    pmids = PATTERNS["pmid"].findall(text)
    if pmids:
        extracted["pmids"] = list(set(pmids))

    return extracted


def process_pdf(pdf_path: str) -> dict:
    """Полный пайплайн обработки одного PDF."""
    if not os.path.exists(pdf_path):
        logger.error(f"Файл не найден: {pdf_path}")
        return {}

    # Пробуем GROBID, затем fallback
    text = extract_text_with_grobid(pdf_path)
    if not text:
        logger.info("GROBID недоступен, используем pdftotext")
        text = extract_text_fallback(pdf_path)

    if not text:
        logger.warning(f"Не удалось извлечь текст из {pdf_path}")
        return {"file": pdf_path, "status": "failed"}

    entities = extract_entities(text)
    entities["file"] = os.path.basename(pdf_path)
    entities["status"] = "success"
    entities["needs_manual_review"] = True  # PDF-данные всегда требуют проверки
    entities["text_length"] = len(text)

    logger.info(f"Извлечено из {pdf_path}: {list(entities.keys())}")
    return entities