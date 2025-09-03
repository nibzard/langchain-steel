# Steel Authentication Patterns

Steel.dev provides robust authentication capabilities for accessing protected web content and authenticated applications. This guide covers common authentication patterns and implementation strategies.

## Overview

Steel supports various authentication methods:

- **Form-based login**: Username/password forms
- **OAuth 2.0 flows**: GitHub, Google, Microsoft, etc.
- **API key authentication**: Headers and query parameters
- **Session management**: Persistent sessions across requests
- **Multi-factor authentication**: SMS, email, authenticator apps
- **Certificate-based auth**: Client certificates

## Basic Authentication Patterns

### Form-Based Login

```python
from langchain_steel import SteelBrowserAgent

def login_with_credentials(site_url: str, username: str, password: str):
    """Handle standard username/password login."""
    
    agent = SteelBrowserAgent()
    
    login_task = f"""
    1. Navigate to {site_url}
    2. Find and fill username field with: {username}
    3. Find and fill password field with: {password}
    4. Click the login/submit button
    5. Wait for login completion (redirect or page change)
    6. Verify successful login by checking for user dashboard or profile
    7. Return session cookies and authentication status
    """
    
    result = agent.run(login_task)
    return result

# Example usage
login_result = login_with_credentials(
    "https://app.example.com/login",
    "user@example.com", 
    "secure_password"
)

# Extract session for reuse
session_id = login_result.get("session_id")
cookies = login_result.get("cookies")
```

### Session Persistence

```python
from langchain_steel import SteelConfig, SteelDocumentLoader, SteelBrowserAgent

class AuthenticatedSession:
    def __init__(self, login_url: str, username: str, password: str):
        self.login_url = login_url
        self.username = username
        self.password = password
        self.session_id = None
        self.cookies = None
        self.authenticated = False
    
    def login(self):
        """Establish authenticated session."""
        config = SteelConfig(
            api_key="your-key",
            session_timeout=1800,  # 30 minutes
            stealth_mode=True
        )
        
        agent = SteelBrowserAgent(config=config)
        
        login_task = f"""
        1. Go to {self.login_url}
        2. Fill login form with username: {self.username}
        3. Fill password field with: {self.password}
        4. Submit login form
        5. Wait for successful authentication
        6. Return session details and current page info
        """
        
        result = agent.run(login_task)
        
        if "success" in result.get("status", "").lower():
            self.session_id = result.get("session_id")
            self.cookies = result.get("cookies")
            self.authenticated = True
            return True
        
        return False
    
    def scrape_authenticated_page(self, url: str):
        """Scrape content from protected page."""
        if not self.authenticated:
            raise Exception("Must login first")
        
        # Use session for authenticated request
        loader = SteelDocumentLoader(
            urls=[url],
            format="markdown",
            session_id=self.session_id
        )
        
        documents = loader.load()
        return documents
    
    def logout(self):
        """Clean logout from session."""
        if self.session_id:
            agent = SteelBrowserAgent()
            logout_task = "Find and click logout button, confirm logout"
            agent.run(logout_task, session_id=self.session_id)
            
        self.session_id = None
        self.cookies = None
        self.authenticated = False

# Usage
session = AuthenticatedSession(
    "https://app.company.com/login",
    "user@company.com",
    "password123"
)

if session.login():
    # Access protected content
    dashboard_docs = session.scrape_authenticated_page("https://app.company.com/dashboard")
    reports_docs = session.scrape_authenticated_page("https://app.company.com/reports")
    
    # Clean logout
    session.logout()
```

## OAuth 2.0 Integration

### GitHub OAuth Flow

