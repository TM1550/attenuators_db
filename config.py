"""
Конфигурация проекта: API-эндпоинты, список Rfam-семейств, настройки.
"""
import os

# ── Пути ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attenuators_v2.db")
CSV_PATH = "/mnt/c/Users/tsire/Downloads/exported_attenuators_standardized_db (4).csv"
LOG_PATH = os.path.join(BASE_DIR, "etl.log")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
PDF_DIR = os.path.join(BASE_DIR, "pdfs")

# ── API ───────────────────────────────────────────────
HEADERS = {"User-Agent": "AttenuatorDB-ETL/3.0 (research)"}
API_DELAY = 0.7  # секунд между запросами

RNACENTRAL_API = "https://rnacentral.org/api/v1/rna/"
RNACENTRAL_RFAM_API = "https://rnacentral.org/api/v1/rfam/"
EBI_SEARCH_API = "https://www.ebi.ac.uk/ebisearch/ws/rest/rfam/entry/"
NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
EUROPEPMC_API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# ── Rfam-семейства для автоматического сбора ─────────
# Ключ = Rfam accession, значение = метаданные
# ... (оставьте старые пути и API-эндпоинты без изменений) ...

# ── Расширенный список Rfam-семейств (Рибосвитчи, Т-боксы, Термометры, Аттенюаторы) ──
RFAM_FAMILIES = {
    # ── Классические рибосвитчи ──
    "RF00059": {"name": "FMN riboswitch", "ligand": "FMN", "type": "riboswitch", "pmid": "12459550"},
    "RF00050": {"name": "SAM-I riboswitch", "ligand": "SAM", "type": "riboswitch", "pmid": "12459550"},
    "RF00080": {"name": "TPP riboswitch", "ligand": "TPP", "type": "riboswitch", "pmid": "12459550"},
    "RF00162": {"name": "Glycine riboswitch", "ligand": "Glycine", "type": "riboswitch", "pmid": "15170430"},
    "RF00168": {"name": "Lysine riboswitch", "ligand": "Lysine", "type": "riboswitch", "pmid": "17558307"},
    "RF00504": {"name": "Purine riboswitch", "ligand": "Guanine/Adenine", "type": "riboswitch", "pmid": "15148735"},
    "RF00622": {"name": "SAM-II riboswitch", "ligand": "SAM", "type": "riboswitch", "pmid": "17558307"},
    "RF01055": {"name": "SAM-IV riboswitch", "ligand": "SAM", "type": "riboswitch", "pmid": "18398440"},
    "RF01174": {"name": "SAM-V riboswitch", "ligand": "SAM", "type": "riboswitch", "pmid": "22941638"},
    "RF01734": {"name": "SAM-VI riboswitch", "ligand": "SAM", "type": "riboswitch", "pmid": "30323089"},
    "RF00380": {"name": "c-di-GMP-II riboswitch", "ligand": "c-di-GMP", "type": "riboswitch", "pmid": "18621677"},
    "RF00234": {"name": "c-di-GMP-I riboswitch", "ligand": "c-di-GMP", "type": "riboswitch", "pmid": "18621677"},
    "RF01800": {"name": "c-di-GMP-III riboswitch", "ligand": "c-di-GMP", "type": "riboswitch", "pmid": "31504532"},
    "RF00521": {"name": "PreQ1 riboswitch", "ligand": "PreQ1", "type": "riboswitch", "pmid": "17584970"},
    "RF01831": {"name": "Guanidine riboswitch", "ligand": "Guanidine", "type": "riboswitch", "pmid": "28031486"},
    "RF02002": {"name": "ZTP riboswitch", "ligand": "ZTP", "type": "riboswitch", "pmid": "25900374"},
    "RF02003": {"name": "ppGpp riboswitch", "ligand": "ppGpp", "type": "riboswitch", "pmid": "29773628"},
    "RF01725": {"name": "Fluoride riboswitch", "ligand": "Fluoride", "type": "riboswitch", "pmid": "23155239"},
    "RF00174": {"name": "MoCo riboswitch", "ligand": "Molybdenum cofactor", "type": "riboswitch", "pmid": "18502848"},
    "RF01054": {"name": "ykoK riboswitch", "ligand": "Unknown", "type": "riboswitch", "pmid": "18398440"},
    "RF00442": {"name": "Mg2 riboswitch", "ligand": "Magnesium", "type": "riboswitch", "pmid": "18398440"},
    "RF01786": {"name": "NiMM riboswitch", "ligand": "Nickel", "type": "riboswitch", "pmid": "23155239"},
    "RF01727": {"name": "c-di-AMP riboswitch", "ligand": "c-di-AMP", "type": "riboswitch", "pmid": "28031486"},
    "RF01750": {"name": "SAH riboswitch", "ligand": "SAH", "type": "riboswitch", "pmid": "23155239"},
    "RF00163": {"name": "THF riboswitch", "ligand": "THF", "type": "riboswitch", "pmid": "15170430"},
    "RF00639": {"name": "Lysine riboswitch (type 2)", "ligand": "Lysine", "type": "riboswitch", "pmid": "17558307"},
    "RF01742": {"name": "Riboflavin riboswitch", "ligand": "Riboflavin", "type": "riboswitch", "pmid": "12459550"},
    "RF01787": {"name": "B12 riboswitch (BtuB)", "ligand": "AdoCbl", "type": "riboswitch", "pmid": "12379862"},
    "RF01788": {"name": "B12 riboswitch (EutB)", "ligand": "AdoCbl", "type": "riboswitch", "pmid": "12379862"},
    # ── T-box (аттенюация на основе тРНК) ──
    "RF00060": {"name": "T-box (hisS)", "ligand": "tRNA", "type": "tbox", "pmid": "12459550"},
    "RF01051": {"name": "T-box (ileS)", "ligand": "tRNA", "type": "tbox", "pmid": "15687264"},
    "RF01052": {"name": "T-box (leuS)", "ligand": "tRNA", "type": "tbox", "pmid": "15687264"},
    "RF01053": {"name": "T-box (thrS)", "ligand": "tRNA", "type": "tbox", "pmid": "15687264"},
    "RF01681": {"name": "T-box (glyS)", "ligand": "tRNA", "type": "tbox", "pmid": "15687264"},
    # ── Термометры ──
    "RF00032": {"name": "ROSE-like thermometer", "ligand": "Temperature", "type": "thermometer", "pmid": "11389153"},
    "RF00033": {"name": "FourU thermometer", "ligand": "Temperature", "type": "thermometer", "pmid": "17382372"},
    "RF00559": {"name": "RNA thermometer (short)", "ligand": "Temperature", "type": "thermometer", "pmid": "17382372"},
    "RF01042": {"name": "RNA thermometer (long)", "ligand": "Temperature", "type": "thermometer", "pmid": "19458107"},
    # ── Антисмы и другие регуляторные РНК ──
    "RF00035": {"name": "Antisense RNA", "ligand": "N/A", "type": "antisense", "pmid": ""},
    "RF00036": {"name": "Antisense RNA (type 2)", "ligand": "N/A", "type": "antisense", "pmid": ""},
}

# ── Запросы для МАССОВОГО сбора (Bulk) ──
# RNAcentral позволит выкачать сотни записей по этим широким запросам
BULK_RNACENTRAL_QUERIES = [
    'riboswitch',
    'attenuator',
    'RNA thermometer',
    'T-box',
    'leader peptide',
    'transcription termination',
]
# ── Поисковые запросы для NCBI / Europe PMC ─────────
NCBI_QUERIES = [
    "riboswitch[Title] AND (sequence[Title] OR structure[Title])",
    "RNA thermometer[Title] AND (attenuator OR terminator)",
    "transcription attenuation[Title] AND leader peptide",
]

EUROPEPMC_QUERIES = [
    "riboswitch AND crystal structure",
    "RNA thermometer AND gene regulation",
    "transcription attenuation AND leader peptide",
]