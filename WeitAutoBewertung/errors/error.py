from typing import Optional, Protocol
from spacy.tokens import Doc

class Error(Protocol):
    """This is the base Error Class - all other errors should be defined as its children
    
    Each error must have a severity(int) and name(str) attributes,
    as well as a constructor (where these values are set) and an evaluate() Method, which returns an int (the error count)
    """

    severity: int
    name: str
    def __init__(self) -> None: ...
    def evaluate(self, original:str, answer:str, orig_spacy: Doc, ans_spacy: Doc) -> int: ...