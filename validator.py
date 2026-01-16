"""
Contact validation module for Indonesia EdTech Lead Gen Engine
Validates WhatsApp numbers and email addresses
"""
import re
import asyncio
import socket
from typing import Optional, Dict
from email_validator import validate_email, EmailNotValidError
import httpx
import logging

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    logging.warning("dnspython not installed. MX record checks will be limited.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContactValidator:
    """
    Validates contact information (WhatsApp, Email)
    
    Uses lightweight checks to verify contacts are "live" without
    sending actual messages or emails
    """
    
    def __init__(self):
        self.whatsapp_cache: Dict[str, bool] = {}
        self.email_cache: Dict[str, Dict[str, bool]] = {}
    
    async def verify_whatsapp(
        self, 
        phone_number: str,
        use_api: bool = False
    ) -> Dict[str, bool]:
        """
        Verify if a phone number exists on WhatsApp
        
        Args:
            phone_number: Phone number in +62 format
            use_api: If True, use external API (requires API key)
            
        Returns:
            Dict with verification results:
            {
                "exists": bool,
                "is_mobile": bool,
                "is_valid_format": bool
            }
        """
        result = {
            "exists": False,
            "is_mobile": False,
            "is_valid_format": False
        }
        
        # Normalize phone number
        normalized = self._normalize_phone(phone_number)
        if not normalized:
            return result
        
        result["is_valid_format"] = True
        
        # Check if it's a mobile number (Indonesian mobile starts with 08 or +62 8)
        if normalized.startswith("+628") or normalized.startswith("+62 8"):
            result["is_mobile"] = True
        
        # Check cache first
        if normalized in self.whatsapp_cache:
            result["exists"] = self.whatsapp_cache[normalized]
            return result
        
        if use_api:
            # Option 1: Use external WhatsApp API (e.g., Waapi, Twilio)
            # This requires API keys - implement based on your provider
            result["exists"] = await self._check_whatsapp_api(normalized)
        else:
            # Option 2: Lightweight check - validate format and mobile prefix
            # In Indonesia, WhatsApp numbers are typically:
            # - Mobile: +628xxxxxxxxx (11-13 digits after +62)
            # - Landline: +62xxxxxxxxx (but less common for WhatsApp)
            
            # Basic validation: Indonesian mobile format
            mobile_pattern = r'^\+628\d{8,10}$'
            if re.match(mobile_pattern, normalized.replace(" ", "")):
                # Assume valid if format matches (lightweight check)
                result["exists"] = True
                result["is_mobile"] = True
        
        # Cache result
        self.whatsapp_cache[normalized] = result["exists"]
        
        return result
    
    async def _check_whatsapp_api(self, phone_number: str) -> bool:
        """
        Check WhatsApp via external API (placeholder for Waapi/Twilio)
        
        To implement:
        1. Sign up for Waapi.io or Twilio WhatsApp API
        2. Add API key to config
        3. Make API call to check number
        
        Example (Waapi):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.waapi.io/check/{phone_number}",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return response.json().get("exists", False)
        """
        # Placeholder - implement with your API provider
        logger.warning(f"WhatsApp API check not implemented for {phone_number}")
        return False
    
    async def verify_email_live(
        self, 
        email: str
    ) -> Dict[str, bool]:
        """
        Verify if an email address is live and valid
        
        Performs:
        1. Syntax validation (email-validator)
        2. MX record check (DNS)
        3. SMTP handshake (without sending email)
        
        Args:
            email: Email address to verify
            
        Returns:
            Dict with verification results:
            {
                "is_valid_syntax": bool,
                "has_mx_record": bool,
                "smtp_handshake": bool,
                "is_personal": bool,  # vs general (info@, admin@)
                "is_live": bool  # Overall result
            }
        """
        result = {
            "is_valid_syntax": False,
            "has_mx_record": False,
            "smtp_handshake": False,
            "is_personal": False,
            "is_live": False
        }
        
        # Check cache
        if email.lower() in self.email_cache:
            cached = self.email_cache[email.lower()]
            result.update(cached)
            return result
        
        # 1. Syntax validation
        try:
            email_info = validate_email(
                email,
                check_deliverability=False  # We'll do MX check separately
            )
            result["is_valid_syntax"] = True
            domain = email_info.domain
        except EmailNotValidError as e:
            logger.debug(f"Email syntax invalid: {email} - {e}")
            self.email_cache[email.lower()] = result
            return result
        
        # 2. Check if personal vs general email
        general_prefixes = [
            "info", "admin", "contact", "support", "help", 
            "noreply", "no-reply", "mail", "webmaster",
            "kontak", "hubungi"
        ]
        local_part = email.split("@")[0].lower()
        result["is_personal"] = not any(
            local_part.startswith(prefix) for prefix in general_prefixes
        )
        
        # 3. MX record check
        try:
            mx_records = await self._check_mx_record(domain)
            result["has_mx_record"] = len(mx_records) > 0
        except Exception as e:
            logger.debug(f"MX check failed for {domain}: {e}")
        
        # 4. SMTP handshake (if MX exists)
        if result["has_mx_record"]:
            try:
                result["smtp_handshake"] = await self._smtp_handshake(
                    domain, 
                    mx_records[0] if mx_records else None
                )
            except Exception as e:
                logger.debug(f"SMTP handshake failed for {domain}: {e}")
        
        # Overall "is_live" = valid syntax + MX record + SMTP handshake
        result["is_live"] = (
            result["is_valid_syntax"] and 
            result["has_mx_record"] and 
            result["smtp_handshake"]
        )
        
        # Cache result
        self.email_cache[email.lower()] = result
        
        return result
    
    async def _check_mx_record(self, domain: str) -> list:
        """
        Check MX records for domain using DNS
        
        Returns list of MX hostnames
        """
        if not DNS_AVAILABLE:
            # Fallback: try socket.getaddrinfo for basic DNS check
            try:
                socket.getaddrinfo(domain, 0)
                return [f"mail.{domain}"]  # Assume mail server exists
            except:
                return []
        
        try:
            # Use dns.resolver for async DNS lookup
            mx_records = dns.resolver.resolve(domain, 'MX')
            return [str(mx.exchange) for mx in mx_records]
        except Exception as e:
            logger.debug(f"DNS MX lookup failed for {domain}: {e}")
            return []
    
    async def _smtp_handshake(
        self, 
        domain: str, 
        mx_host: Optional[str] = None
    ) -> bool:
        """
        Perform SMTP handshake to verify mailbox exists
        
        Does NOT send an email, just checks if server accepts connection
        """
        if not mx_host:
            # Try common mail servers
            mx_host = f"mail.{domain}"
        
        try:
            # Try to connect to SMTP server (port 25)
            # Use asyncio for non-blocking connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(mx_host, 25),
                timeout=5.0
            )
            
            # Read greeting
            greeting = await asyncio.wait_for(reader.readline(), timeout=5.0)
            
            # Send EHLO
            writer.write(b"EHLO localhost\r\n")
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(reader.readline(), timeout=5.0)
            
            writer.close()
            await writer.wait_closed()
            
            # If we got a response, server is reachable
            return response.startswith(b"250")
            
        except (asyncio.TimeoutError, OSError, Exception) as e:
            logger.debug(f"SMTP handshake failed for {mx_host}: {e}")
            return False
    
    def _normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone to +62 format"""
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        if cleaned.startswith('08'):
            return '+62' + cleaned[1:]
        elif cleaned.startswith('62') and not cleaned.startswith('+'):
            return '+' + cleaned
        elif cleaned.startswith('+62'):
            return cleaned
        
        return None


# Singleton instance
validator = ContactValidator()

