#!/usr/bin/env python3
"""Load sample drugs into the database.

This script loads the sample drugs and interactions from data/sample_drugs.json
into the drug database for testing and initial setup.
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.drugs import (
    DrugDatabase,
    Drug,
    DrugInteraction,
    TherapeuticClass,
    PregnancyCategory,
    LactationRisk,
    InteractionSeverity,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_sample_drugs():
    """Load sample drugs from JSON file."""
    # Load JSON data
    data_file = Path(__file__).parent.parent / "data" / "sample_drugs.json"

    if not data_file.exists():
        logger.error(f"Sample drugs file not found: {data_file}")
        return

    logger.info(f"Loading sample drugs from {data_file}")

    with open(data_file, "r") as f:
        data = json.load(f)

    # Initialize database
    db = DrugDatabase()

    # Load drugs
    drugs_loaded = 0
    for drug_data in data.get("drugs", []):
        try:
            drug = Drug(
                id=drug_data["id"],
                generic_name=drug_data["generic_name"],
                brand_names=drug_data.get("brand_names", []),
                indian_brand_names=drug_data.get("indian_brand_names", []),
                therapeutic_class=TherapeuticClass(drug_data.get("therapeutic_class", "other")),
                mechanism_of_action=drug_data.get("mechanism_of_action", ""),
                indications=drug_data.get("indications", []),
                contraindications=drug_data.get("contraindications", []),
                common_side_effects=drug_data.get("common_side_effects", []),
                serious_side_effects=drug_data.get("serious_side_effects", []),
                rxcui=drug_data.get("rxcui"),
                atc_code=drug_data.get("atc_code"),
                adult_dose=drug_data.get("adult_dose"),
                max_dose_per_day=drug_data.get("max_dose_per_day"),
                pregnancy_category=PregnancyCategory(drug_data.get("pregnancy_category", "UNKNOWN")),
                lactation_risk=LactationRisk(drug_data.get("lactation_risk", "UNKNOWN")),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            if db.add_drug(drug):
                drugs_loaded += 1

        except Exception as e:
            logger.error(f"Error loading drug {drug_data.get('generic_name', 'unknown')}: {e}")

    logger.info(f"Loaded {drugs_loaded} drugs")

    # Load interactions
    interactions_loaded = 0
    for interaction_data in data.get("interactions", []):
        try:
            interaction = DrugInteraction(
                id=interaction_data["id"],
                drug1_id=interaction_data["drug1_id"],
                drug1_name=interaction_data["drug1_name"],
                drug2_id=interaction_data["drug2_id"],
                drug2_name=interaction_data["drug2_name"],
                severity=InteractionSeverity(interaction_data.get("severity", "unknown")),
                mechanism=interaction_data.get("mechanism", ""),
                clinical_significance=interaction_data.get("clinical_significance", ""),
                management_strategy=interaction_data.get("management_strategy", ""),
                alternative_suggestions=interaction_data.get("alternative_suggestions", []),
                source=interaction_data.get("source", "Dora Database"),
                evidence_level=interaction_data.get("evidence_level", "Expert Opinion"),
                references=interaction_data.get("references", []),
            )

            if db.add_interaction(interaction):
                interactions_loaded += 1

        except Exception as e:
            logger.error(f"Error loading interaction {interaction_data.get('id', 'unknown')}: {e}")

    logger.info(f"Loaded {interactions_loaded} interactions")

    # Print statistics
    stats = db.get_database_stats()
    logger.info(f"\nDatabase Statistics:")
    logger.info(f"  Total drugs: {stats['total_drugs']}")
    logger.info(f"  Total interactions: {stats['total_interactions']}")
    logger.info(f"  Drugs by class:")
    for drug_class, count in stats.get("drugs_by_class", {}).items():
        logger.info(f"    {drug_class}: {count}")

    db.close()
    logger.info("\nSample drugs loaded successfully!")


if __name__ == "__main__":
    load_sample_drugs()
