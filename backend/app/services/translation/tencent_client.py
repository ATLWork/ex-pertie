"""
Tencent Cloud Translation API Client.

Implements T028: Tencent Cloud Translation API Client
Implements T029: Tencent Cloud Translation Response Parser
"""

import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.middleware.exception import ExternalAPIError


class TencentTranslateClient:
    """
    Tencent Cloud Machine Translation API Client.

    API Documentation: https://cloud.tencent.com/document/api/551/15619
    """

    SERVICE = "tmt"
    VERSION = "2018-03-21"
    HOST = "tmt.tencentcloudapi.com"
    ENDPOINT = f"https://{HOST}"

    # Supported language codes mapping
    LANGUAGE_MAP = {
        "zh": "zh",
        "zh-cn": "zh",
        "zh-tw": "zh-TW",
        "en": "en",
        "ja": "jp",
        "ko": "kr",
        "es": "es",
        "fr": "fr",
        "de": "de",
        "it": "it",
        "pt": "pt",
        "ru": "ru",
        "vi": "vi",
        "th": "th",
        "ms": "ms",
        "ar": "ar",
        "hi": "hi",
    }

    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize Tencent Translation client.

        Args:
            secret_id: Tencent Cloud Secret ID
            secret_key: Tencent Cloud Secret Key
            region: Tencent Cloud region
            timeout: Request timeout in seconds
        """
        self.secret_id = secret_id or settings.TENCENT_SECRET_ID
        self.secret_key = secret_key or settings.TENCENT_SECRET_KEY
        self.region = region or settings.TENCENT_REGION
        self.timeout = timeout or settings.TRANSLATION_TIMEOUT

        if not self.secret_id or not self.secret_key:
            logger.warning("Tencent Cloud credentials not configured")

    def _generate_signature(self, payload: str, timestamp: int) -> str:
        """
        Generate Tencent Cloud API signature.

        Args:
            payload: Request payload string
            timestamp: Request timestamp

        Returns:
            Base64 encoded signature
        """
        # Create signature string
        date_str = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        credential_scope = f"{date_str}/{self.SERVICE}/tc3_request"

        # Step 1: Hash the payload
        hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        # Step 2: Create canonical request
        canonical_request = (
            f"POST\n"
            f"/\n\n"
            f"content-type:application/json\n"
            f"host:{self.HOST}\n\n"
            f"content-type;host\n"
            f"{hashed_payload}"
        )

        # Step 3: Create string to sign
        string_to_sign = (
            f"TC3-HMAC-SHA256\n"
            f"{timestamp}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        # Step 4: Calculate signature
        secret_date = hmac.new(
            f"TC3{self.secret_key}".encode("utf-8"),
            date_str.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        secret_service = hmac.new(
            secret_date, self.SERVICE.encode("utf-8"), hashlib.sha256
        ).digest()
        secret_signing = hmac.new(
            secret_service, b"tc3_request", hashlib.sha256
        ).digest()
        signature = hmac.new(
            secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return signature

    def _build_headers(self, payload: str) -> Dict[str, str]:
        """
        Build request headers with authentication.

        Args:
            payload: Request payload

        Returns:
            Headers dictionary
        """
        timestamp = int(time.time())
        signature = self._generate_signature(payload, timestamp)

        authorization = (
            f"TC3-HMAC-SHA256 "
            f"Credential={self.secret_id}/{datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')}/{self.SERVICE}/tc3_request, "
            f"SignedHeaders=content-type;host, "
            f"Signature={signature}"
        )

        return {
            "Content-Type": "application/json",
            "Host": self.HOST,
            "X-TC-Action": "TextTranslate",
            "X-TC-Version": self.VERSION,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": self.region,
            "Authorization": authorization,
        }

    def _normalize_language_code(self, lang_code: str) -> str:
        """
        Normalize language code to Tencent Cloud format.

        Args:
            lang_code: Input language code

        Returns:
            Normalized language code
        """
        lang_lower = lang_code.lower()
        return self.LANGUAGE_MAP.get(lang_lower, lang_lower)

    async def translate(
        self,
        text: str,
        source_lang: str = "zh",
        target_lang: str = "en",
        project_id: int = 0,
    ) -> Dict[str, Any]:
        """
        Translate text using Tencent Cloud Machine Translation.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            project_id: Project ID (default 0)

        Returns:
            Translation result dictionary with:
                - translated_text: Translated text
                - source: Translation source
                - confidence: Confidence score (if available)

        Raises:
            ExternalAPIError: If translation fails
        """
        if not self.secret_id or not self.secret_key:
            raise ExternalAPIError(
                message="Tencent Cloud credentials not configured",
                details={"service": "tencent_translate"},
            )

        # Normalize language codes
        source = self._normalize_language_code(source_lang)
        target = self._normalize_language_code(target_lang)

        # Build request payload
        payload_dict = {
            "SourceText": text,
            "Source": source,
            "Target": target,
            "ProjectId": project_id,
        }
        payload = json.dumps(payload_dict, ensure_ascii=False)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._build_headers(payload)
                response = await client.post(
                    self.ENDPOINT,
                    content=payload,
                    headers=headers,
                )

                return self._parse_response(response, text)

        except httpx.TimeoutException:
            logger.error(f"Tencent translate timeout for text: {text[:50]}...")
            raise ExternalAPIError(
                message="Translation request timeout",
                details={"service": "tencent_translate", "timeout": self.timeout},
            )
        except httpx.RequestError as e:
            logger.error(f"Tencent translate request error: {e}")
            raise ExternalAPIError(
                message="Translation request failed",
                details={"service": "tencent_translate", "error": str(e)},
            )

    def _parse_response(self, response: httpx.Response, original_text: str) -> Dict[str, Any]:
        """
        Parse Tencent Cloud API response.

        Args:
            response: HTTP response object
            original_text: Original text for reference

        Returns:
            Parsed translation result

        Raises:
            ExternalAPIError: If API returns error
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise ExternalAPIError(
                message="Invalid JSON response from translation service",
                details={"status_code": response.status_code, "response": response.text[:200]},
            )

        # Check for API errors
        if response.status_code != 200:
            error_msg = data.get("Message", "Unknown error")
            error_code = data.get("Code", response.status_code)
            raise ExternalAPIError(
                message=f"Translation API error: {error_msg}",
                details={"code": error_code, "message": error_msg},
            )

        if "Response" not in data:
            raise ExternalAPIError(
                message="Invalid response structure from translation service",
                details={"response": str(data)[:200]},
            )

        resp = data["Response"]

        # Check for errors in response
        if "Error" in resp:
            error = resp["Error"]
            raise ExternalAPIError(
                message=f"Translation failed: {error.get('Message', 'Unknown error')}",
                details={"code": error.get("Code"), "request_id": resp.get("RequestId")},
            )

        # Extract translation result
        translated_text = resp.get("TargetText", "")
        source = resp.get("Source", "")
        target = resp.get("Target", "")
        request_id = resp.get("RequestId", "")

        logger.debug(
            f"Tencent translation completed",
            extra={
                "request_id": request_id,
                "source_lang": source,
                "target_lang": target,
                "original_length": len(original_text),
                "translated_length": len(translated_text),
            },
        )

        return {
            "translated_text": translated_text,
            "source": source,
            "target": target,
            "request_id": request_id,
            "confidence": None,  # Tencent API doesn't provide confidence score
        }

    async def batch_translate(
        self,
        texts: List[str],
        source_lang: str = "zh",
        target_lang: str = "en",
    ) -> List[Dict[str, Any]]:
        """
        Batch translate multiple texts.

        Note: Tencent Cloud doesn't have a native batch API,
        so we process texts sequentially with rate limiting.

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of translation results
        """
        results = []
        for text in texts:
            try:
                result = await self.translate(text, source_lang, target_lang)
                results.append(result)
            except ExternalAPIError as e:
                logger.warning(f"Batch translation failed for text: {text[:30]}... Error: {e}")
                results.append({
                    "translated_text": "",
                    "source": source_lang,
                    "target": target_lang,
                    "error": str(e),
                })

        return results


# Singleton instance
_tencent_client: Optional[TencentTranslateClient] = None


def get_tencent_client() -> TencentTranslateClient:
    """
    Get or create Tencent Translation client instance.

    Returns:
        TencentTranslateClient instance
    """
    global _tencent_client
    if _tencent_client is None:
        _tencent_client = TencentTranslateClient()
    return _tencent_client