```python
from langchain_steel import SteelBrowserAgent
from urllib.parse import parse_qs, urlparse

class GitHubOAuthHandler:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
    
    def authorize(self, scopes: list = None):
        """Handle OAuth authorization flow."""
        if scopes is None:
            scopes = ["user:email", "repo"]
        
        scope_string = " ".join(scopes)
        auth_url = f"https://github.com/login/oauth/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={scope_string}"
        
        agent = SteelBrowserAgent()
        
        oauth_task = f"""
        1. Navigate to {auth_url}
        2. If not logged in, handle GitHub login process
        3. Review and click "Authorize" button for the application
        4. Wait for redirect to {self.redirect_uri}
        5. Extract the authorization code from the callback URL
        6. Return the authorization code and final redirect URL
        """
        
        result = agent.run(oauth_task)
        
        # Extract authorization code
        callback_url = result.get("final_url", "")
        parsed_url = urlparse(callback_url)
        query_params = parse_qs(parsed_url.query)
        
        if "code" in query_params:
            auth_code = query_params["code"][0]
            return self.exchange_code_for_token(auth_code)
        else:
            raise Exception("Authorization failed - no code received")
    
    def exchange_code_for_token(self, auth_code: str):
        """Exchange authorization code for access token."""
        import requests
        
        token_url = "https://github.com/login/oauth/access_token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": auth_code,
            "redirect_uri": self.redirect_uri
        }
        
        headers = {"Accept": "application/json"}
        
        response = requests.post(token_url, data=data, headers=headers)
        token_data = response.json()
        
        if "access_token" in token_data:
            self.access_token = token_data["access_token"]
            return self.access_token
        else:
            raise Exception(f"Token exchange failed: {token_data}")

# Usage
github_auth = GitHubOAuthHandler(
    client_id="your_github_client_id",
    client_secret="your_github_client_secret", 
    redirect_uri="https://yourapp.com/auth/callback"
)

access_token = github_auth.authorize(["user:email", "repo", "read:org"])
print(f"Obtained access token: {access_token[:10]}...")
```

### Google OAuth with 2FA

```python
def handle_google_oauth_with_2fa(client_id: str, redirect_uri: str):
    """Handle Google OAuth with 2FA support."""
    
    agent = SteelBrowserAgent()
    
    auth_url = f"https://accounts.google.com/oauth2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=email+profile"
    
    oauth_task = f"""
    1. Navigate to {auth_url}
    2. If login required:
       a. Enter Google email address
       b. Enter password on next screen
       c. If 2FA prompt appears:
          - Wait for user to enter 2FA code from their device
          - Or handle SMS/email verification if configured
    3. Review permissions and click "Allow/Accept"
    4. Wait for redirect to {redirect_uri}
    5. Extract authorization code from callback URL
    6. Return code and any error messages
    """
    
    result = agent.run(oauth_task)
    return result
```

## Multi-Factor Authentication

### SMS-Based 2FA

```python
from langchain_steel import SteelBrowserAgent
import time

def handle_sms_2fa_login(login_url: str, username: str, password: str, sms_handler=None):
    """Handle login with SMS-based 2FA."""
    
    agent = SteelBrowserAgent()
    
    # Step 1: Initial login
    login_task = f"""
    1. Navigate to {login_url}
    2. Fill username field with: {username}
    3. Fill password field with: {password}
    4. Click login button
    5. Check if 2FA prompt appears
    6. Return current page status and any 2FA requirements
    """
    
    login_result = agent.run(login_task)
    
    if "2fa" in login_result.get("status", "").lower() or "verification" in login_result.get("page_content", "").lower():
        print("2FA required - SMS code should be sent")
        
        # Wait for SMS (user needs to provide code)
        if sms_handler:
            sms_code = sms_handler.get_latest_code()
        else:
            sms_code = input("Enter SMS verification code: ")
        
        # Step 2: Submit 2FA code
        mfa_task = f"""
        1. Find the verification code input field
        2. Enter the code: {sms_code}
        3. Submit the verification form
        4. Wait for successful authentication
        5. Return final authentication status
        """
        
        mfa_result = agent.run(mfa_task, session_id=login_result.get("session_id"))
        return mfa_result
    
    return login_result

# Usage with custom SMS handler
class SMSCodeHandler:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
    
    def get_latest_code(self, timeout: int = 60):
        """Get the latest SMS code (implement based on your SMS service)."""
        # This would integrate with your SMS service API
        # For demo purposes, we'll simulate user input
        return input(f"Enter SMS code sent to {self.phone_number}: ")

sms_handler = SMSCodeHandler("+1234567890")
result = handle_sms_2fa_login(
    "https://secure-app.com/login",
    "user@example.com",
    "password123",
    sms_handler
)
```

