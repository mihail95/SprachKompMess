import re
import random
import pandas as pd
import pickle
import spacy
from spacy_syllables import SpacySyllables

class EITItemExtractor():
    def __init__(self) -> None:
        self.sentences = []
        self.lexicon = {}
        self.checkedIndeces = set()
        self.pipeline = None
        self.items = pd.DataFrame(columns=['Sentence', 'Syllables', 'LowestFreq', 'Constraint1'])
    
    def load_lexicon(self, filename:str, isPickled:bool) -> None:
        """Loads the lexicon from an excel spreadsheet or a precompiled binary (depending on the isPickled flag)"""
        if (isPickled):
            with open(f"{filename}.pickle", 'rb') as file:
                self.lexicon = pickle.load(file)
        else:
            df = pd.read_excel(f"{filename}.xlsx")
            # self.lexicon = dict(zip(df.Word, zip(df.ZipfSUBTLEX, df.ZipfGoogle, (df.ZipfSUBTLEX + df.ZipfGoogle)/2)))
            # Constructs a dictionary like: { word: CombinedZipf }
            self.lexicon = dict(zip(df.Word, (df.ZipfSUBTLEX + df.ZipfGoogle)/2))
            with open(f"{filename}.pickle", 'wb') as file:
                pickle.dump(self.lexicon, file, protocol=pickle.HIGHEST_PROTOCOL)
        
        print(self.lexicon['die'])
            
    def load_sentences(self, filenames:list) -> None:
        """Loads all sentences from an array of sources and does some light formatting"""
        for sentenceFile in filenames:
            with open(sentenceFile, 'r', encoding='utf-8') as file:
                for sentence in file:
                    currentSentence = sentence.replace("<i>", "").replace("</ i>", "").strip()
                    currentSentence = re.sub(r"^- ", "", currentSentence)
                    currentSentence = re.sub(r"^[0-9]*\t", "", currentSentence)
                    self.sentences.append(currentSentence)

    def init_pipeline(self) -> None:
        """Initializes the spacy pipeline""" 
        nlp = spacy.load("de_core_news_sm")
        nlp.add_pipe("syllables", after="tagger", config={"lang": "de_DE"})
        self.pipeline = nlp

    def GenerateUniqueRandomInt(self) -> int:
        """Generates a random integer, not included in the checkedIndeces set and adds it to it"""
        # Throw an error if we've checked all indeces
        if (len(self.sentences) == len(self.checkedIndeces)):
            raise Exception("All possible indeces in the sentences array have been checked without succesfully finding all needed items")
        randInt = random.randint(0, len(self.sentences))
        while randInt in self.checkedIndeces:
            randInt = random.randint(0, len(self.sentences))
        self.checkedIndeces.add(randInt)

        return randInt

    def CountSyllablesInSentence(self, sentence:str) -> tuple[spacy.__doc__, int]:
        """Counts up all syllables in the given sentece and returns the sum and the Spacy-Doc"""
        doc = self.pipeline(sentence)
        syllableSum = sum((token._.syllables_count) or 0 for token in doc)
        return doc, syllableSum

    def choose_items(self, minLen:int, maxLen:int, perLength:int) -> None:
        """The main method for item selection"""
        # Wortfrequenz: Zipf-Score des seltensten Wortes sinkt mit steigender Satzlänge (d.h. längere Sätze sollen auch seltenere Wörter enthalten)
        # Max - Min Combined Zipf = 7.37 - 0.7 (7 - 1 if rounded)
        # Constraints

        maxItemCount = (maxLen - minLen + 1) * perLength

        # While item rows are less than needed items
        while (len(self.items.index) < maxItemCount):
            # Get a random new sentence from the list
            randInt = self.GenerateUniqueRandomInt()
            sentence = self.sentences[randInt]
            doc, syllableCount = self.CountSyllablesInSentence(sentence)

            # Continue to next cycle if syllableCount is not in the boundaries or all items of current sentence length are already selected
            if ((syllableCount < minLen) or (syllableCount > maxLen) or (len(self.items.query(f"Syllables == {syllableCount}").index) >= perLength)):
                continue
            
            # columns=['Sentence', 'Syllables', 'LowestFreq', 'Constraint1']
            toConcat = pd.DataFrame([[sentence, syllableCount, '3', '4']], columns=self.items.columns)
            self.items = pd.concat([toConcat, self.items], ignore_index=True)
        
        self.items.to_excel("output.xlsx", sheet_name= "Sentences")
            

if __name__ == "__main__":
    itemExtractor = EITItemExtractor()
    itemExtractor.load_lexicon('ZipfLexicon', isPickled=True)
    itemExtractor.load_sentences(['OpenSubtitles.tok', 'deu-com_web_2021_10K-sentences.txt'])
    itemExtractor.init_pipeline()
    itemExtractor.choose_items(minLen=7, maxLen=30, perLength=5)
    # Write sentences to file (sorted by length)
