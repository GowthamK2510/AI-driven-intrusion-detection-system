#!/usr/bin/env python3
"""
API Key Detection Tool v1.0
Ethical Security Assessment Tool for Bug Bounty Hunters

DISCLAIMER: This tool is designed for authorized security testing only.
Use only on systems you have explicit permission to test.
Compliance with applicable laws and terms of service is required.
"""

import re
import json
import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright
from mitmproxy import http
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_key_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ApiKeyFinding:
    """Data class to store API key findings"""
    key_type: str
    key_value: str
    source_url: str
    location: str  # DOM, HTTP Request, HTTP Response
    timestamp: datetime

class ApiKeyDetector:
    """Main API key detection engine"""
    
    def __init__(self):
        self.findings: List[ApiKeyFinding] = []
        self.seen_keys: Set[str] = set()
        
        # Common API key patterns (add more based on your needs)
        self.patterns = {
            'AWS_ACCESS_KEY': r'(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}',
            'AWS_SECRET_KEY': r'(?i)aws_(?:secret|access)_key[^\'"]*[\'\"]([a-zA-Z0-9/+]{40})',
            'GOOGLE_API_KEY': r'AIza[0-9A-Za-z\\-_]{35}',
            'GOOGLE_OAUTH': r'[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com',
            'FACEBOOK_ACCESS_TOKEN': r'EAACEdEose0cBA[0-9A-Za-z]+',
            'TWITTER_ACCESS_TOKEN': r'[1-9][0-9]+-[0-9a-zA-Z]{40}',
            'HEROKU_API_KEY': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            'STRIPE_PUBLISHABLE_KEY': r'pk_(?:test|live)_[0-9a-zA-Z]{24}',
            'STRIPE_SECRET_KEY': r'sk_(?:test|live)_[0-9a-zA-Z]{24}',
            'GITHUB_TOKEN': r'ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}',
            'SLACK_TOKEN': r'xox[baprs]-[0-9a-zA-Z]{10,48}',
            'DROPBOX_API_KEY': r'sl\.[A-Za-z0-9\-_=]{128,144}',
            'MAILGUN_API_KEY': r'key-[0-9a-zA-Z]{32}',
            'SENDGRID_API_KEY': r'SG\.[A-Za-z0-9\-_\.]{20,}\.[A-Za-z0-9\-_\.]{20,}',
        }
        
        # Compile regex patterns for performance
        self.compiled_patterns = {name: re.compile(pattern) 
                                for name, pattern in self.patterns.items()}
        
        # Domains to exclude from scanning (to avoid false positives)
        self.excluded_domains = {
            'localhost', '127.0.0.1', 'example.com'
        }

    def is_excluded_domain(self, url: str) -> bool:
        """Check if domain should be excluded from scanning"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.split(':')[0]
            return domain in self.excluded_domains
        except Exception:
            return False

    def detect_keys_in_text(self, text: str, source_url: str, location: str) -> List[ApiKeyFinding]:
        """Detect API keys in given text using compiled patterns"""
        findings = []
        
        if not text or self.is_excluded_domain(source_url):
            return findings
            
        for key_type, pattern in self.compiled_patterns.items():
            matches = pattern.findall(text)
            
            for match in matches:
                # Handle both full matches and captured groups
                key_value = match if isinstance(match, str) else match[0] if match else ""
                
                # Skip empty matches and already seen keys
                if not key_value or key_value in self.seen_keys:
                    continue
                    
                # Additional validation to reduce false positives
                if self.validate_key_format(key_type, key_value):
                    finding = ApiKeyFinding(
                        key_type=key_type,
                        key_value=self.mask_key(key_value),
                        source_url=source_url,
                        location=location,
                        timestamp=datetime.now()
                    )
                    findings.append(finding)
                    self.seen_keys.add(key_value)
                    
        return findings

    def validate_key_format(self, key_type: str, key_value: str) -> bool:
        """Additional validation to reduce false positives"""
        # Basic length checks
        if len(key_value) < 8:
            return False
            
        # Specific validations for different key types
        if key_type == 'AWS_ACCESS_KEY':
            return len(key_value) == 20 and key_value.startswith(('AKIA', 'ASIA', 'AGPA'))
        elif key_type == 'GOOGLE_API_KEY':
            return len(key_value) == 39 and key_value.startswith('AIza')
        elif key_type == 'STRIPE_SECRET_KEY':
            return key_value.startswith('sk_test') or key_value.startswith('sk_live')
            
        return True

    def mask_key(self, key: str) -> str:
        """Mask sensitive key values for logging"""
        if len(key) <= 8:
            return "*" * len(key)
        return key[:4] + "*" * (len(key) - 8) + key[-4:]

    def log_findings(self, findings: List[ApiKeyFinding]):
        """Log detected API keys"""
        for finding in findings:
            logger.warning(f"API KEY DETECTED: Type={finding.key_type}, "
                          f"Location={finding.location}, URL={finding.source_url}")
            self.findings.append(finding)

class TrafficInterceptor:
    """MITM Proxy integration for HTTP traffic interception"""
    
    def __init__(self, detector: ApiKeyDetector):
        self.detector = detector
        
    def request(self, flow: http.HTTPFlow) -> None:
        """Intercept and analyze HTTP requests"""
        # Check request headers
        for header_name, header_value in flow.request.headers.items():
            findings = self.detector.detect_keys_in_text(
                header_value, flow.request.url, "HTTP Request Header"
            )
            self.detector.log_findings(findings)
            
        # Check request body
        if flow.request.content:
            try:
                content = flow.request.content.decode('utf-8', errors='ignore')
                findings = self.detector.detect_keys_in_text(
                    content, flow.request.url, "HTTP Request Body"
                )
                self.detector.log_findings(findings)
            except Exception as e:
                logger.debug(f"Error processing request body: {e}")

    def response(self, flow: http.HTTPFlow) -> None:
        """Intercept and analyze HTTP responses"""
        # Check response headers
        for header_name, header_value in flow.response.headers.items():
            findings = self.detector.detect_keys_in_text(
                header_value, flow.request.url, "HTTP Response Header"
            )
            self.detector.log_findings(findings)
            
        # Check response body
        if flow.response.content:
            try:
                content = flow.response.content.decode('utf-8', errors='ignore')
                findings = self.detector.detect_keys_in_text(
                    content, flow.request.url, "HTTP Response Body"
                )
                self.detector.log_findings(findings)
            except Exception as e:
                logger.debug(f"Error processing response body: {e}")

async def scan_page_dom(page, url: str, detector: ApiKeyDetector) -> None:
    """Scan DOM content for API keys"""
    try:
        # Get page HTML content
        html_content = await page.content()
        findings = detector.detect_keys_in_text(html_content, url, "DOM HTML")
        detector.log_findings(findings)
        
        # Check JavaScript variables in window object
        js_variables = await page.evaluate("""
            () => {
                const vars = [];
                for (let prop in window) {
                    if (typeof window[prop] === 'string' && window[prop].length > 10) {
                        vars.push(window[prop]);
                    }
                }
                return vars.join(' ');
            }
        """)
        
        findings = detector.detect_keys_in_text(js_variables, url, "DOM JavaScript")
        detector.log_findings(findings)
        
        # Check all script tags content
        scripts_content = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script');
                return Array.from(scripts).map(script => script.textContent || '').join(' ');
            }
        """)
        
        findings = detector.detect_keys_in_text(scripts_content, url, "DOM Script Tags")
        detector.log_findings(findings)
        
    except Exception as e:
        logger.error(f"Error scanning DOM for {url}: {e}")

