"""
Test skryptu do czyszczenia odpowiedzi uszkodzonego modelu.
"""

import re

def cleanup_response(text: str) -> str:
    """Czyści odpowiedź z uszkodzonych modeli, usuwając śmieciowe znaczniki.
    
    Args:
        text: Tekst do wyczyszczenia
        
    Returns:
        Wyczyszczony tekst
    """
    # Usuwanie bloków kodu markdown
    text = re.sub(r'```[^`]*```', ' ', text)
    
    # Usuwanie oddzielnych znaczników backtick
    text = re.sub(r'`{1,5}', ' ', text)
    
    # Usuwanie nawiasów z zawartością typu (*)
    text = re.sub(r'\(\*\)', ' ', text)
    
    # Usuwanie nawiasów z zawartością typu /LIRA/
    text = re.sub(r'\/[A-Za-z]+\/', ' ', text)
    
    # Usuwanie ciągów nawiasów i znaków specjalnych
    text = re.sub(r'[\)\}\(\{\[\]\/\\]{2,}', ' ', text)
    
    # Usuwanie linii zawierających tylko znaki specjalne
    text = re.sub(r'^[^\w\s]*$', '', text, flags=re.MULTILINE)
    
    # Usuwanie wielokrotnych spacji i znaków nowej linii
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    
    # Konwertuje text do pojedynczej linii jeśli zawiera głównie śmieci
    if len(re.findall(r'[^\w\s]', text)) > len(text) / 3:
        sentences = re.findall(r'[A-Z][^.!?]*[.!?]', text)
        if sentences:
            return ' '.join(sentences)
    
    return text.strip()

# Przykładowe testy

# Test 1: Odpowiedź z backtick i nawiasami
test1 = """```
```
</|>

````
````/````

(Looking forward)
```
Enter text here...
```
) ) ) ) )
```
)/)\n

Hey, what's your name again?

(  ` ```)\n
```

print("Test output")
"""

# Test 2: Usuwanie struktury LIRA
test2 = """
<LIRA/>

(Lira:) Ahah, yes, it's me again!

(Lira:)

So, how was your day? This is an actual content sentence.

(What did you do?)

(Was anything interesting happenin'?)...

(Please tell!)...

Go on!...)...)
"""

# Test 3: Usuwanie "```}" i podobnych
test3 = """
```
User Name
````````
<LIRA/>``````
```
=Lira
```
)

(Like That)
``}

````)}```}````}}}}}} Here's some actual text.

)}}``}}
```)}
```}\n``}`}``}}
"""

print("=== Test 1 ===")
print(cleanup_response(test1))
print("\n=== Test 2 ===")
print(cleanup_response(test2))
print("\n=== Test 3 ===")
print(cleanup_response(test3))