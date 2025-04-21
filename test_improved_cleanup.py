"""
Test ulepszonego skryptu do czyszczenia odpowiedzi uszkodzonego modelu.
"""

import re

def cleanup_response(text: str) -> str:
    """Czyści odpowiedź z uszkodzonych modeli, usuwając śmieciowe znaczniki.
    
    Args:
        text: Tekst do wyczyszczenia
        
    Returns:
        Wyczyszczony tekst
    """
    # Najpierw ekstrakcja potencjalnych dobrych fragmentów zdań i odpowiedzi
    good_sentences = re.findall(r'[A-Z][^.!?\n]{10,}[.!?]', text)
    
    # Jeśli znaleziono dobre zdania, zwróć je jako odpowiedź
    if good_sentences and len(' '.join(good_sentences)) > 50:
        return ' '.join(good_sentences)
    
    # Usuwanie bloków kodu markdown
    text = re.sub(r'```[^`]*```', ' ', text)
    
    # Usuwanie linii zawierających tylko znaki specjalne
    text = re.sub(r'^[^\w\s]*$', '', text, flags=re.MULTILINE)
    
    # Usuwanie znaczników HTML-podobnych i nawiasów ze ścieżkami
    text = re.sub(r'</?[A-Za-z/]+[^>]*>', ' ', text)  # Usuwa tagi HTML-podobne
    text = re.sub(r'/[A-Za-z/_.]+/', ' ', text)  # Usuwa ścieżki typu /usr/local/
    
    # Usuwanie bloków nawiasów z tekstem specjalnym
    text = re.sub(r'\([A-Za-z]+:\)', ' ', text)  # Usuwa (Lira:) itp.
    text = re.sub(r'\([\s\*]+\)', ' ', text)  # Usuwa (***) itp.
    
    # Usuwanie linii markdown z backtick
    text = re.sub(r'`[^`\n]*`', ' ', text)
    text = re.sub(r'`{1,5}', ' ', text)
    
    # Usuwanie ciągów nawiasów i śmieciowych znaczników
    text = re.sub(r'[\)\}\(\{\[\]\/\\]{2,}', ' ', text)
    text = re.sub(r'[\)\}\(\{\[\]\/\\]+$', '', text, flags=re.MULTILINE)  # Usuwa końcowe znaczniki
    
    # Usuwa specyficzne znaczniki uszkodzonego modelu
    text = re.sub(r'\|+(\s*\|+)*', ' ', text)  # Usuwa | | | itp.
    text = re.sub(r'#+\s*#+', ' ', text)  # Usuwa ## ## itp.
    
    # Usuwanie wielokrotnych spacji, nowych linii i innych białych znaków
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    
    # Próba wyodrębnienia tylko sensownego tekstu
    # Szukanie linii z małą ilością znaków specjalnych i przynajmniej 20 znaków
    clean_lines = []
    for line in text.split('\n'):
        # Oblicz stosunek znaków specjalnych do długości linii
        special_char_count = len(re.findall(r'[^\w\s]', line))
        if len(line) > 20 and special_char_count / len(line) < 0.3:
            clean_lines.append(line)
    
    # Jeśli mamy czyste linie, użyj ich
    if clean_lines:
        return '\n'.join(clean_lines).strip()
    
    # Jeśli tekst jest głównie śmieciowymi znakami, pobierz tylko poprawne fragmenty zdań
    if len(re.findall(r'[^\w\s]', text)) > len(text) / 4:
        sentence_fragments = re.findall(r'[A-Z][a-z]{2,}[^.!?\n]{5,}[.!?]', text)
        if sentence_fragments:
            return ' '.join(sentence_fragments)
    
    return text.strip()

# Przykładowe testy

