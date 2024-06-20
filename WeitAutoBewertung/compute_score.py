import spacy
import re
import string

# Import the custom errors
from errors.minimal_repetition import MinimalRepetitionError

def format_item(input_string:str) -> str:
    # Remove Punctuation
    punctuation_re = re.compile('[%s]' % re.escape(string.punctuation))
    output_string = punctuation_re.sub('', input_string)

    return output_string

def compute_score(original:str, answer:str) -> int:

    # TODO: Vorverarbeitung (siehe etherpad: https://moodle.ruhr-uni-bochum.de/mod/etherpadlite/view.php?id=2935463)
    original = format_item(original)
    answer = format_item(answer)

    # Check if 'normalized' answer and original are the same => return a full score (4)
    if answer == original: return 4
    
    nlp_pipeline = spacy.load("de_core_news_sm")
    # TODO: Which pipeline elements do we need (exclude unused for performance): default active - tok2vec, tagger, morphologizer, parser, lemmatizer, attribute_ruler, ner

    orig_doc = nlp_pipeline(original)
    answer_doc = nlp_pipeline(answer)
    
    # Initialize a list of errors
    error_list = [MinimalRepetitionError()]

    # Initialize a dictionary with the error severity as keys and a dictionary of error names and counts as the value
    error_counts = { 0: {}, 1: {}, 2:{}, 3:{} }   

    score = 999

    # Go through the list of errors and use their respective evaluate() methods
    for error in error_list:
        error_counts[error.severity][error.name] = error.evaluate(original, answer, orig_doc, answer_doc)
        print("Error Counts: ", error_counts)

        # Break the loop and return a 0 score, if one or more severity 0 errors are found
        if sum(error_counts[0].values()) > 0: return 0


    # Count up the errors and compute a final score

    return score


if __name__ == "__main__":
    original = "Die Häuser sind nicht sehr schön und viel zu teuer."
    
    # die haußer sind die = 0 Punkte
    # Die Häuser nicht sind sehr schön = 1 Punkt
    # Das Hause sind nicht sehr schön und zu teuer = 2 Punkte
    # Die Häuser sind nicht sehr schön, und viel zu teurer = 3 Punkte
    # Die Häuser sind nicht sehr schön und viel zu teuer. = 4 Punkte
    answers = [
        "die haußer sind die", 
        "Die Häuser nicht sind sehr schön", 
        "Das Hause sind nicht sehr schön und zu teuer", 
        "Die Häuser sind nicht sehr schön, und viel zu teurer", 
        "Die Häuser sind nicht sehr schön, und viel zu teuer"
    ]
    
    for answer in answers:
        print("Item: ", original)
        print("Answer: ", answer)
        score = compute_score(original, answer)
        print(f"Score: {score}\n")
