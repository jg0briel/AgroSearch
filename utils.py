import unicodedata

STOPWORDS = ["os", "o", "a", "para", "de", "em", "e", "por", "na", "no", "da", "do"]

def normalize(text):
    text = text.lower()
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    return text

def stemmer(palavra):
    if palavra.endswith("entos"): return palavra[:-4]
    if palavra.endswith("amente"): return palavra[:-5]
    if palavra.endswith("ados"): return palavra[:-3]
    return palavra