### Authenticator App Integration

```python
def handle_totp_authentication(login_url: str, username: str, password: str):
    """Handle Time-based One-Time Password (TOTP) authentication."""
    
    agent = SteelBrowserAgent()
    
    # Initial login
    login_task = f"""
    1. Go to {login_url}
    2. Enter credentials: {username} / {password}
    3. Click login
    4. If TOTP/authenticator prompt appears:
       a. Take screenshot of QR code if present (first-time setup)
       b. Wait for 6-digit code input field
       c. Pause for manual code entry
    5. Return page status and authentication requirements
    """
    
    result = agent.run(login_task)
    
    if "authenticator" in result.get("page_content", "").lower() or "totp" in result.get("status", "").lower():
        # User needs to check their authenticator app
        totp_code = input("Enter 6-digit code from authenticator app: ")
        
        totp_task = f"""
        1. Enter the TOTP code: {totp_code}
        2. Submit authentication form
        3. Handle any "trust this device" prompts
        4. Wait for successful authentication
        5. Return final login status
        """
        
        final_result = agent.run(totp_task, session_id=result.get("session_id"))
        return final_result
    
    return result
```

## API Key Authentication

### Header-Based API Authentication

```python
from langchain_steel import SteelDocumentLoader, SteelScrapeTool

def scrape_with_api_key(url: str, api_key: str, auth_header: str = "Authorization"):
    """Scrape API-protected content using API key authentication."""
    
    # Method 1: Using document loader with custom headers
    loader = SteelDocumentLoader(
        urls=[url],
        format="markdown",
        custom_headers={
            auth_header: f"Bearer {api_key}",
            "User-Agent": "SteelBot/1.0",
            "Accept": "application/json"
        }
    )
    
    try:
        documents = loader.load()
        return documents
    except Exception as e:
        print(f"API authentication failed: {e}")
        return None

# Method 2: Using scraping tool
def scrape_api_endpoint_with_key(endpoint: str, api_key: str):
    """Scrape API endpoint with key authentication."""
    
    tool = SteelScrapeTool()
    
    result = tool.run({
        "url": endpoint,
        "format": "markdown",
        "custom_headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    })
    
    return result

# Usage examples
api_docs = scrape_with_api_key(
    "https://api.company.com/docs",
    "sk-1234567890abcdef",
    "X-API-Key"
)

api_data = scrape_api_endpoint_with_key(
    "https://api.service.com/v1/user/profile",
    "your-api-key-here"
)
```

## Advanced Authentication Patterns

### Corporate SSO (SAML)

```python
def handle_saml_sso_login(saml_login_url: str, username: str, password: str):
    """Handle SAML-based Single Sign-On authentication."""
    
    agent = SteelBrowserAgent()
    
    saml_task = f"""
    1. Navigate to {saml_login_url}
    2. If redirected to identity provider:
       a. Enter corporate username: {username}
       b. Enter corporate password: {password}
       c. Handle any MFA prompts that appear
    3. Wait for SAML response and redirect back to application
    4. Verify successful authentication to target application
    5. Return authentication status and session info
    """
    
    result = agent.run(saml_task)
    return result

# Usage for corporate applications
saml_result = handle_saml_sso_login(
    "https://app.company.com/sso/login",
    "john.doe@company.com",
    "corporate_password"
)
```

### Certificate-Based Authentication

```python
from langchain_steel import SteelConfig, SteelDocumentLoader

def scrape_with_client_certificate(url: str, cert_path: str, key_path: str):
    """Access content requiring client certificate authentication."""
    
    config = SteelConfig(
        api_key="your-key",
        session_options={
            "client_certificate": cert_path,
            "client_key": key_path,
            "verify_ssl": True
        }
    )
    
    loader = SteelDocumentLoader(
        urls=[url],
        config=config,
        format="markdown"
    )
    
    try:
        documents = loader.load()
        return documents
    except Exception as e:
        print(f"Certificate authentication failed: {e}")
        return None

# Usage
secure_docs = scrape_with_client_certificate(
    "https://secure.company.com/internal-docs",
    "/path/to/client-cert.pem",
    "/path/to/client-key.pem"
)
```

