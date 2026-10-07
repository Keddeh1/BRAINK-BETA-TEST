"""Reversible A/B binary graph codec, version 1.

A=1, B=0. X is the slot index 1..9. The virtual root 1 is implicit,
permanently powered and unaddressable; the first addressable position is 2.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib

MAX_X=9
CODEC="KEDDEH_AB_BINARY_V1"
ROOT=1
FIRST_ADDRESS=2

@dataclass(frozen=True)
class Mapping:
    x:int
    address:int
    symbol:str
    state:int
    expression:str
    def as_dict(self):
        return {"x":self.x,"address":self.address,"symbol":self.symbol,
                "state":self.state,"expression":self.expression}

def _valid_bits(bits):
    if not isinstance(bits,str) or not 1<=len(bits)<=MAX_X or any(c not in "01" for c in bits):
        raise ValueError("ab_bits_must_be_1_to_9_binary_symbols")
    return bits

def encode(bits):
    """Compress one A/B state at each X into the minimum whole bytes, MSB first."""
    _valid_bits(bits)
    packed=bytearray((len(bits)+7)//8)
    for index,symbol in enumerate(bits):
        if symbol=="1": packed[index//8] |= 1 << (7-index%8)
    return bytes(packed)

def process(packed,length,consumer):
    """Decode each slot and process it in the same pass, without an expanded array."""
    if type(length) is not int or not 1<=length<=MAX_X: raise ValueError("invalid_ab_length")
    if not isinstance(packed,bytes) or len(packed)!=(length+7)//8:
        raise ValueError("invalid_ab_frame")
    if length%8 and packed[-1] & ((1 << (8-length%8))-1):
        raise ValueError("nonzero_ab_padding")
    for index in range(length):
        x=index+1
        state=(packed[index//8] >> (7-index%8)) & 1
        symbol="A" if state else "B"
        mapping=Mapping(x,x+1,symbol,state,f"{symbol}X({x})")
        consumer(mapping)

def decode(packed,length):
    mappings=[]
    process(packed,length,mappings.append)
    return "".join(str(item.state) for item in mappings)

def graph(packed,length):
    mappings=[]
    process(packed,length,mappings.append)
    return {"origin":{"from":ROOT,"to":FIRST_ADDRESS,
                      "powered":True,"addressable":False},
            "mappings":[item.as_dict() for item in mappings]}

def proof(packed,length):
    bits=decode(packed,length)
    if encode(bits)!=packed: raise ValueError("ab_reverse_roundtrip_failed")
    return {"codec":CODEC,"bits":bits,"sha256":hashlib.sha256(packed).hexdigest(),
            "packed_bytes":len(packed),"expanded_symbols":length,
            "origin":{"from":ROOT,"to":FIRST_ADDRESS,
                      "powered":True,"addressable":False}}