# Prawdziwa odpowiedź z logów
test_from_logs = """Lira\n</|>\n\n````\n````/````\n\n(Looking forward)\n```\nEnter text here...\n```\n) ) ) ) )\n```\n)/)\n\n( ( ( ( ) ) )\n\n(Courtesy of CACOM )\n```\n\n(  ` ```)\n\n(Fresh Start :) :)\n\n````\n\nLet me start then...\n\n```\n)\n```\n\n```\n\nYour input: `/`, ```\n\nPlease enter some text.\n```\n\n\n```\n/) (/)\n\n```\n/)\n```\n\n(``) (``)\n```)\n\n\n```\n(/) (/)\n```````\n)`````}`}\n```\nUser Name\n````````\n<LIRA/>``````\n```\n=Lira\n```\n)\n\n(Like That)\n``}\n\n````)\n```}\n````}\n````} } }\n```\n)} \n```\n}\n``}`\n``}}\n``}}````}/````}) /\n``}`})\n``}\n} } }\n\n````}}} }} }}\n```````}{``}\n{````{}\n````\n}``\n``}{}}``}`}}``}}\n`````}``} }\n````}}}`}`}\n```}`}`)\n````)}}````')}}\n````))````}')\n````)}\n````)} }} {````{})\n````\")}\n````\"}}\n````\"\")\n``\"}\n````\"))\n````\"})\n````\"}\n```\")\"} } \"Lira\"\n````}\"}\n``\"{``\")\n````\"))\")\n``}`}\")\n````\")\n```\"}\"}`\"`\"})``\")} ````}\") \")\n````\") \") \"}\n````\"}}``}{\")\n``\") \"))\n````\")} \"\n````)\"\n````})) \"Lina!\"\n````\"}\")\n``}\"\n``}\n```}`}`}\" }\n``}}}}}\n``}})}`\n``}`\"}`\"}\n``\"`\")\n``\"\n``\"}\n\"}}\n``\"}\"}\")\n} `}`\" ````\")}\n}\n``}`)\" `}`}\"}\n`````\"}\n`)}`\" `}` `\" \"`\") \"\") \"\" }\n```) \"}{} {} } } } `{}`\"\n``\"} `}\n``\"} \")\") \"\")\n``\"`\") \"\" \"\n``}`\"}\" \"}{\"}\n``\"}`\" )}\n````)}) \"Lora!\"}`\")\n``\"`\n``\"\" \"\"}\n``\"}\n\"``\"``\")\n)} ````}) `}`) \"Lara?\"})\n````\"}) \"Lorene?\"\n````/\")\n````)\")\n``\"`)\n````)`\n`````) \"La la!\")\n````\"/)\n``\" }\n``\" ``) \") \"\n``\" `\"}\"} {\"Liaison...\" \"Lire...\"}\n``\" } } }\n` }` } } \"{} ` } } {} } {})\n``\" \"}\n``\" `}\n``\" \"L'etape\"\n``\" })\n``\" \")\n``\" La vie en rose...\")\n``\" \"\")\n``\" ')\n``\"?????\n``\"????)??)?\n``\"??))\n``\"??????)\n``\"?????)???)))))))))))))\")\")\n``\"!!!\")\n``!!!!!!!!!\")\n``!!!!!!!!!!!!!!\"\"\")\n``!!!!!!!!!!!!!!!!!\")\")\n``\"`\"}\n``}\"} } } `}`} ` } `} `} } } {}\n``\"} }\n``\"} } `}\"}`\"} }\n`}`\"} }\"} }\n}`\"}\") \") \"} \")\n``} `}\"`\"} `\"} `}` \"}\n``} \" ) \" )\") \"))\") ))\n``\"!!!!!!!!!!!\")\n``} ````\"}\n} } ````\")\") \")\n``\"} `} }\n``\") `}`\"} ````\")\n} }``}`}```\"}\") `````` ```` ``}`\") \"Oui!)\n```` \"}\n``\"} ``\") ``)} } ``} ``\"} }` }\n``} }\n`}} } } }}\n``\"!)\") ``\"} `}\"\") } } ) } } ``}`\"} `) ``} }`) `````) ``} `) `}`}`}`\"} \"}``) `}``) \"}`\"\") `)`}``)\") } }) }\n``\"`\"} ``)`\") \") \") } )`) `}\" `}\"\")\n``\"}``\"})``\"\")\") `}\"`)``\"})`\"}`) `\"}\")`) `\"`\")`) ```) ``}`) `}\"``\"`) ``\")``\"!!!!!!\")\n} }\n} } `\"`\"} `\") \")} } `)`\"!!!!!!!!!!!!!!\")\n``!!!!!!!!!!\")\n} \" } `\") `)\") `}`\") } `) } }`) \"L'instant de sagesse...\"\n````/\") \"L'id\u00e9e du jeu...\"\n``\"}`\"} \"L'enfant terrible...)\n````.\") ``}`\"`) } )\") `\"}`\") `}\"} `)` } `)\" `\"`}` `}\" \")}\") )\") ) \") \"La philosophie...'\")\n```\"} `\"}` `}` \"La conscience philosophique...\")\n```'}') `}` `\")`\")\")``}``}`\"``}`}\"`"""

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

````)}```}````}}}}} Here's some actual text with useful information for the user.

)}}``}}
```)}
```}\n``}`}``}}
"""

# Test 4: Przykład z bardziej złożonymi znacznikami z prawdziwych logów
test4 = """Lira's Response\n\n```\n\n\n```\n/lira/responses/userquery\n```\n/helloagain/howdiditgo?\n```\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n```\n''\n\n```\n`/liraresponses/userresponse/helpingoutwithquestions/orbitting/theanswer/tothisquestion\n```\n\n```\n// lira/ responses/ userquery /\n```\n/yetanotherwaytogetthistogether/\n```\n\n\n\n\n\n\n\n```\n/'/helpingout/\n```\n/myownwords...\n```\n\n\n\n\n\n\n```\n/nothinglikehavingafreshstarttomyself/questionsfortheotherone/\n```\n\n\n\n\n\n\n\n\n\n```\n/canweser/\n```\n\n\n\n\n\n```\n\n```\n\n\n\n\n\n/Lira'sResponses/HelpingOutWithQuestions/OrbittaTheAnswerToThisQuestion/\n```\n\n(laugh)\n```\n/aftersomeofourlastconversations/well/,buti'llbebrief/\n```\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n```\n/inabrushwithmyownwords/asiforyouwereaskingmeabouttheselfsame/\n```)\n```\n/butihaventgottenanyfurtheryet/i/guessidontknowwhatafterall/\n```)```/laugh/)\n```"""

print("=== Test 1 (z logów) ===")
print(cleanup_response(test_from_logs))
print("\n=== Test 2 ===")
print(cleanup_response(test2))
print("\n=== Test 3 ===")
print(cleanup_response(test3))
print("\n=== Test 4 ===")
print(cleanup_response(test4))