## Session Management Best Practices

### Session Pooling

```python
from typing import Dict, Optional
import time

class AuthenticationManager:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self.session_timeout = 1800  # 30 minutes
    
    def get_or_create_session(self, site_key: str, credentials: dict) -> Optional[str]:
        """Get existing session or create new one."""
        
        # Check if we have a valid session
        if site_key in self.sessions:
            session_data = self.sessions[site_key]
            if time.time() - session_data["created_at"] < self.session_timeout:
                return session_data["session_id"]
            else:
                # Session expired, remove it
                del self.sessions[site_key]
        
        # Create new session
        session_id = self._authenticate(credentials)
        if session_id:
            self.sessions[site_key] = {
                "session_id": session_id,
                "created_at": time.time(),
                "credentials": credentials
            }
        
        return session_id
    
    def _authenticate(self, credentials: dict) -> Optional[str]:
        """Perform authentication and return session ID."""
        agent = SteelBrowserAgent()
        
        auth_task = f"""
        1. Navigate to {credentials['login_url']}
        2. Fill login form with username: {credentials['username']}
        3. Fill password: {credentials['password']}
        4. Submit login form
        5. Handle any 2FA if required
        6. Return session ID on successful authentication
        """
        
        result = agent.run(auth_task)
        return result.get("session_id")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = time.time()
        expired_keys = [
            key for key, session in self.sessions.items()
            if current_time - session["created_at"] > self.session_timeout
        ]
        
        for key in expired_keys:
            del self.sessions[key]
        
        print(f"Cleaned up {len(expired_keys)} expired sessions")

# Usage
auth_manager = AuthenticationManager()

# Use pooled sessions for multiple requests
credentials = {
    "login_url": "https://app.example.com/login",
    "username": "user@example.com", 
    "password": "password123"
}

session_id = auth_manager.get_or_create_session("example_app", credentials)

# Use session for multiple operations
loader = SteelDocumentLoader(
    urls=["https://app.example.com/data1", "https://app.example.com/data2"],
    session_id=session_id
)
```

### Automatic Session Renewal

```python
class AutoRenewingSession:
    def __init__(self, login_credentials: dict, renewal_threshold: int = 300):
        self.credentials = login_credentials
        self.renewal_threshold = renewal_threshold  # 5 minutes before expiry
        self.session_id = None
        self.session_created = 0
        self.session_duration = 1800  # 30 minutes
    
    def ensure_valid_session(self) -> str:
        """Ensure we have a valid session, renewing if necessary."""
        current_time = time.time()
        
        if (self.session_id is None or 
            current_time - self.session_created > self.session_duration - self.renewal_threshold):
            
            print("Renewing authentication session...")
            self.session_id = self._create_new_session()
            self.session_created = current_time
        
        return self.session_id
    
    def _create_new_session(self) -> str:
        """Create a new authenticated session."""
        agent = SteelBrowserAgent()
        
        auth_task = f"""
        1. Navigate to {self.credentials['login_url']}
        2. Perform login with stored credentials
        3. Handle any authentication challenges
        4. Return new session ID
        """
        
        result = agent.run(auth_task)
        return result.get("session_id")
    
    def scrape_with_auth(self, urls: list) -> list:
        """Scrape URLs with automatic session management."""
        session_id = self.ensure_valid_session()
        
        loader = SteelDocumentLoader(
            urls=urls,
            session_id=session_id,
            format="markdown"
        )
        
        return loader.load()

# Usage
auto_session = AutoRenewingSession({
    "login_url": "https://portal.company.com/login",
    "username": "employee@company.com",
    "password": "secure_password"
})

# Sessions automatically renewed as needed
docs1 = auto_session.scrape_with_auth(["https://portal.company.com/reports"])
time.sleep(600)  # 10 minutes later
docs2 = auto_session.scrape_with_auth(["https://portal.company.com/analytics"])  # Session renewed automatically
```

