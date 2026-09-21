"""
Расчёт физико-химических свойств РНК и пептидов.
"""
import re
import logging

logger = logging.getLogger(__name__)


def calculate_rna_properties(seq: str) -> dict:
    """
    Эмпирические расчёты для РНК:
      - melting_temperature (формула Уоллеса, адаптированная)
      - stem_energy (грубая оценка на длину)
      - u_rich_content (% U)
      - u_rich_tract (макс. длина подряд идущих U)
      - gc_content (%)
    """
    if not seq:
        return {}
    seq = seq.upper().replace("T", "U")
    n = len(seq)
    if n == 0:
        return {}

    gc = seq.count("G") + seq.count("C")
    u_count = seq.count("U")

    # Формула Уоллеса для коротких олигонуклеотидов
    tm = 64.9 + 41.0 * (gc - 16.4) / n if n > 0 else 0.0
    # Грубая энергия стебля (ккал/моль)
    energy = -0.5 * n
    # Максимальная длина непрерывного U-тракта
    u_tracts = re.findall(r"U+", seq)
    max_u_tract = max((len(t) for t in u_tracts), default=0)

    return {
        "melting_temperature": round(tm, 2),
        "stem_energy": round(energy, 2),
        "u_rich_content": round((u_count / n) * 100, 2),
        "u_rich_tract": max_u_tract,
        "gc_content": round((gc / n) * 100, 2),
        "length_nt": n,
    }


def calculate_peptide_properties(seq: str) -> dict:
    """
    Расчёт свойств пептида через Biopython:
      - peptide_mw (молекулярная масса, Да)
      - peptide_charge (заряд при pH 7.0)
      - peptide_gravy (индекс гидропатичности)
      - peptide_length (число аминокислот)
    """
    if not seq:
        return {}
    # Очистка: только канонические аминокислоты
    clean = re.sub(r"[^ACDEFGHIKLMNPQRSTVWY]", "", seq.upper())
    if len(clean) < 2:
        return {}
    try:
        from Bio.SeqUtils.ProtParam import ProteinAnalysis
        pa = ProteinAnalysis(clean)
        return {
            "peptide_mw": round(pa.molecular_weight(), 2),
            "peptide_charge": round(pa.charge_at_pH(7.0), 2),
            "peptide_gravy": round(pa.gravy(), 4),
            "peptide_length": len(clean),
        }
    except Exception as e:
        logger.warning(f"Biopython не смог обработать пептид: {e}")
        return {"peptide_length": len(clean)}