import time
import re
import pandas as pd
import pickle
import spacy
from spacy_syllables import SpacySyllables

class EITItemExtractor():
    def __init__(self) -> None:
        self.sentences = []
        self.lexicon = {}
        self.checkedIndeces = []
        self.pipeline = None
        self.items = {}
    
    def LoadLexicon(self, filename:str, isPickled:bool) -> None:
        """Loads the lexicon from an excel spreadsheet or a precompiled binary (depending on the isPickled flag)"""
        if (isPickled):
            with open(f"{filename}.pickle", 'rb') as file:
                self.lexicon = pickle.load(file)
        else:
            df = pd.read_excel(f"{filename}.xlsx")
            self.lexicon = dict(zip(df.Word, zip(df.ZipfSUBTLEX, df.ZipfGoogle)))  
            with open(f"{filename}.pickle", 'wb') as file:
                pickle.dump(self.lexicon, file, protocol=pickle.HIGHEST_PROTOCOL)
        
        # TODO: Set global min and max Zipf scores = (val[0]+val[1])/2
            
    def LoadSentences(self, filenames:list) -> None:
        """Loads all sentences from an array of sources and does some light formatting"""
        for sentenceFile in filenames:
            with open(sentenceFile, 'r', encoding='utf-8') as file:
                for sentence in file:
                    currentSentence = sentence.replace("<i>", "").replace("</ i>", "").strip()
                    currentSentence = re.sub(r"^- ", "", currentSentence)
                    currentSentence = re.sub(r"^[0-9]*\t", "", currentSentence)
                    self.sentences.append(currentSentence)

    def InitializePipeline(self) -> None:
        """Initializes the spacy pipeline""" 
        nlp = spacy.load("de_core_news_sm")
        nlp.add_pipe("syllables", after="tagger", config={"lang": "de_DE"})
        self.pipeline = nlp

    def ChooseItems(self, minLen:int, maxLen:int) -> None:
        """The main method for item selection"""
        # Länge: 7 - 30 Silben, 5 Sätze pro Länge
        # Wortfrequenz: Zipf-Score des seltensten Wortes sinkt mit steigender Satzlänge (d.h. längere Sätze sollen auch seltenere Wörter enthalten)
        # Max - Min Combined Zipf = 7.37 - 0.7 (7 - 1 if rounded)
        # Constraints
        ...

if __name__ == "__main__":
    itemExtractor = EITItemExtractor()
    itemExtractor.LoadLexicon('ZipfLexicon', isPickled=True)
    itemExtractor.LoadSentences(['OpenSubtitles.tok', 'deu-com_web_2021_10K-sentences.txt'])
    itemExtractor.InitializePipeline()

    itemExtractor.ChooseItems(minLen=7, maxLen=30)
    # Write sentences to file (sorted by length)