## Troubleshooting Authentication Issues

### Common Authentication Problems

```python
from langchain_steel.utils.errors import SteelError

def diagnose_auth_failure(login_url: str, username: str, password: str):
    """Diagnose authentication failures with detailed logging."""
    
    agent = SteelBrowserAgent()
    
    diagnostic_task = f"""
    1. Navigate to {login_url}
    2. Take screenshot of login page
    3. Fill username field and verify it appears correctly
    4. Fill password field (verify field accepts input)
    5. Click login button
    6. Wait 5 seconds for response
    7. Take screenshot of result page
    8. Check for common error indicators:
       - "Invalid credentials" messages
       - CAPTCHA requirements
       - Rate limiting warnings
       - Redirect loops
    9. Return detailed diagnostic information
    """
    
    try:
        result = agent.run(diagnostic_task)
        
        # Analyze common failure patterns
        page_content = result.get("page_content", "").lower()
        
        if "captcha" in page_content:
            return {"error": "CAPTCHA_REQUIRED", "solution": "Enable CAPTCHA solving in Steel config"}
        elif "invalid" in page_content or "incorrect" in page_content:
            return {"error": "INVALID_CREDENTIALS", "solution": "Verify username/password are correct"}
        elif "blocked" in page_content or "suspended" in page_content:
            return {"error": "ACCOUNT_BLOCKED", "solution": "Account may be locked or suspended"}
        elif "rate" in page_content or "limit" in page_content:
            return {"error": "RATE_LIMITED", "solution": "Wait before retrying or use different IP"}
        else:
            return {"error": "UNKNOWN", "details": result, "solution": "Check screenshots and page content"}
    
    except SteelError as e:
        return {"error": "STEEL_API_ERROR", "details": str(e), "solution": "Check Steel API status and configuration"}

# Usage
diagnosis = diagnose_auth_failure(
    "https://problematic-site.com/login",
    "test_user",
    "test_password"
)

print(f"Authentication issue: {diagnosis['error']}")
print(f"Suggested solution: {diagnosis['solution']}")
```

## Security Considerations

### Credential Management

```python
import os
from cryptography.fernet import Fernet

class SecureCredentialStore:
    def __init__(self):
        # Use environment variable for encryption key
        key = os.environ.get("STEEL_CRED_KEY", Fernet.generate_key())
        self.cipher = Fernet(key)
    
    def store_credentials(self, site_id: str, username: str, password: str):
        """Securely store credentials."""
        credentials = f"{username}:{password}"
        encrypted_creds = self.cipher.encrypt(credentials.encode())
        
        # Store encrypted credentials (use secure storage in production)
        with open(f".steel_creds_{site_id}", "wb") as f:
            f.write(encrypted_creds)
    
    def retrieve_credentials(self, site_id: str) -> tuple:
        """Retrieve and decrypt credentials."""
        try:
            with open(f".steel_creds_{site_id}", "rb") as f:
                encrypted_creds = f.read()
            
            decrypted = self.cipher.decrypt(encrypted_creds).decode()
            username, password = decrypted.split(":", 1)
            return username, password
        
        except Exception as e:
            raise Exception(f"Failed to retrieve credentials for {site_id}: {e}")

# Usage with secure credential management
cred_store = SecureCredentialStore()
cred_store.store_credentials("company_portal", "john.doe@company.com", "secure_password")

username, password = cred_store.retrieve_credentials("company_portal")
# Use retrieved credentials for authentication
```

### Best Practices Summary

1. **Never hardcode credentials** in source code
2. **Use environment variables** or secure credential stores
3. **Implement session timeouts** and automatic renewal
4. **Handle MFA scenarios** gracefully with user prompts
5. **Log authentication attempts** for debugging (but not credentials)
6. **Use HTTPS only** for authentication flows
7. **Implement retry logic** with exponential backoff
8. **Clean up sessions** when done to prevent resource leaks

Steel's authentication capabilities provide enterprise-grade security features while maintaining ease of use for developers building AI applications that need to access protected content.