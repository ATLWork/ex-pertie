"""
Translation Rule PDF Parser.

Parses PDF documents containing translation rules and generates structured rules using AI.
"""

import json
import re
from typing import Any, Dict, List, Optional
from io import BytesIO

from loguru import logger

from app.core.config import settings
from app.schemas.translation import TranslationRuleCreate


# Prompt for parsing translation rules from PDF content
RULE_PARSING_PROMPT = """You are an expert at analyzing hotel translation rule documents.

Your task is to extract structured translation rules from the following document content.

Document Content:
---

{content}

---

Please analyze this document and extract all translation rules in JSON format. The rules should be structured as follows:

{{
    "rules": [
        {{
            "name": "rule name - make it descriptive and unique",
            "source_lang": "zh",
            "target_lang": "en",
            "field_name": "field this rule applies to (e.g., room_type, amenity, hotel_name)",
            "rule_type": "direct",  # direct means direct text replacement/mapping
            "rule_value": JSON string containing the actual mappings or rules
        }}
    ],
    "summary": "Brief summary of what this document contains",
    "document_type": "Type of document (e.g., SOP, Guidelines, Standard)"
}}

Important rules for parsing:
1. Extract specific translation mappings (e.g., "大床" -> "King Bed" or "King Suite")
2. Extract formatting rules (e.g., bed type naming conventions, amenity naming)
3. Extract prohibited terms or expressions
4. Extract field-specific rules
5. Each rule should be atomic and focused on one aspect

Rule value examples:
- For room types: {{"mappings": {{"大床": "King Suite", "双床": "Twin Executive"}}}}
- For amenities: {{"mappings": {{"免费WiFi": "Complimentary Wi-Fi", "停车场": "Complimentary Parking"}}}}
- For naming conventions: {{"pattern": "Use 'Suite' not 'Standard' for bed types"}}

Return only valid JSON without any markdown formatting.
"""


