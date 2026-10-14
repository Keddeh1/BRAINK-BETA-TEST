from __future__ import annotations
import hmac
from pathlib import Path

class MutationAuthorizer:
    """Optional bearer-token gate for mutation endpoints.

    No token file means local development mode. Production deployment should
    provide a root-readable token file through the deployment secret boundary.
    """
    def __init__(self, token_file: str | None = None, *, insecure_local_dev: bool = False):
        if token_file and insecure_local_dev: raise ValueError("conflicting_auth_modes")
        self.insecure_local_dev = insecure_local_dev
        self.token = None
        if token_file:
            value=Path(token_file).read_text(encoding="utf-8").strip()
            if not value: raise ValueError("empty_token_file")
            self.token=value

    @property
    def enabled(self): return self.token is not None

    def allowed(self, authorization: str | None) -> bool:
        if not self.enabled: return self.insecure_local_dev
        if not authorization or not authorization.startswith("Bearer "): return False
        return hmac.compare_digest(authorization[7:], self.token)
