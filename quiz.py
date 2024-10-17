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
import time

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

def unique(it):
    seen = set()
    for x in it:
        if x not in seen:
            yield x
            seen.add(x)

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
    times = []
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        if letters_mode:
            order = sorted(word_to_cooldown.keys(), key=lambda v:(word_to_streak[v],word_to_cooldown[v]))
            print(f"streak   {show_dict(word_to_streak, order)}")
            print(f"cooldown {show_dict(word_to_cooldown, order)}")
        word = choice(words)
        translated = ''.join(m[c] for c in word)
        if word_to_cooldown[translated] > 0:
            word_to_cooldown[translated] -= 1
            continue

        recent_history = history[-50:]
        recent_times = times[-50:]
        # print(f"{sum(history)}/{len(history)} overall | {sum(recent_history)}/{len(recent_history)} recent")
        print(f"correct: {sum(recent_history)}/{len(recent_history)}")
        print(f"sec/answer: {sum(recent_times)/len(recent_times) if recent_times else float('inf'):.2f}")
        print(f"")
        print(translated)
        right = True
        gave_up = False
        tic = time.monotonic()
        while (guess := input("> ")) != word:
            if guess == " ":
                gave_up = True
                right = False
                for k in unique(word):
                    print(get_mnemonic(k))
                input()
                break
            right = False
        toc = time.monotonic()
        if not gave_up:
            word_to_streak[translated] += 1
            times.append(toc - tic)
        else:
            word_to_streak[translated] = max(0, word_to_streak[translated] - 1)
        word_to_cooldown[translated] = 2 ** word_to_streak[translated] - 1
        history.append(right)

def mnemonic_goodness(word):
    if 4 <= len(word) <= 7:
        return 3
    if len(word) >= 3:
        return 2
    return 1

def get_mnemonic(k):
    v = m[k]
    overrides = {w[0]+w[-1]:w for w in MNEMONIC_OVERRIDES}
    if (v + k) in overrides:
        return overrides[v + k]
    mnemonics = list(filter(
        lambda w: w.startswith(v) and w.endswith(k),
        common_words()
    ))
    return max(mnemonics, key=mnemonic_goodness, default=v+k)

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
        for k, v in l:
            print(get_mnemonic(k))
        print()
        return

    play_game(args.letters_mode)

main()
