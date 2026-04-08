"""
AI Translation Enhancement Client (DeepSeek).

Implements T030: AI Model Client (DeepSeek)
Implements T031: AI Translation Polish Prompt Template
"""

import json
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.middleware.exception import ExternalAPIError


class DeepSeekClient:
    """
    DeepSeek AI Client for translation enhancement.

    DeepSeek API is OpenAI-compatible, making integration straightforward.
    """

    DEFAULT_MODEL = "deepseek-chat"
    MAX_TOKENS = 2000
    TEMPERATURE = 0.3  # Lower temperature for more consistent translations

    # Translation enhancement prompt template
    TRANSLATION_PROMPT_TEMPLATE = """You are a professional translator specializing in hotel and hospitality industry terminology.

Your task is to enhance and polish machine-translated text for hotel listings on Expedia platform.

Context:
- Original language: {source_lang}
- Target language: {target_lang}
- Domain: Hotel and hospitality industry
{additional_context}

Original text:
{original_text}

Machine translation:
{machine_translation}

Requirements:
1. Preserve the original meaning accurately
2. Use professional hospitality industry terminology
3. Make the text natural and appealing for international travelers
4. Keep proper nouns, hotel names, and location names unchanged
5. Maintain consistent style throughout

Please provide:
1. Enhanced translation (polished and professional)
2. A brief explanation of major changes (if any)

Response format (JSON):
{{
    "enhanced_translation": "your enhanced translation here",
    "changes": "brief explanation of major changes or 'No significant changes needed'"
}}
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        Initialize DeepSeek client.

        Args:
            api_key: DeepSeek API key
            base_url: API base URL
            model: Model to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.AI_API_KEY
        self.base_url = (base_url or settings.AI_API_BASE_URL).rstrip("/")
        self.model = model or settings.AI_MODEL or self.DEFAULT_MODEL
        self.timeout = timeout

        if not self.api_key:
            logger.warning("DeepSeek API key not configured")

    def _build_headers(self) -> Dict[str, str]:
        """
        Build request headers.

        Returns:
            Headers dictionary
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def build_translation_prompt(
        self,
        original_text: str,
        machine_translation: str,
        source_lang: str = "zh",
        target_lang: str = "en",
        context: Optional[str] = None,
    ) -> str:
        """
        Build translation enhancement prompt.

        Args:
            original_text: Original text
            machine_translation: Machine translation result
            source_lang: Source language
            target_lang: Target language
            context: Additional context

        Returns:
            Formatted prompt string
        """
        additional_context = f"- Additional context: {context}" if context else ""

        return self.TRANSLATION_PROMPT_TEMPLATE.format(
            source_lang=source_lang,
            target_lang=target_lang,
            additional_context=additional_context,
            original_text=original_text,
            machine_translation=machine_translation,
        )

    async def enhance_translation(
        self,
        original_text: str,
        machine_translation: str,
        source_lang: str = "zh",
        target_lang: str = "en",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enhance machine translation using AI.

        Args:
            original_text: Original text
            machine_translation: Machine translation result
            source_lang: Source language
            target_lang: Target language
            context: Additional context

        Returns:
            Enhanced translation result with:
                - enhanced_text: Enhanced translation
                - changes: Explanation of changes
                - raw_response: Raw API response

        Raises:
            ExternalAPIError: If enhancement fails
        """
        if not self.api_key:
            logger.warning("DeepSeek API key not configured, returning original translation")
            return {
                "enhanced_text": machine_translation,
                "changes": "AI enhancement unavailable",
                "raw_response": None,
            }

        prompt = self.build_translation_prompt(
            original_text=original_text,
            machine_translation=machine_translation,
            source_lang=source_lang,
            target_lang=target_lang,
            context=context,
        )

        try:
            result = await self._call_api(prompt)
            return self._parse_enhancement_response(result, machine_translation)

        except ExternalAPIError as e:
            logger.error(f"AI enhancement failed: {e}")
            # Fallback to machine translation
            return {
                "enhanced_text": machine_translation,
                "changes": f"AI enhancement failed: {e.message}",
                "raw_response": None,
            }

    async def _call_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call DeepSeek API.

        Args:
            prompt: Prompt string

        Returns:
            API response dictionary

        Raises:
            ExternalAPIError: If API call fails
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional translator specializing in hotel industry translations.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.MAX_TOKENS,
            "temperature": self.TEMPERATURE,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self._build_headers(),
                    json=payload,
                )

                return self._handle_api_response(response)

        except httpx.TimeoutException:
            raise ExternalAPIError(
                message="AI enhancement request timeout",
                details={"service": "deepseek", "timeout": self.timeout},
            )
        except httpx.RequestError as e:
            raise ExternalAPIError(
                message="AI enhancement request failed",
                details={"service": "deepseek", "error": str(e)},
            )

    def _handle_api_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle API response.

        Args:
            response: HTTP response

        Returns:
            Parsed response dictionary

        Raises:
            ExternalAPIError: If response indicates error
        """
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
            except Exception:
                error_msg = response.text[:200]

            raise ExternalAPIError(
                message=f"AI API error: {error_msg}",
                details={"status_code": response.status_code, "service": "deepseek"},
            )

        return response.json()

    def _parse_enhancement_response(
        self, api_response: Dict[str, Any], fallback_text: str
    ) -> Dict[str, Any]:
        """
        Parse AI enhancement response.

        Args:
            api_response: Raw API response
            fallback_text: Fallback text if parsing fails

        Returns:
            Parsed enhancement result
        """
        try:
            content = api_response.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not content:
                return {
                    "enhanced_text": fallback_text,
                    "changes": "Empty AI response",
                    "raw_response": api_response,
                }

            # Try to parse JSON from response
            # The AI might return markdown code blocks, so we need to extract JSON
            json_str = self._extract_json(content)

            if json_str:
                parsed = json.loads(json_str)
                return {
                    "enhanced_text": parsed.get("enhanced_translation", fallback_text),
                    "changes": parsed.get("changes", ""),
                    "raw_response": api_response,
                }

            # If no JSON found, use the content directly
            return {
                "enhanced_text": content if content else fallback_text,
                "changes": "Direct response used",
                "raw_response": api_response,
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            return {
                "enhanced_text": fallback_text,
                "changes": "Failed to parse AI response",
                "raw_response": api_response,
            }
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return {
                "enhanced_text": fallback_text,
                "changes": f"Parse error: {str(e)}",
                "raw_response": api_response,
            }

    def _extract_json(self, content: str) -> Optional[str]:
        """
        Extract JSON string from content that might be wrapped in markdown.

        Args:
            content: Content string

        Returns:
            JSON string or None
        """
        # Try to find JSON in markdown code block
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        # Try to find JSON in regular code block
        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        # Try to find raw JSON object
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            return content[start:end]

        return None

    async def batch_enhance(
        self,
        items: List[Dict[str, Any]],
        source_lang: str = "zh",
        target_lang: str = "en",
    ) -> List[Dict[str, Any]]:
        """
        Batch enhance multiple translations.

        Args:
            items: List of dicts with original_text and machine_translation
            source_lang: Source language
            target_lang: Target language

        Returns:
            List of enhancement results
        """
        results = []
        for item in items:
            result = await self.enhance_translation(
                original_text=item.get("original_text", ""),
                machine_translation=item.get("machine_translation", ""),
                source_lang=source_lang,
                target_lang=target_lang,
                context=item.get("context"),
            )
            results.append(result)

        return results


# Singleton instance
_deepseek_client: Optional[DeepSeekClient] = None


def get_deepseek_client() -> DeepSeekClient:
    """
    Get or create DeepSeek client instance.

    Returns:
        DeepSeekClient instance
    """
    global _deepseek_client
    if _deepseek_client is None:
        _deepseek_client = DeepSeekClient()
    return _deepseek_client
