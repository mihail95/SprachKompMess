import re
import random
import pandas as pd
import numpy as np
import pickle
import spacy
from spacy_syllables import SpacySyllables
from typing import Any

class EITItemExtractor():
    def __init__(self) -> None:
        self.sentences = []
        self.lexicon = {}
        self.checkedIndeces = set()
        self.pipeline = None
        self.items = pd.DataFrame(columns=['Sentence', 'Syllables', 'LowestZipfWord', 'LowestZipfScore', 'Constraint1'])
        # Max - Min Combined Zipf = 7.37 - 0.7 (7 - 1 if rounded)
        # Hard-coded for now - maybe change later 
        self.zipfBoundaries = {
            0: (4, 1000), 
            1: (2.5, 4),
            2: (0, 2.5)
        }
    
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

    def generate_unique_random_int(self) -> int:
        """Generates a random integer, not included in the checkedIndeces set and adds it to it"""
        # Throw an error if we've checked all indeces
        if (len(self.sentences) == len(self.checkedIndeces)):
            raise Exception("All possible indeces in the sentences array have been checked without succesfully finding all needed items")
        randInt = random.randint(0, len(self.sentences))
        while randInt in self.checkedIndeces:
            randInt = random.randint(0, len(self.sentences))
        self.checkedIndeces.add(randInt)

        return randInt

    def count_syllables(self, sentence:str) -> tuple[Any, int]:
        """Counts up all syllables in the given sentece and returns the sum and the Spacy-Doc"""
        doc = self.pipeline(sentence)
        syllableSum = sum((token._.syllables_count) or 0 for token in doc)
        return doc, syllableSum

    def find_word_with_lowest_zipf(self, doc:Any) -> tuple[str, float]:
        """Returns a tuple of a word and its zipf score, for the lowest scoring word in the sentence (the least frequent one)"""
        tokenZipfs = {}
        for token in doc:
            # Check for text in the lexicon
            zipf = self.lexicon.get(token.text, 999)
            tokenZipfs[token.text] = zipf

        return min(tokenZipfs.items(), key=lambda x: x[1])
    
    def create_zipf_categories(self, min:int, max:int, chunks:int) -> dict:
        """Creates a dictionary of sentence lengths with their respective category"""
        # Split the range into #chunks# equal parts
        splitRange = np.array_split(range(min, max+1), chunks)

        return { length: outerIndex for outerIndex, innerList in enumerate(splitRange) for length in innerList}



    def choose_items(self, minLen:int, maxLen:int, perLength:int) -> None:
        """The main method for item selection"""
        # Wortfrequenz: Zipf-Score des seltensten Wortes sinkt mit steigender Satzlänge (d.h. längere Sätze sollen auch seltenere Wörter enthalten)
        # Constraints

        maxItemCount = (maxLen - minLen + 1) * perLength

        # While item rows are less than needed items
        while (len(self.items.index) < maxItemCount):
            # Get a random new sentence from the list
            randInt = self.generate_unique_random_int()
            sentence = self.sentences[randInt]
            doc, syllableCount = self.count_syllables(sentence)

            # Continue to next cycle if syllableCount is not in the boundaries or all items of current sentence length are already selected
            if ((syllableCount < minLen) or (syllableCount > maxLen) or (len(self.items.query(f"Syllables == {syllableCount}").index) >= perLength)):
                continue
            
            lowestZipf = self.find_word_with_lowest_zipf(doc)
            zipfCategoriesDict = self.create_zipf_categories(minLen, maxLen, chunks = 3)
            zipfBoundary = self.zipfBoundaries[zipfCategoriesDict[syllableCount]]

            # Continue to next cycle if the lowest Zipf score does not fit in the boundary, corresponding to the sentence length
            if ((lowestZipf[1] < zipfBoundary[0]) or (lowestZipf[1] > zipfBoundary[1])):
                continue

            # columns=['Sentence', 'Syllables', 'LowestZipfWord', 'LowestZipfScore', 'Constraint1']
            toConcat = pd.DataFrame([[sentence, syllableCount, lowestZipf[0], lowestZipf[1], '4']], columns=self.items.columns)
            self.items = pd.concat([toConcat, self.items], ignore_index=True)
        
        self.items.to_excel("output.xlsx", sheet_name= "Sentences")
            

if __name__ == "__main__":
    itemExtractor = EITItemExtractor()
    itemExtractor.load_lexicon('ZipfLexicon', isPickled=True)
    itemExtractor.load_sentences(['OpenSubtitles.tok', 'deu-com_web_2021_10K-sentences.txt'])
    itemExtractor.init_pipeline()
    itemExtractor.choose_items(minLen=7, maxLen=30, perLength=5)
    # Write sentences to file (sorted by length)
