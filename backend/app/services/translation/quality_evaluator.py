"""
Translation Quality Evaluation Service.

Provides comprehensive quality assessment for translations including:
- Accuracy (translation correctness)
- Professionalism (domain terminology usage)
- Localization (cultural adaptation)
- Completeness (full translation vs partial)
- Booking match rate (similarity to Booking.com references)
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from loguru import logger


@dataclass
class QualityScores:
    """Quality evaluation scores."""

    accuracy: float = 0.0  # 0-100
    professionalism: float = 0.0  # 0-100
    localization: float = 0.0  # 0-100
    completeness: float = 0.0  # 0-100
    booking_match_rate: float = 0.0  # 0-100
    overall: float = 0.0  # 0-100

    def to_dict(self) -> Dict[str, float]:
        return {
            "accuracy": self.accuracy,
            "professionalism": self.professionalism,
            "localization": self.localization,
            "completeness": self.completeness,
            "booking_match_rate": self.booking_match_rate,
            "overall": self.overall,
        }


@dataclass
class QualityEvaluation:
    """Full quality evaluation result."""

    scores: QualityScores
    issues: List[str]  # List of identified issues
    suggestions: List[str]  # Suggestions for improvement
    reference_matches: Dict[str, float]  # Similarity to reference translations


class TranslationQualityEvaluator:
    """
    Evaluates translation quality across multiple dimensions.
    """

    def __init__(self):
        """Initialize evaluator."""
        self._glossary_service = None
        self._booking_reference_service = None

    @property
    def glossary_service(self):
        """Lazy load glossary service."""
        if self._glossary_service is None:
            from app.services.glossary import glossary
            self._glossary_service = glossary
        return self._glossary_service

    @property
    def booking_reference_service(self):
        """Lazy load booking reference service."""
        if self._booking_reference_service is None:
            from app.services.booking_reference_service import booking_reference
            self._booking_reference_service = booking_reference
        return self._booking_reference_service

    async def evaluate(
        self,
        original_text: str,
        translated_text: str,
        source_lang: str = "zh",
        target_lang: str = "en",
        db=None,
    ) -> QualityEvaluation:
        """
        Evaluate translation quality.

        Args:
            original_text: Original source text
            translated_text: Translated text
            source_lang: Source language code
            target_lang: Target language code
            db: Optional database session for reference lookups

        Returns:
            QualityEvaluation with scores and suggestions
        """
        scores = QualityScores()
        issues = []
        suggestions = []
        reference_matches = {}

        # 1. Calculate accuracy (basic checks)
        accuracy_score = self._evaluate_accuracy(original_text, translated_text)
        scores.accuracy = accuracy_score

        # 2. Calculate completeness
        completeness_score = self._evaluate_completeness(original_text, translated_text)
        scores.completeness = completeness_score
        if completeness_score < 80:
            issues.append("Translation appears incomplete or truncated")
            suggestions.append("Review full translation to ensure all content is captured")

        # 3. Calculate professionalism (terminology usage)
        professionalism_score = 0.0
        if db:
            try:
                professionalism_score = await self._evaluate_professionalism(
                    original_text, translated_text, source_lang, target_lang, db
                )
                scores.professionalism = professionalism_score
            except Exception as e:
                logger.warning(f"Professionalism evaluation failed: {e}")
                scores.professionalism = 50.0  # Default neutral score
        else:
            scores.professionalism = 50.0

        # 4. Calculate localization
        localization_score = self._evaluate_localization(translated_text, target_lang)
        scores.localization = localization_score
        if localization_score < 60:
            issues.append("Translation may not be properly localized")
            suggestions.append("Consider adapting phrasing for target locale")

        # 5. Calculate Booking match rate
        booking_match_rate = 0.0
        if db:
            try:
                booking_match_rate = await self._evaluate_booking_match(
                    original_text, translated_text, source_lang, target_lang, db
                )
                reference_matches["booking"] = booking_match_rate
            except Exception as e:
                logger.warning(f"Booking match evaluation failed: {e}")
        scores.booking_match_rate = booking_match_rate

        # Calculate overall score (weighted average)
        scores.overall = (
            scores.accuracy * 0.25
            + scores.professionalism * 0.25
            + scores.localization * 0.15
            + scores.completeness * 0.20
            + scores.booking_match_rate * 0.15
        )

        return QualityEvaluation(
            scores=scores,
            issues=issues,
            suggestions=suggestions,
            reference_matches=reference_matches,
        )

    def _evaluate_accuracy(
        self, original_text: str, translated_text: str
    ) -> float:
        """
        Evaluate translation accuracy.

        Checks for:
        - Untranslated content
        - Obvious errors
        - Format preservation
        """
        if not translated_text:
            return 0.0

        score = 100.0

        # Check if text is empty or very short (likely an error)
        if len(translated_text.strip()) < 2:
            return 10.0

        # Check for significant length mismatch (might indicate truncation)
        original_len = len(original_text)
        translated_len = len(translated_text)

        # Allow some variance but flag large differences
        if original_len > 10:
            ratio = translated_len / original_len
            if ratio < 0.5:
                score -= 30  # Significant truncation
            elif ratio > 3.0:
                score -= 20  # Unexpected expansion

        # Check for untranslated Chinese characters (common error)
        # Count Chinese characters in original
        chinese_chars = sum(1 for c in original_text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars > 0:
            # Check if translated text still contains Chinese
            translated_chinese = sum(1 for c in translated_text if '\u4e00' <= c <= '\u9fff')
            if translated_chinese > chinese_chars * 0.5:
                score -= 25  # Likely untranslated content

        # Check for placeholder patterns that weren't translated
        placeholder_patterns = ["{{", "}}", "[[", "]]", "[TODO]", "[PLACEHOLDER]"]
        for pattern in placeholder_patterns:
            if pattern in original_text and pattern in translated_text:
                score -= 10

        return max(0.0, min(100.0, score))

    def _evaluate_completeness(
        self, original_text: str, translated_text: str
    ) -> float:
        """
        Evaluate translation completeness.

        Checks if all content was translated.
        """
        if not original_text or not translated_text:
            return 0.0 if not translated_text else 50.0

        # Word/character count comparison
        # Chinese characters are roughly equivalent to words
        original_words = len(original_text)
        translated_words = len(translated_text)

        if original_words == 0:
            return 50.0

        ratio = translated_words / original_words

        # Ideal ratio is around 1.0-1.5 for zh-en (Chinese tends to be more compact)
        if 0.8 <= ratio <= 2.0:
            return 100.0
        elif 0.5 <= ratio < 0.8:
            return 75.0
        elif 2.0 < ratio <= 3.0:
            return 80.0
        else:
            # Very short or very long translation
            return max(20.0, 100.0 - abs(ratio - 1.0) * 30)

    async def _evaluate_professionalism(
        self,
        original_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        db,
    ) -> float:
        """
        Evaluate professionalism (proper use of domain terminology).

        Checks if known terminology from glossary was properly used.
        """
        terms = await self.glossary_service.get_active_terms(
            db, source_lang=source_lang, target_lang=target_lang
        )

        if not terms:
            return 50.0  # No terminology data available, neutral score

        matched = 0
        total = 0

        for term in terms:
            if term.term in original_text:
                total += 1
                # Check if the translation uses the correct terminology
                if term.translation.lower() in translated_text.lower():
                    matched += 1

        if total == 0:
            return 50.0

        # Score based on terminology match rate
        match_rate = (matched / total) * 100
        return match_rate

    def _evaluate_localization(
        self, translated_text: str, target_lang: str
    ) -> float:
        """
        Evaluate localization quality.

        Checks for proper cultural adaptation and locale-specific patterns.
        """
        if not translated_text:
            return 0.0

        score = 70.0  # Base score

        # English-specific checks
        if target_lang == "en":
            # Check for common Chinese phrasing that wasn't localized
            chinese_patterns_in_english = [
                "is contains", "is has", "will be get",
                "please your", "thank for your",
            ]
            lower_text = translated_text.lower()
            for pattern in chinese_patterns_in_english:
                if pattern in lower_text:
                    score -= 10

            # Check for proper capitalization at start of sentence
            sentences = translated_text.split('.')
            for i, sent in enumerate(sentences[:3]):  # Check first 3 sentences
                sent = sent.strip()
                if sent and sent[0].islower() and i > 0:
                    score -= 5

            # Check for proper spacing after punctuation
            if "  " in translated_text:  # Double spaces
                score -= 5

            # Check for missing articles (common in Chinese-influenced English)
            # Simple heuristic: words starting with capital letters that shouldn't
            words = translated_text.split()
            problematic_count = sum(1 for w in words if w and w[0].isupper() and len(w) > 1 and w not in ['I', 'DNA', 'RNA', 'GDP'])
            if problematic_count > 3:
                score -= 10

        return max(0.0, min(100.0, score))

    async def _evaluate_booking_match(
        self,
        original_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        db,
    ) -> float:
        """
        Evaluate similarity to Booking.com reference translations.

        Returns a score based on how closely the translation matches
        known Booking.com reference translations for similar content.
        """
        # Look up reference translations
        ref = await self.booking_reference_service.find_by_source_text(
            db,
            source_text=original_text,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        if not ref or not ref.booking_translation:
            # Try similar match
            similar_refs = await self.booking_reference_service.find_similar(
                db,
                source_text=original_text,
                source_lang=source_lang,
                target_lang=target_lang,
                limit=1,
            )
            if similar_refs and similar_refs[0].booking_translation:
                ref = similar_refs[0]
            else:
                return 0.0  # No reference available

        booking_translation = ref.booking_translation

        # Calculate similarity using simple word overlap
        translated_words = set(translated_text.lower().split())
        booking_words = set(booking_translation.lower().split())

        if not translated_words or not booking_words:
            return 0.0

        # Jaccard similarity
        intersection = translated_words & booking_words
        union = translated_words | booking_words
        similarity = len(intersection) / len(union) if union else 0.0

        return similarity * 100

    async def evaluate_batch(
        self,
        translations: List[Dict[str, str]],
        source_lang: str = "zh",
        target_lang: str = "en",
        db=None,
    ) -> List[QualityEvaluation]:
        """
        Evaluate quality for a batch of translations.

        Args:
            translations: List of dicts with 'original' and 'translated' keys
            source_lang: Source language code
            target_lang: Target language code
            db: Optional database session

        Returns:
            List of QualityEvaluation results
        """
        results = []
        for item in translations:
            evaluation = await self.evaluate(
                original_text=item.get("original", ""),
                translated_text=item.get("translated", ""),
                source_lang=source_lang,
                target_lang=target_lang,
                db=db,
            )
            results.append(evaluation)

        return results


# Singleton instance
_evaluator: Optional[TranslationQualityEvaluator] = None


def get_quality_evaluator() -> TranslationQualityEvaluator:
    """Get or create quality evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = TranslationQualityEvaluator()
    return _evaluator