async def crawl_and_scan(start_url: str, max_pages: int = 10) -> List[ApiKeyFinding]:
    """Main crawling and scanning function"""
    
    detector = ApiKeyDetector()
    findings = []
    
    async with async_playwright() as p:
        # Launch browser with proxy support for mitmproxy integration
        browser = await p.chromium.launch(
            headless=False,  # Set to True for headless operation
            args=['--proxy-server=http://localhost:8080']  # Point to mitmproxy
        )
        
        context = await browser.new_context(
            ignore_https_errors=True  # Required for HTTPS interception
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to start URL
            await page.goto(start_url)
            await scan_page_dom(page, start_url, detector)
            
            # Follow links to discover more pages (basic crawler)
            visited_urls = {start_url}
            urls_to_visit = [start_url]
            
            while urls_to_visit and len(visited_urls) < max_pages:
                current_url = urls_to_visit.pop(0)
                
                try:
                    await page.goto(current_url)
                    await page.wait_for_load_state('networkidle')
                    
                    # Scan current page
                    await scan_page_dom(page, current_url, detector)
                    
                    # Discover new URLs
                    if len(visited_urls) < max_pages:
                        new_links = await page.evaluate("""
                            () => Array.from(document.querySelectorAll('a[href]'))
                                      .map(a => a.href)
                                      .filter(href => href.startsWith('http'))
                        """)
                        
                        for link in new_links:
                            if link not in visited_urls and len(visited_urls) < max_pages:
                                visited_urls.add(link)
                                urls_to_visit.append(link)
                                
                except Exception as e:
                    logger.error(f"Error processing {current_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Browser error: {e}")
        finally:
            await browser.close()
    
    return detector.findings

def start_mitm_proxy(detector: ApiKeyDetector):
    """Start MITM proxy for traffic interception"""
    from mitmproxy.tools.main import mitmdump
    
    # This would typically be run in a separate process
    # For demonstration, we'll show how it would work
    
    def create_addon():
        class KeyDetectionAddon:
            def __init__(self, detector):
                self.detector = detector
                
            def request(self, flow):
                interceptor = TrafficInterceptor(self.detector)
                interceptor.request(flow)
                
            def response(self, flow):
                interceptor = TrafficInterceptor(self.detector)
                interceptor.response(flow)
                
        return KeyDetectionAddon(detector)
    
    return create_addon()

# Main execution function
async def main():
    """Main execution function"""
    print("API Key Detection Tool - Starting...")
    
    # Example usage - replace with your target URL
    target_url = "https://example.com"  # CHANGE THIS TO YOUR AUTHORIZED TARGET
    
    # Start MITM proxy in background (would require separate process in real implementation)
    detector = ApiKeyDetector()
    
    # Perform crawling and DOM scanning
    findings = await crawl_and_scan(target_url, max_pages=5)
    
    # Output results
    print(f"\nScan completed. Found {len(findings)} potential API key exposures:")
    for finding in findings:
        print(f"- {finding.key_type} found in {finding.location} at {finding.source_url}")
    
    # Save findings to JSON file
    findings_data = [
        {
            'type': f.key_type,
            'masked_value': f.key_value,
            'url': f.source_url,
            'location': f.location,
            'timestamp': f.timestamp.isoformat()
        }
        for f in findings
    ]
    
    with open('findings.json', 'w') as f:
        json.dump(findings_data, f, indent=2)
    
    print("\nFindings saved to 'findings.json'")
    print("Detailed logs available in 'api_key_detection.log'")

if __name__ == "__main__":
    # Run the tool
    asyncio.run(main())
