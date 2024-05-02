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
        if (isPickled):
            with open(f"{filename}.pickle", 'rb') as file:
                self.lexicon = pickle.load(file)
        else:
            df = pd.read_excel(f"{filename}.xlsx")
            self.lexicon = dict(zip(df.Word, zip(df.ZipfSUBTLEX, df.ZipfGoogle)))  
            with open(f"{filename}.pickle", 'wb') as file:
                pickle.dump(self.lexicon, file, protocol=pickle.HIGHEST_PROTOCOL)
            
    def LoadSentences(self, filenames:list) -> None:
        for sentenceFile in filenames:
            with open(sentenceFile, 'r', encoding='utf-8') as file:
                for sentence in file:
                    currentSentence = sentence.replace("<i>", "").replace("</ i>", "").strip()
                    currentSentence = re.sub(r"^- ", "", currentSentence)
                    currentSentence = re.sub(r"^[0-9]*\t", "", currentSentence)
                    self.sentences.append(currentSentence)


    def InitializePipeline(self) -> None:
        ...


if __name__ == "__main__":

    # General Setup
    itemExtractor = EITItemExtractor()
    ## Load Lexicon File
    itemExtractor.LoadLexicon('ZipfLexicon', isPickled=True)
    ## Load Sentences Files
    itemExtractor.LoadSentences(['OpenSubtitles.tok', 'deu-com_web_2021_10K-sentences.txt'])
    ## Setup NLP-Pipeline
    itemExtractor.InitializePipeline()

    # Choose sentences