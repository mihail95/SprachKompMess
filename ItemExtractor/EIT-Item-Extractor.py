from datetime import datetime
start = datetime.now()

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
        self.items = pd.DataFrame(columns=['Sentence', 'Syllables', 'LowestZipfWord', 'LowestZipfScore', 'NoPropNouns', 'NoNumbers', 'HasVerb', 'NoAbbrev'])
        # Max - Min Combined Zipf = 7.37 - 0.7 (7 - 1 if rounded)
        # Hard-coded for now - maybe change later 
        self.zipfBoundaries = {
            0: (6, 8), 
            1: (5, 7),
            2: (4, 6),
            3: (3, 5),
            4: (1.5, 3.5),
            5: (0, 2.25)
        }
    
    def load_lexicon(self, filename:str, isPickled:bool) -> None:
        """Loads the lexicon from an excel spreadsheet or a precompiled binary (depending on the isPickled flag)"""
        if (isPickled):
            with open(f"{filename}.pickle", 'rb') as file:
                self.lexicon = pickle.load(file)
        else:
            df = pd.read_excel(f"{filename}.xlsx")
            filteredDf = df[df['spell-check OK (1/0)'] == 1] 
            # self.lexicon = dict(zip(df.Word, zip(df.ZipfSUBTLEX, df.ZipfGoogle, (df.ZipfSUBTLEX + df.ZipfGoogle)/2)))
            # Constructs a dictionary like: { word: CombinedZipf }
            self.lexicon = dict(zip(filteredDf.Word, (filteredDf.ZipfSUBTLEX + filteredDf.ZipfGoogle)/2))
            with open(f"{filename}.pickle", 'wb') as file:
                pickle.dump(self.lexicon, file, protocol=pickle.HIGHEST_PROTOCOL)
            
    def load_sentences(self, filenames:list) -> None:
        """Loads all sentences from an array of sources and does some light formatting"""
        for sentenceFile in filenames:
            with open(sentenceFile, 'r', encoding='utf-8') as file:
                for sentence in file:
                    currentSentence = sentence.replace("<i>", "").replace("</ i>", "").strip()
                    currentSentence = re.sub(r"^- ", "", currentSentence)
                    currentSentence = re.sub(r"\.\.\.", " ", currentSentence)
                    currentSentence = re.sub(r"\. \. \.", " ", currentSentence)
                    currentSentence = re.sub(r"^[0-9]*\t", "", currentSentence)
                    currentSentence = re.sub(r"  ", " ", currentSentence)
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
            if (zipf == 999): zipf = self.lexicon.get(token.lemma_, 999)
            tokenZipfs[token.text] = zipf

        return min(tokenZipfs.items(), key=lambda x: x[1])
    
    def create_zipf_categories(self, min:int, max:int, chunks:int) -> dict:
        """Creates a dictionary of sentence lengths with their respective category"""
        # Split the range into #chunks# equal parts
        splitRange = np.array_split(range(min, max+1), chunks)

        return { length: outerIndex for outerIndex, innerList in enumerate(splitRange) for length in innerList}

    def check_constraints(self, doc:Any)->tuple[bool,bool,bool,bool]:
        """Checks for all extra constraints and return a bool for each:
            1. Don't allow proper nouns (token.pos_ = PROPN)
            2. Don't allow numbers (token.pos_ = NUM)
            3. Don't allow sentences without verbs (token.pos_ = VERB)
            4. Don't allow abbreviations ('.' in token.text AND token.pos_ =! PUNCT)
        """ 
        constraints = dict.fromkeys(["noPropNouns", "noNumbers", "noAbbrev"], True)
        constraints.update(dict.fromkeys(["hasVerb"], False))
        for token in doc:
            if (token.pos_ == 'PROPN'): constraints['noPropNouns'] = False
            if (token.pos_ == 'NUM'): constraints['noNumbers'] = False
            if (('.' in token.text) and (token.pos_ != 'PUNCT')): constraints['noAbbrev'] = False
            if (token.pos_ == 'VERB'): constraints['hasVerb'] = True


        return constraints['noPropNouns'], constraints['noNumbers'], constraints['hasVerb'], constraints['noAbbrev']



    def choose_items(self, minLen:int, maxLen:int, perLength:int) -> None:
        """The main method for item selection"""

        cycleCount = 0
        maxItemCount = (maxLen - minLen + 1) * perLength

        # While item rows are less than needed items
        while (len(self.items.index) < maxItemCount):
            cycleCount = cycleCount + 1
            # Get a random new sentence from the list
            randInt = self.generate_unique_random_int()
            sentence = self.sentences[randInt]
            doc, syllableCount = self.count_syllables(sentence)

            # Continue to next cycle if syllableCount is not in the boundaries or all items of current sentence length are already selected
            itemsOfCurrentLen = len(self.items.query(f"Syllables == {syllableCount}").index)
            if ((syllableCount < minLen) or (syllableCount > maxLen) or (itemsOfCurrentLen >= perLength)):
                continue
            
            lowestZipf = self.find_word_with_lowest_zipf(doc)
            zipfCategoriesDict = self.create_zipf_categories(minLen, maxLen, chunks = 6)
            zipfBoundary = self.zipfBoundaries[zipfCategoriesDict[syllableCount]]

            # Continue to next cycle if the lowest Zipf score does not fit in the boundary, corresponding to the sentence length
            if ((lowestZipf[1] == 999) or (lowestZipf[1] < zipfBoundary[0]) or (lowestZipf[1] > zipfBoundary[1])):
                continue
            
            # Constraints - all should be true, otherwise continue to next cycle
            noPropNouns, noNumbers, hasVerb, noAbbrev = self.check_constraints(doc)
            if (not (noPropNouns and noNumbers and hasVerb and noAbbrev)):
                continue

            # columns=['Sentence', 'Syllables', 'LowestZipfWord', 'LowestZipfScore', 'NoPropNouns', 'NoNumbers', 'HasVerb', 'NoAbbrev']
            toConcat = pd.DataFrame([[sentence, syllableCount, lowestZipf[0], lowestZipf[1], noPropNouns, noNumbers, hasVerb, noAbbrev]], columns=self.items.columns)
            self.items = pd.concat([toConcat, self.items], ignore_index=True)
            print(f"{datetime.now() - start}: Item of length {syllableCount} has been added. ({itemsOfCurrentLen + 1}/{perLength})")
        
        print(f"All items found after {cycleCount} cycles. ({maxItemCount} total items)")
        self.items.to_excel("output.xlsx", sheet_name= "Sentences")
            

if __name__ == "__main__":
    itemExtractor = EITItemExtractor()
    itemExtractor.load_lexicon('ZipfLexicon', isPickled=True)
    itemExtractor.load_sentences(['OpenSubtitles.tok', 'deu-com_web_2021_10K-sentences.txt'])
    itemExtractor.init_pipeline()
    itemExtractor.choose_items(minLen=7, maxLen=30, perLength=5)
    # Write sentences to file (sorted by length)

    print("Program ended in: ", datetime.now() - start)

    # TODO: Ask if searching the lexicon by lemma makes sense.
    # TODO: Ask if splitting all lenghts into 3 equally big groups makes sense. More, less groups? Nor equal?
    # TODO: How should the zipfs be divided between these groups?


