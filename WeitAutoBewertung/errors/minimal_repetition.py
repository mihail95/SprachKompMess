from typing import Optional
from spacy.tokens import Doc
from .error import Error

class MinimalRepetitionError(Error):
    """Checks for 'Nothing (no entry)' and 'Minimal repetition, then item abandoned', results directly in a 0 point score"""
    def __init__(self) -> None:
        self.severity = 0
        self.name = "Minimal_Repetition_Error"

    def evaluate(self, original:str, answer:str, orig_spacy: Doc, ans_spacy: Doc) -> int:
        # Check if the answer has less than half the words of the original => directry count as error if so
        if len(answer.split()) < (len(original.split()) / 2): return 1

        # TODO: If we have more than the needed minumum, check for spelling etc.

        # If none of the above => no error
        return 0


