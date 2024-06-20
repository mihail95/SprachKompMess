from typing import Optional
from spacy.tokens import Doc
from .error import Error

class ExampleError(Error):
    """This can be used as a prototype for all new errors. 
    
    Just copy and rename the file, change the class name (Line 5), and set the severity and name attributes in the constructor\\
    Afterwards you can define a custom evaluate function (which uses either the item/answer strings or the spacy docs), which returns the error count
    """

    def __init__(self) -> None:
        self.severity = 0
        self.name = "Error_Name_Goes_Here"

    def evaluate(self, original:str, answer:str, orig_spacy: Doc, ans_spacy: Doc) -> int:

        # Do something do count up all the errors in the sentence string or spacy document (or both)
        # and then return the accumulated count
        count = 0 
        return count