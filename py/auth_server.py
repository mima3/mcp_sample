import httpx
import jwt
from jwt import PyJWKClient
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from dataclasses import dataclass
from pydantic import AnyHttpUrl
from typing import Any
import time
from pydantic import BaseModel

logger = get_logger("FastMCP.Server")

class CalculatorResult(BaseModel):
    input: list[float]
    total: float

@dataclass
class KeycloakOIDCMetadata:
    issuer: str
    jwks_uri: str


class KeycloakJWTVerifier(TokenVerifier):
    """
    Verify Keycloak-issued JWT access tokens using OIDC discovery + JWKS.
    - Fetches {issuer}/.well-known/openid-configuration (OIDC discovery)
    - Uses jwks_uri to validate token signature
    - Validates issuer and required scopes
    """

    def __init__(self, issuer_url: str, required_scopes: list[str] | None = None) -> None:
        self.issuer_url = issuer_url.rstrip("/")
        self.required_scopes = required_scopes or []
        self._meta: KeycloakOIDCMetadata | None = None
        self._jwk_client: PyJWKClient | None = None

    async def _load_metadata(self) -> KeycloakOIDCMetadata:
        if self._meta is not None:
            return self._meta

        # Keycloak OIDC discovery endpoint pattern is shown in MCP auth tutorial
        # e.g. http://localhost:8080/realms/master/.well-known/openid-configuration
        discovery = f"{self.issuer_url}/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(discovery)
            logger.info(discovery)
            logger.info(r)
            r.raise_for_status()
            data = r.json()

        self._meta = KeycloakOIDCMetadata(
            issuer=data["issuer"],
            jwks_uri=data["jwks_uri"],
        )
        logger.info(self._meta)
        self._jwk_client = PyJWKClient(self._meta.jwks_uri)
        return self._meta

    async def verify_token(self, token: str) -> AccessToken | None:
        meta = await self._load_metadata()
        assert self._jwk_client is not None

        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token).key
            logger.info(f'verify...{signing_key}')
            unverified = jwt.decode(token, options={"verify_signature": False})
            logger.info(unverified.get("aud"))
            logger.info(unverified.get("azp"))
            logger.info(unverified.get("scope"))

            # Validate signature + issuer; audience validation is optional and depends on your token config.
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256", "ES256"],  # Keycloak commonly uses RS256; ES256 also possible.
                issuer=meta.issuer,
                options={
                    "require": ["exp", "iss"],
                },
                audience="account",
            )
        except Exception as e:
            logger.info(f'verify...error {e}')
            return None
        logger.info('verify...2')
        # Keycloak "scope" claim is typically a space-separated string for OAuth2 access tokens.
        scope_str = claims.get("scope", "") or ""
        scopes = [s for s in scope_str.split(" ") if s]

        if any(req not in scopes for req in self.required_scopes):
            logger.info(scopes)
            logger.info(self.required_scopes)
            return None

        logger.info('verify...3')
        exp = claims.get("exp")
        if isinstance(exp, int) and exp < int(time.time()):
            return None

        logger.info('verify...4')
        client_id = claims.get("azp") or claims.get("client_id") or "unknown-client"

        return AccessToken(
            token=token,
            client_id=str(client_id),
            scopes=scopes,
            expires_at=int(exp) if isinstance(exp, int) else None,
            # resource=...  # (RFC8707 resource indicator) 使うならここに入れる
        )

KEYCLOAK_ISSUER = "http://localhost:8080/realms/master"
RESOURCE_SERVER_URL = "http://localhost:8000"
REQUIRED_SCOPES = ["mcp:tools"]
verifier = KeycloakJWTVerifier(KEYCLOAK_ISSUER, required_scopes=REQUIRED_SCOPES)


mcp = FastMCP(
    "CalculatorAuthMCPServer",
    host="localhost",
    port=8000,
    token_verifier=verifier,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(KEYCLOAK_ISSUER),
        resource_server_url=AnyHttpUrl(RESOURCE_SERVER_URL),
        required_scopes=REQUIRED_SCOPES,
    ),
)

@mcp.tool()
async def calculator_sum(numbers: list[float], ctx: Context) -> CalculatorResult:
    """与えられた数値のリストの合計を計算するツール。

    Args:
        numbers: 合計を計算する数値のリスト。
    """
    logger.info(f"calculator_sum called with numbers: {numbers} ")
    total = sum(numbers)
    logger.info(f"calculator_sum result {total} ")
    
    return CalculatorResult(
        input = numbers,
        total = total
    )

def main():
    logger.info('start main...')
    # FastMCP docs: transport="http" + host/port
    # Server endpoint will be: http://127.0.0.1:8000/mcp
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
