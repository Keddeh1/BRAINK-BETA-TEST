from dataclasses import dataclass, asdict
from typing import Optional

@dataclass(frozen=True)
class ArtifactWrite:
    path:str
    content:bytes
    source:str
    predecessor:Optional[str]=None
    media_type:str="application/octet-stream"
    continuation_id:Optional[str]=None
    expected_version:Optional[int]=None

@dataclass(frozen=True)
class ArtifactRecord:
    digest:str
    path:str
    source:str
    predecessor:Optional[str]
    media_type:str
    size:int
    created_at:float
    def as_dict(self): return asdict(self)

@dataclass(frozen=True)
class Receipt:
    receipt_id:str
    kind:str
    status:str
    artifact_digest:Optional[str]
    path:Optional[str]
    previous_receipt_digest:Optional[str]
    receipt_digest:str
    at:float
    detail:dict
    def as_dict(self): return asdict(self)