class TranslationRuleParser:
    """
    Parser for translation rule PDF documents.

    Extracts structured rules from PDF files using AI.
    """

    def __init__(self):
        """Initialize the parser."""
        self._deepseek_client = None

    @property
    def deepseek_client(self):
        """Lazy load DeepSeek client."""
        if self._deepseek_client is None:
            from app.services.translation.ai_client import get_deepseek_client
            self._deepseek_client = get_deepseek_client()
        return self._deepseek_client

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract text content from PDF file.

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            Extracted text content
        """
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            result = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(result)} characters from PDF")
            return result

        except ImportError:
            logger.error("pdfplumber not installed. Please install with: pip install pdfplumber")
            raise ImportError("PDF parsing library not available. Please install pdfplumber.")
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise

    def parse_content_with_ai(self, content: str) -> Dict[str, Any]:
        """
        Parse extracted content using AI to generate structured rules.

        Args:
            content: Extracted text content from PDF

        Returns:
            Parsed rules and metadata
        """
        import httpx

        if not settings.AI_API_KEY:
            raise ValueError("AI API key not configured")

        prompt = RULE_PARSING_PROMPT.format(content=content[:15000])  # Limit content size

        payload = {
            "model": settings.AI_MODEL or "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing hotel translation rule documents.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 4000,
            "temperature": 0.2,
        }

        try:
            response = httpx.post(
                f"{settings.AI_API_BASE_URL}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.AI_API_KEY}",
                },
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()

            content_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Extract JSON from response
            json_str = self._extract_json(content_text)
            if json_str:
                parsed = json.loads(json_str)
                return parsed

            raise ValueError("Failed to parse AI response as JSON")

        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            raise

    def _extract_json(self, content: str) -> Optional[str]:
        """Extract JSON string from content."""
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            return content[start:end]

        return None

    def create_rules_from_parsed(
        self, parsed_data: Dict[str, Any], source_file: str
    ) -> List[TranslationRuleCreate]:
        """
        Create TranslationRuleCreate objects from parsed data.

        Args:
            parsed_data: Parsed rules from AI
            source_file: Source PDF filename

        Returns:
            List of TranslationRuleCreate objects
        """
        rules = []
        parsed_rules = parsed_data.get("rules", [])

        for rule in parsed_rules:
            try:
                rule_create = TranslationRuleCreate(
                    name=f"{source_file}: {rule.get('name', 'Unnamed Rule')}",
                    source_lang=rule.get("source_lang", "zh"),
                    target_lang=rule.get("target_lang", "en"),
                    field_name=rule.get("field_name", "general"),
                    rule_type=rule.get("rule_type", "direct"),
                    rule_value=json.dumps(rule.get("rule_value", {}), ensure_ascii=False),
                    is_active=True,
                )
                rules.append(rule_create)
            except Exception as e:
                logger.warning(f"Failed to create rule: {e}")
                continue

        return rules

    async def parse_pdf(
        self,
        pdf_content: bytes,
        source_filename: str,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        Parse PDF document and generate structured rules.

        Args:
            pdf_content: PDF file content
            source_filename: Original filename
            use_ai: Whether to use AI for parsing (if False, uses regex only)

        Returns:
            Parsing result with extracted rules
        """
        # Step 1: Extract text from PDF
        logger.info(f"Parsing PDF: {source_filename}")
        text_content = self.extract_text_from_pdf(pdf_content)

        if not text_content:
            return {
                "success": False,
                "rules_count": 0,
                "rules": [],
                "error": "No text content extracted from PDF",
            }

        # Step 2: Parse with AI
        if use_ai:
            try:
                parsed_data = self.parse_content_with_ai(text_content)
                rules = self.create_rules_from_parsed(parsed_data, source_filename)

                return {
                    "success": True,
                    "rules_count": len(rules),
                    "rules": [r.model_dump() for r in rules],
                    "summary": parsed_data.get("summary", ""),
                    "document_type": parsed_data.get("document_type", ""),
                    "raw_content_length": len(text_content),
                }
            except Exception as e:
                logger.error(f"AI parsing failed, falling back to regex: {e}")
                use_ai = False

        # Fallback: Use regex-based extraction
        if not use_ai:
            rules = self._extract_rules_with_regex(text_content, source_filename)
            return {
                "success": True,
                "rules_count": len(rules),
                "rules": [r.model_dump() for r in rules],
                "summary": f"Extracted {len(rules)} rules using pattern matching",
                "document_type": "Unknown",
                "raw_content_length": len(text_content),
                "warning": "Used basic pattern matching - AI parsing recommended for better results",
            }

    def _extract_rules_with_regex(
        self, content: str, source_file: str
    ) -> List[TranslationRuleCreate]:
        """
        Extract rules using regex patterns as fallback.

        Handles SOP document formats like:
        - 高级大床房 Superior King Room
        - 例：高级城景大床房 Superior King Room with City View
        - 无景观/设施房型
        """
        rules = []
        extracted_mappings = {}

        # Pattern 1: Chinese phrase followed by English (common in SOP)
        # e.g., "高级大床房 Superior King Room" or "大床 King Bed"
        pattern1 = r'([\u4e00-\u9fff]+(?:床|房|厅|卫|厨|餐|WiFi|网络|停车|健身|SPA|泳池)[^\n]*?)\s+([A-Za-z][A-Za-z\s,]+?)(?:\n|$)'
        for match in re.finditer(pattern1, content):
            zh = match.group(1).strip()
            en = match.group(2).strip()
            if zh and en and 1 < len(zh) < 50 and 2 < len(en) < 100:
                key = f"{zh}|{en}"
                if key not in extracted_mappings:
                    extracted_mappings[key] = (zh, en, "direct")

        # Pattern 2: Room type naming conventions from SOP
        # e.g., "深睡（Deep Sleep）+ 非套房房型公式"
        pattern2 = r'([\u4e00-\u9fff（）()\s]+)[（(]([A-Za-z\s]+)[)）]\s*[+]'
        for match in re.finditer(pattern2, content):
            zh = match.group(1).strip()
            en = match.group(2).strip()
            if zh and en:
                key = f"{zh}|{en}"
                if key not in extracted_mappings:
                    extracted_mappings[key] = (zh, en, "direct")

        # Pattern 3: Common hotel terms in Chinese followed by English
        terms = [
            (r'大床', 'King Bed'),
            (r'双床', 'Twin Beds'),
            (r'单人床', 'Single Bed'),
            (r'标准', 'Standard'),
            (r'高级', 'Superior'),
            (r'豪华', 'Deluxe'),
            (r'套房', 'Suite'),
            (r'公寓', 'Apartment'),
            (r'城景', 'City View'),
            (r'园景', 'Garden View'),
            (r'湖景', 'Lake View'),
            (r'海景', 'Sea View'),
            (r'享浴', 'with Bathtub'),
            (r'深睡', 'Deep Sleep'),
            (r'免费WiFi', 'Complimentary Wi-Fi'),
            (r'停车场', 'Complimentary Parking'),
            (r'健身房', 'Fitness Center'),
            (r'会议室', 'Meeting Room'),
            (r'餐厅', 'Restaurant'),
        ]

        for zh_term, en_term in terms:
            if zh_term in content and en_term in content:
                key = f"{zh_term}|{en_term}"
                if key not in extracted_mappings:
                    extracted_mappings[key] = (zh_term, en_term, "direct")

        # Create rules from extracted mappings
        for key, (zh, en, rtype) in extracted_mappings.items():
            field_name = self._infer_field_name(zh, content)
            try:
                rule = TranslationRuleCreate(
                    name=f"{source_file}: {zh} -> {en}",
                    source_lang="zh",
                    target_lang="en",
                    field_name=field_name,
                    rule_type=rtype,
                    rule_value=json.dumps({
                        "mappings": {zh: en},
                        "source": "pdf_regex_extraction"
                    }, ensure_ascii=False),
                    is_active=True,
                )
                rules.append(rule)
            except Exception:
                continue

        return rules[:100]  # Limit to 100 rules

    def _infer_field_name(self, text: str, context: str) -> str:
        """Infer field name based on text content."""
        text_lower = text.lower()
        context_lower = context.lower()

        if any(word in text_lower for word in ["床", "room", "套房", "房"]):
            return "room_type"
        if any(word in text_lower for word in ["wifi", "网络", "停车", "gym", "健身"]):
            return "amenity"
        if any(word in text_lower for word in ["酒店", "hotel"]):
            return "hotel_name"
        if any(word in text_lower for word in ["早餐", "breakfast", "餐"]):
            return "meal"
        if any(word in text_lower for word in ["政策", "policy", "取消"]):
            return "policy"

        return "general"


# Singleton instance
_rule_parser: Optional[TranslationRuleParser] = None


def get_rule_parser() -> TranslationRuleParser:
    """Get or create TranslationRuleParser instance."""
    global _rule_parser
    if _rule_parser is None:
        _rule_parser = TranslationRuleParser()
    return _rule_parser
