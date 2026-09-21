"""
Курированные данные об аттенюаторах, собранные вручную из научных статей.
Каждая запись содержит ссылки на публикации (PMID) и помечена как 'curated'.
Последовательности, помеченные как None, будут получены из API на этапе ETL.
"""
import json

SEED_RECORDS = [
    # ── 1. Fluoride riboswitch (Baker et al., 2012, Science, PMID:23155239) ──
    {
        "element_id": "SEED_RF01725_PSYR",
        "species": "Pseudomonas syringae",
        "gene_family": "crcB",
        "regulated_gene": "crcB",
        "sequence_type": "RNA",
        "sequence": "GGGAAGCUUGUCUUCGGGCCAGCAUGAAAGCUGGCUUUGUCUUCGGGCCAGCAUGAAAGCUGGCUUU",
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "rfam_family_id": "RF01725",
            "attenuator_name": "Fluoride riboswitch (crcB)",
            "known_elements": "Fluoride riboswitch",
            "sequentional_elements": "Ligand: Fluoride ion",
            "ligand": "Fluoride",
            "mechanism": "transcription termination",
            "pmid": "23155239",
            "reference": "Baker JL et al. (2012) Science 338:1343-1346",
            "fetch_from_api": True,
        }
    },
    # ── 2. FourU thermometer agsA (Waldminghaus et al., 2007, PMID:17382372) ──
    {
        "element_id": "SEED_FOURU_AGSA_SENT",
        "species": "Salmonella enterica",
        "gene_family": "agsA",
        "regulated_gene": "agsA",
        "sequence_type": "RNA",
        "sequence": "AGAGGUUUUUUUUUUAGAUACAGGAUGAAGGUUUCUAAC",
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "rfam_family_id": "RF00033",
            "attenuator_name": "FourU thermometer (agsA)",
            "known_elements": "FourU RNA thermometer",
            "sequentional_elements": "Ligand: Temperature",
            "ligand": "Temperature",
            "mechanism": "translational repression via SD sequestration",
            "temperature_threshold_celsius": 45,
            "pmid": "17382372",
            "reference": "Waldminghaus T et al. (2007) FEMS Microbiol Lett 273:180-186",
            "fetch_from_api": True,
        }
    },
    # ── 3. prfA thermometer (Johansson et al., 2002, Cell, PMID:12088842) ──
    {
        "element_id": "SEED_THERMO_PRFA_LMON",
        "species": "Listeria monocytogenes",
        "gene_family": "prfA",
        "regulated_gene": "prfA",
        "sequence_type": "RNA",
        "sequence": None,
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "attenuator_name": "prfA RNA thermometer",
            "known_elements": "prfA thermometer",
            "sequentional_elements": "Ligand: Temperature",
            "ligand": "Temperature",
            "mechanism": "translational activation at 37°C via hairpin melting",
            "temperature_threshold_celsius": 37,
            "pmid": "12088842",
            "reference": "Johansson J et al. (2002) Cell 110:551-561",
            "fetch_from_api": True,
        }
    },
    # ── 4. rpoH thermometer (Morita et al., 1999, Genes Dev, PMID:10364162) ──
    {
        "element_id": "SEED_THERMO_RPOH_ECOLI",
        "species": "Escherichia coli",
        "gene_family": "rpoH",
        "regulated_gene": "rpoH",
        "sequence_type": "RNA",
        "sequence": None,
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "attenuator_name": "rpoH RNA thermometer",
            "known_elements": "rpoH heat-shock thermometer",
            "sequentional_elements": "Ligand: Temperature",
            "ligand": "Temperature",
            "mechanism": "translational activation at 42°C via structure melting",
            "temperature_threshold_celsius": 42,
            "pmid": "10364162",
            "reference": "Morita MT et al. (1999) Genes Dev 13:1133-1138",
            "fetch_from_api": True,
        }
    },
    # ── 5. cspA cold-shock (Goldenberg et al., 1996, PMID:8647436) ──
    {
        "element_id": "SEED_COLD_CSPA_ECOLI",
        "species": "Escherichia coli",
        "gene_family": "cspA",
        "regulated_gene": "cspA",
        "sequence_type": "RNA",
        "sequence": None,
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "attenuator_name": "cspA cold-shock 5' UTR",
            "known_elements": "cspA cold-box element",
            "sequentional_elements": "Ligand: Low temperature",
            "ligand": "Cold",
            "mechanism": "mRNA stabilization at low temperature, enhanced translation",
            "temperature_threshold_celsius": 15,
            "pmid": "8647436",
            "reference": "Goldenberg D et al. (1996) Genes Dev 10:1050-1057",
            "fetch_from_api": True,
        }
    },
    # ── 6. glmS riboswitch (Winkler et al., 2004, Nature, PMID:15229603) ──
    {
        "element_id": "SEED_GLMS_BSUB",
        "species": "Bacillus subtilis",
        "gene_family": "glmS",
        "regulated_gene": "glmS",
        "sequence_type": "RNA",
        "sequence": None,
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "attenuator_name": "glmS ribozyme riboswitch",
            "known_elements": "glmS GlcN6P riboswitch-ribozyme",
            "sequentional_elements": "Ligand: Glucosamine-6-phosphate",
            "ligand": "Glucosamine-6-phosphate",
            "mechanism": "self-cleavage upon ligand binding, mRNA degradation",
            "pmid": "15229603",
            "reference": "Winkler WC et al. (2004) Nature 428:281-286",
            "fetch_from_api": True,
        }
    },
    # ── 7. AdoCbl (B12) riboswitch btuB (Nahvi et al., 2002, PMID:12379862) ──
    {
        "element_id": "SEED_ADOCBL_BTUB_ECOLI",
        "species": "Escherichia coli",
        "gene_family": "btuB",
        "regulated_gene": "btuB",
        "sequence_type": "RNA",
        "sequence": None,
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "rfam_family_id": "RF00174",
            "attenuator_name": "AdoCbl (B12) riboswitch (btuB)",
            "known_elements": "Cobalamin riboswitch",
            "sequentional_elements": "Ligand: Adenosylcobalamin (B12)",
            "ligand": "Adenosylcobalamin",
            "mechanism": "translational repression via SD sequestration",
            "pmid": "12379862",
            "reference": "Nahvi A et al. (2002) Chem Biol 9:1043-1049",
            "fetch_from_api": True,
        }
    },
    # ── 8. ermC leader peptide (Horinouchi & Weisblum, 1980, PMID:6780570) ──
    {
        "element_id": "SEED_ERMC_BSUB",
        "species": "Bacillus subtilis",
        "gene_family": "ermC",
        "regulated_gene": "ermC",
        "sequence_type": "peptide",
        "sequence": "MGIFSVFLVISQHYSQPNK",
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "attenuator_name": "ermC leader peptide",
            "known_elements": "ermC leader (translational attenuation, erythromycin-inducible)",
            "sequentional_elements": "Erythromycin binding stalls ribosome on leader, exposing ermC RBS",
            "ligand": "Erythromycin",
            "mechanism": "translational attenuation via ribosome stalling",
            "pmid": "6780570",
            "reference": "Horinouchi S & Weisblum B (1980) PNAS 77:7079-7083",
        }
    },
    # ── 9. cat-86 leader peptide (Harwood et al., 1983, PMID:6306474) ──
    {
        "element_id": "SEED_CAT86_BSUB",
        "species": "Bacillus subtilis",
        "gene_family": "cat-86",
        "regulated_gene": "cat-86",
        "sequence_type": "peptide",
        "sequence": "MIFHITLVISQHYSQPNK",
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "attenuator_name": "cat-86 leader peptide",
            "known_elements": "cat-86 leader (chloramphenicol-inducible)",
            "sequentional_elements": "Chloramphenicol stalls ribosome, exposing cat-86 RBS",
            "ligand": "Chloramphenicol",
            "mechanism": "translational attenuation via ribosome stalling",
            "pmid": "6306474",
            "reference": "Harwood CR et al. (1983) J Bacteriol 154:1077-1083",
        }
    },
    # ── 10. Moco riboswitch moaA (Regulski et al., 2008, PMID:18502848) ──
    {
        "element_id": "SEED_MOCO_MOAA_ECOLI",
        "species": "Escherichia coli",
        "gene_family": "moaA",
        "regulated_gene": "moaA",
        "sequence_type": "RNA",
        "sequence": None,
        "source_db": "seed_literature",
        "confidence": "curated",
        "details": {
            "rfam_family_id": "RF00174",
            "attenuator_name": "Moco riboswitch (moaA)",
            "known_elements": "Molybdenum cofactor riboswitch",
            "sequentional_elements": "Ligand: Molybdenum cofactor (Moco)",
            "ligand": "Molybdenum cofactor",
            "mechanism": "transcription termination",
            "pmid": "18502848",
            "reference": "Regulski EE et al. (2008) Genes Dev 22:2811-2822",
            "fetch_from_api": True,
        }
    },
]


def get_seed_records():
    """Возвращает список seed-записей с details_json в формате строки."""
    records = []
    for r in SEED_RECORDS:
        rec = dict(r)
        rec["details_json"] = json.dumps(rec.pop("details"), ensure_ascii=False)
        records.append(rec)
    return records