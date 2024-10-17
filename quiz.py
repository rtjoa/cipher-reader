#!/usr/bin/env python3
from dataclasses import dataclass
from collections import Counter
from urllib.request import urlretrieve
from random import choice
from typing import TypeVar, Generic
import os
import subprocess
import string
import argparse

WORD_SOURCE="https://raw.githubusercontent.com/first20hours/google-10000-english/refs/heads/master/google-10000-english-no-swears.txt"
CACHE_FILE="common_words.txt"
CIPHER_FILE="cipher.txt"

MNEMONIC_OVERRIDES=[]
MNEMONIC_OVERRIDES_FILE = "mnemonic_overrides.txt"
if os.path.exists(MNEMONIC_OVERRIDES_FILE):
    with open(MNEMONIC_OVERRIDES_FILE) as file:
        for line in file.readlines():
            if stripped := line.strip():
                MNEMONIC_OVERRIDES.append(stripped)

# Global state: cipher map
m = None

alphabet = "abcdefghijklmnopqrstuvwxyz"

def set_cipher():
    while len(cipher := input(f"{alphabet} should correpond to:\n")) != 26:
        print("len 26 required")
    with open(CIPHER_FILE, "w") as file:
        file.write(cipher)
    return cipher

def try_get_cipher():
  if not os.path.exists(CIPHER_FILE):
      return False, f"{CIPHER_FILE} doesn't exist"
  with open(CIPHER_FILE, "r") as file:
      s = file.read().strip()
      if len(s) != 26:
          return False, f"cipher should have length 26. read {CIPHER_FILE} to be:\n{s}"
      return True, s

def get_cipher_set_if_needed():
    success, cipher_or_error = try_get_cipher()
    if success:
        cipher = cipher_or_error
    else:
        print(cipher_or_error)
        cipher = set_cipher()
    return {k:v for k, v in zip(alphabet, cipher, strict=True)}

def common_words():
  if not os.path.exists(CACHE_FILE):
      subprocess.run(["wget", WORD_SOURCE, "-O", CACHE_FILE])

  with open(CACHE_FILE, "r") as file:
      return [s.strip() for s in file.readlines()]

def get_words(letters_mode):
    if letters_mode:
        return list(m)
    return common_words()

def show_dict(d, order=None):
    if order is None:
        order = d.keys()
    return ' '.join(f"{k}{d[k]}" for k in order)

def play_game(letters_mode):
    words = get_words(letters_mode)
    word_to_streak = Counter()
    word_to_cooldown = Counter()
    history = []
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        if letters_mode:
            order = sorted(word_to_cooldown.keys(), key=lambda k:(word_to_streak[k],word_to_cooldown[k]))
            print(f"streak   {show_dict(word_to_streak, order)}")
            print(f"cooldown {show_dict(word_to_cooldown, order)}")
        word = choice(words)
        if word_to_cooldown[word] > 0:
            word_to_cooldown[word] -= 1
            continue

        recent_history = history[-50:]
        # print(f"{sum(history)}/{len(history)} overall | {sum(recent_history)}/{len(recent_history)} recent")
        print(f"{sum(recent_history)}/{len(recent_history)} recent")
        translated = ''.join(m[c] for c in word)
        print(translated)
        right = True
        while input("> ") != word:
            right = False
        if right:
            word_to_streak[word] += 1
        else:
            word_to_streak[word] = max(0, word_to_streak[word] - 1)
        word_to_cooldown[word] = 2 ** word_to_streak[word] - 1
        history.append(right)

def mnemonic_goodness(word):
    if 4 <= len(word) <= 7:
        return 3
    if len(word) >= 3:
        return 2
    return 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--letters-mode", action="store_true")
    parser.add_argument("-c", "--cheatsheet", action="store_true")
    parser.add_argument("-s", "--set-cipher", action="store_true")
    args = parser.parse_args()

    global m
    if args.set_cipher:
        m = set_cipher()
    else:
        m = get_cipher_set_if_needed()

    if args.cheatsheet:
        l = list(m.items())
        l.sort(key=lambda kv:kv[1])
        print(" ".join(v for (k, v) in l))
        print(" ".join(k for (k, v) in l))
        print()
        overrides = {w[0]+w[-1]:w for w in MNEMONIC_OVERRIDES}
        for k, v in l:
            if (v + k) in overrides:
                print(overrides[v + k])
                continue
            mnemonics = list(filter(
                lambda w: w.startswith(v) and w.endswith(k),
                common_words()
            ))
            print(max(mnemonics, key=mnemonic_goodness, default=v+k))
        print()
        return

    play_game(args.letters_mode)

main()
