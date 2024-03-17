#!/usr/bin/env python3
from sys import argv

def suggest_words(letters):
        suggestions = []
        with open('data/dictionary-weird.txt', 'r') as words_file:
            for line in words_file:
                word = line.strip()
                if can_spell(letters, word):
                    suggestions.append(word)
        return suggestions

def can_spell(letters, word):
    letters = sorted(letters)
    word = list(word)
    for letter in letters:
        if len(word) == 0:
            return True
        elif letter in word:
            word.remove(letter)
    return len(word) == 0

def de_dupe_file(filename):
    words = []
    set_words = set()
    with open('data/dictionary-weird.txt', 'r') as words_file:
            for line in words_file:
                word = line.strip()
                words.append(word)
                set_words.add(word)
    
    print(len(words), len(set_words)) 
