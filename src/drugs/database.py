"""Drug database storage with SQLite backend.

Provides full-text search, fuzzy matching, and offline-first storage.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional
from difflib import SequenceMatcher

from .models import (
    Drug,
    DrugInteraction,
    DrugFormulation,
    DrugPrice,
    PregnancySafety,
    LactationSafety,
    RenalDosingAdjustment,
    HepaticDosingAdjustment,
    PediatricDosing,
    GenericEquivalent,
    DrugAllergy,
    Contraindication,
    DrugSearchResult,
    TherapeuticClass,
    InteractionSeverity,
    PregnancyCategory,
    LactationRisk,
    RenalDosing,
    HepaticDosing,
    FormulationType,
)

logger = logging.getLogger(__name__)


class DrugDatabase:
    """SQLite-based drug database with search capabilities."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize drug database.

        Args:
            db_path: Path to SQLite database file. Defaults to data/drugs.db
        """
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "data" / "drugs.db")

        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._ensure_database()

    def _ensure_database(self):
        """Ensure database and tables exist."""
        # Create data directory if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()
        self._create_indexes()

    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()

        # Drugs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drugs (
                id TEXT PRIMARY KEY,
                generic_name TEXT NOT NULL,
                brand_names TEXT,
                indian_brand_names TEXT,
                therapeutic_class TEXT,
                mechanism_of_action TEXT,
                indications TEXT,
                contraindications TEXT,
                common_side_effects TEXT,
                serious_side_effects TEXT,
                rxcui TEXT,
                atc_code TEXT,
                adult_dose TEXT,
                max_dose_per_day TEXT,
                pregnancy_category TEXT,
                lactation_risk TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Full-text search virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS drugs_fts USING fts5(
                id,
                generic_name,
                brand_names,
                indian_brand_names,
                therapeutic_class,
                content='drugs',
                content_rowid='rowid'
            )
        """)

        # Drug interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drug_interactions (
                id TEXT PRIMARY KEY,
                drug1_id TEXT,
                drug1_name TEXT,
                drug2_id TEXT,
                drug2_name TEXT,
                severity TEXT,
                mechanism TEXT,
                clinical_significance TEXT,
                management_strategy TEXT,
                alternative_suggestions TEXT,
                source TEXT,
                evidence_level TEXT,
                references TEXT,
                FOREIGN KEY (drug1_id) REFERENCES drugs(id),
                FOREIGN KEY (drug2_id) REFERENCES drugs(id)
            )
        """)

        # Pregnancy safety table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pregnancy_safety (
                drug_id TEXT PRIMARY KEY,
                drug_name TEXT,
                category TEXT,
                trimester_specific TEXT,
                description TEXT,
                fetal_risks TEXT,
                maternal_risks TEXT,
                alternatives TEXT,
                references TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        # Lactation safety table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lactation_safety (
                drug_id TEXT PRIMARY KEY,
                drug_name TEXT,
                risk_category TEXT,
                description TEXT,
                infant_risks TEXT,
                monitoring_parameters TEXT,
                alternatives TEXT,
                peak_levels_timing TEXT,
                references TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        # Renal dosing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS renal_dosing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id TEXT,
                drug_name TEXT,
                gfr_category TEXT,
                dose_adjustment TEXT,
                frequency_adjustment TEXT,
                supplemental_dose_dialysis TEXT,
                monitoring_parameters TEXT,
                precautions TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        # Hepatic dosing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hepatic_dosing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id TEXT,
                drug_name TEXT,
                hepatic_category TEXT,
                dose_adjustment TEXT,
                contraindicated INTEGER,
                monitoring_parameters TEXT,
                precautions TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        # Pediatric dosing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pediatric_dosing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id TEXT,
                drug_name TEXT,
                age_group TEXT,
                min_age TEXT,
                max_age TEXT,
                weight_based_formula TEXT,
                age_based_dose TEXT,
                max_single_dose TEXT,
                max_daily_dose TEXT,
                frequency TEXT,
                route TEXT,
                precautions TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        # Formulations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS formulations (
                id TEXT PRIMARY KEY,
                drug_id TEXT,
                drug_name TEXT,
                formulation_type TEXT,
                strength TEXT,
                route TEXT,
                manufacturer TEXT,
                is_generic INTEGER,
                prescription_required INTEGER,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        # Pricing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drug_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id TEXT,
                drug_name TEXT,
                formulation TEXT,
                strength TEXT,
                manufacturer TEXT,
                is_generic INTEGER,
                mrp REAL,
                pharmacy_price REAL,
                online_price REAL,
                nlem_drug INTEGER,
                price_controlled INTEGER,
                last_updated TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        # Generic equivalents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generic_equivalents (
                drug_id TEXT PRIMARY KEY,
                brand_name TEXT,
                generic_name TEXT,
                generic_alternatives TEXT,
                bioequivalent INTEGER,
                cost_savings_percent REAL,
                therapeutic_equivalence_code TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        # Drug allergies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drug_allergies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id TEXT,
                drug_name TEXT,
                drug_class TEXT,
                cross_reactive_classes TEXT,
                cross_reactive_drugs TEXT,
                safe_alternatives TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        # Contraindications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contraindications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id TEXT,
                drug_name TEXT,
                condition TEXT,
                severity TEXT,
                rationale TEXT,
                alternatives TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)

        self.conn.commit()

    def _create_indexes(self):
        """Create database indexes for performance."""
        cursor = self.conn.cursor()

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_drugs_generic ON drugs(generic_name)",
            "CREATE INDEX IF NOT EXISTS idx_drugs_class ON drugs(therapeutic_class)",
            "CREATE INDEX IF NOT EXISTS idx_interactions_drug1 ON drug_interactions(drug1_id)",
            "CREATE INDEX IF NOT EXISTS idx_interactions_drug2 ON drug_interactions(drug2_id)",
            "CREATE INDEX IF NOT EXISTS idx_interactions_severity ON drug_interactions(severity)",
            "CREATE INDEX IF NOT EXISTS idx_formulations_drug ON formulations(drug_id)",
            "CREATE INDEX IF NOT EXISTS idx_prices_drug ON drug_prices(drug_id)",
        ]

        for index in indexes:
            cursor.execute(index)

        self.conn.commit()

    def add_drug(self, drug: Drug) -> bool:
        """
        Add a drug to the database.

        Args:
            drug: Drug object to add.

        Returns:
            True if successful.
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO drugs (
                    id, generic_name, brand_names, indian_brand_names,
                    therapeutic_class, mechanism_of_action, indications,
                    contraindications, common_side_effects, serious_side_effects,
                    rxcui, atc_code, adult_dose, max_dose_per_day,
                    pregnancy_category, lactation_risk, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drug.id,
                drug.generic_name,
                json.dumps(drug.brand_names),
                json.dumps(drug.indian_brand_names),
                drug.therapeutic_class.value,
                drug.mechanism_of_action,
                json.dumps(drug.indications),
                json.dumps(drug.contraindications),
                json.dumps(drug.common_side_effects),
                json.dumps(drug.serious_side_effects),
                drug.rxcui,
                drug.atc_code,
                drug.adult_dose,
                drug.max_dose_per_day,
                drug.pregnancy_category.value,
                drug.lactation_risk.value,
                drug.created_at.isoformat(),
                drug.updated_at.isoformat(),
            ))

            # Update FTS index
            cursor.execute("""
                INSERT OR REPLACE INTO drugs_fts (
                    id, generic_name, brand_names, indian_brand_names, therapeutic_class
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                drug.id,
                drug.generic_name,
                " ".join(drug.brand_names),
                " ".join(drug.indian_brand_names),
                drug.therapeutic_class.value,
            ))

            self.conn.commit()
            logger.info(f"Added drug: {drug.generic_name} ({drug.id})")
            return True

        except Exception as e:
            logger.error(f"Error adding drug {drug.id}: {e}")
            return False

    def get_drug(self, drug_id: str) -> Optional[Drug]:
        """
        Get a drug by ID.

        Args:
            drug_id: Drug identifier.

        Returns:
            Drug object or None if not found.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM drugs WHERE id = ?", (drug_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_drug(row)

    def search_drugs(
        self,
        query: str,
        therapeutic_class: Optional[str] = None,
        limit: int = 20,
    ) -> list[DrugSearchResult]:
        """
        Search drugs by name with fuzzy matching.

        Args:
            query: Search query.
            therapeutic_class: Filter by therapeutic class.
            limit: Maximum results to return.

        Returns:
            List of search results.
        """
        results = []

        # Exact match search
        exact_results = self._search_exact(query, therapeutic_class, limit)
        results.extend(exact_results)

        # Full-text search if not enough results
        if len(results) < limit:
            fts_results = self._search_fts(query, therapeutic_class, limit - len(results))
            results.extend(fts_results)

        # Fuzzy match if still not enough results
        if len(results) < limit // 2:
            fuzzy_results = self._search_fuzzy(query, therapeutic_class, limit - len(results))
            results.extend(fuzzy_results)

        # Remove duplicates and sort by relevance
        seen = set()
        unique_results = []
        for result in results:
            if result.drug_id not in seen:
                seen.add(result.drug_id)
                unique_results.append(result)

        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return unique_results[:limit]

    def _search_exact(
        self,
        query: str,
        therapeutic_class: Optional[str],
        limit: int,
    ) -> list[DrugSearchResult]:
        """Exact match search."""
        cursor = self.conn.cursor()
        query_lower = query.lower()

        sql = """
            SELECT id, generic_name, brand_names, therapeutic_class
            FROM drugs
            WHERE LOWER(generic_name) = ?
        """
        params = [query_lower]

        if therapeutic_class:
            sql += " AND therapeutic_class = ?"
            params.append(therapeutic_class)

        sql += f" LIMIT {limit}"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        return [
            DrugSearchResult(
                drug_id=row["id"],
                generic_name=row["generic_name"],
                brand_names=json.loads(row["brand_names"]) if row["brand_names"] else [],
                therapeutic_class=row["therapeutic_class"],
                relevance_score=1.0,
                match_type="exact",
            )
            for row in rows
        ]

    def _search_fts(
        self,
        query: str,
        therapeutic_class: Optional[str],
        limit: int,
    ) -> list[DrugSearchResult]:
        """Full-text search."""
        cursor = self.conn.cursor()

        # Use FTS5 MATCH for full-text search
        sql = """
            SELECT d.id, d.generic_name, d.brand_names, d.therapeutic_class
            FROM drugs d
            JOIN drugs_fts fts ON d.id = fts.id
            WHERE drugs_fts MATCH ?
        """
        params = [query]

        if therapeutic_class:
            sql += " AND d.therapeutic_class = ?"
            params.append(therapeutic_class)

        sql += f" LIMIT {limit}"

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [
                DrugSearchResult(
                    drug_id=row["id"],
                    generic_name=row["generic_name"],
                    brand_names=json.loads(row["brand_names"]) if row["brand_names"] else [],
                    therapeutic_class=row["therapeutic_class"],
                    relevance_score=0.8,
                    match_type="fts",
                )
                for row in rows
            ]
        except Exception as e:
            logger.warning(f"FTS search failed: {e}")
            return []

    def _search_fuzzy(
        self,
        query: str,
        therapeutic_class: Optional[str],
        limit: int,
    ) -> list[DrugSearchResult]:
        """Fuzzy matching search."""
        cursor = self.conn.cursor()

        sql = "SELECT id, generic_name, brand_names, therapeutic_class FROM drugs"
        params = []

        if therapeutic_class:
            sql += " WHERE therapeutic_class = ?"
            params.append(therapeutic_class)

        sql += " LIMIT 500"  # Limit candidates for fuzzy matching

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Calculate similarity scores
        results = []
        query_lower = query.lower()

        for row in rows:
            generic_lower = row["generic_name"].lower()
            brand_names = json.loads(row["brand_names"]) if row["brand_names"] else []

            # Check generic name similarity
            score = SequenceMatcher(None, query_lower, generic_lower).ratio()

            # Check brand names
            for brand in brand_names:
                brand_score = SequenceMatcher(None, query_lower, brand.lower()).ratio()
                score = max(score, brand_score)

            # Only include if similarity > 0.6
            if score > 0.6:
                results.append(
                    DrugSearchResult(
                        drug_id=row["id"],
                        generic_name=row["generic_name"],
                        brand_names=brand_names,
                        therapeutic_class=row["therapeutic_class"],
                        relevance_score=score * 0.6,  # Scale down fuzzy scores
                        match_type="fuzzy",
                    )
                )

        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    def get_drugs_by_class(self, therapeutic_class: str) -> list[Drug]:
        """Get all drugs in a therapeutic class."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM drugs WHERE therapeutic_class = ?",
            (therapeutic_class,)
        )
        rows = cursor.fetchall()
        return [self._row_to_drug(row) for row in rows]

    def add_interaction(self, interaction: DrugInteraction) -> bool:
        """Add a drug interaction."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO drug_interactions (
                    id, drug1_id, drug1_name, drug2_id, drug2_name,
                    severity, mechanism, clinical_significance,
                    management_strategy, alternative_suggestions,
                    source, evidence_level, references
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction.id,
                interaction.drug1_id,
                interaction.drug1_name,
                interaction.drug2_id,
                interaction.drug2_name,
                interaction.severity.value,
                interaction.mechanism,
                interaction.clinical_significance,
                interaction.management_strategy,
                json.dumps(interaction.alternative_suggestions),
                interaction.source,
                interaction.evidence_level,
                json.dumps(interaction.references),
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding interaction: {e}")
            return False

    def get_interactions(self, drug_id: str) -> list[DrugInteraction]:
        """Get all interactions for a drug."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM drug_interactions
            WHERE drug1_id = ? OR drug2_id = ?
        """, (drug_id, drug_id))
        rows = cursor.fetchall()
        return [self._row_to_interaction(row) for row in rows]

    def check_interaction(self, drug1_id: str, drug2_id: str) -> Optional[DrugInteraction]:
        """Check for interaction between two drugs."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM drug_interactions
            WHERE (drug1_id = ? AND drug2_id = ?)
               OR (drug1_id = ? AND drug2_id = ?)
        """, (drug1_id, drug2_id, drug2_id, drug1_id))
        row = cursor.fetchone()
        return self._row_to_interaction(row) if row else None

    def _row_to_drug(self, row: sqlite3.Row) -> Drug:
        """Convert database row to Drug object."""
        return Drug(
            id=row["id"],
            generic_name=row["generic_name"],
            brand_names=json.loads(row["brand_names"]) if row["brand_names"] else [],
            indian_brand_names=json.loads(row["indian_brand_names"]) if row["indian_brand_names"] else [],
            therapeutic_class=TherapeuticClass(row["therapeutic_class"]),
            mechanism_of_action=row["mechanism_of_action"] or "",
            indications=json.loads(row["indications"]) if row["indications"] else [],
            contraindications=json.loads(row["contraindications"]) if row["contraindications"] else [],
            common_side_effects=json.loads(row["common_side_effects"]) if row["common_side_effects"] else [],
            serious_side_effects=json.loads(row["serious_side_effects"]) if row["serious_side_effects"] else [],
            rxcui=row["rxcui"],
            atc_code=row["atc_code"],
            adult_dose=row["adult_dose"],
            max_dose_per_day=row["max_dose_per_day"],
            pregnancy_category=PregnancyCategory(row["pregnancy_category"]) if row["pregnancy_category"] else PregnancyCategory.UNKNOWN,
            lactation_risk=LactationRisk(row["lactation_risk"]) if row["lactation_risk"] else LactationRisk.UNKNOWN,
        )

    def _row_to_interaction(self, row: sqlite3.Row) -> DrugInteraction:
        """Convert database row to DrugInteraction object."""
        return DrugInteraction(
            id=row["id"],
            drug1_id=row["drug1_id"],
            drug1_name=row["drug1_name"],
            drug2_id=row["drug2_id"],
            drug2_name=row["drug2_name"],
            severity=InteractionSeverity(row["severity"]),
            mechanism=row["mechanism"],
            clinical_significance=row["clinical_significance"],
            management_strategy=row["management_strategy"],
            alternative_suggestions=json.loads(row["alternative_suggestions"]) if row["alternative_suggestions"] else [],
            source=row["source"],
            evidence_level=row["evidence_level"],
            references=json.loads(row["references"]) if row["references"] else [],
        )

    def get_database_stats(self) -> dict:
        """Get database statistics."""
        cursor = self.conn.cursor()

        stats = {}

        # Count drugs
        cursor.execute("SELECT COUNT(*) FROM drugs")
        stats["total_drugs"] = cursor.fetchone()[0]

        # Count interactions
        cursor.execute("SELECT COUNT(*) FROM drug_interactions")
        stats["total_interactions"] = cursor.fetchone()[0]

        # Count by therapeutic class
        cursor.execute("""
            SELECT therapeutic_class, COUNT(*) as count
            FROM drugs
            GROUP BY therapeutic_class
        """)
        stats["drugs_by_class"] = {row[0]: row[1] for row in cursor.fetchall()}

        return stats

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
