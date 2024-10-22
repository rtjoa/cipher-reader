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
import sys

def wrt_script(path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.join(os.path.dirname(__file__), path)

def path_exists_wrt_script(path):
    return os.path.exists(wrt_script(path))

WORD_SOURCE="https://raw.githubusercontent.com/first20hours/google-10000-english/refs/heads/master/google-10000-english-no-swears.txt"
CACHE_FILE="common_words.txt"
DEFAULT_CIPHER_FILE="cipher.txt"

MNEMONIC_OVERRIDES=[]
MNEMONIC_OVERRIDES_FILE = "mnemonic_overrides.txt"
if path_exists_wrt_script(MNEMONIC_OVERRIDES_FILE):
    with open(wrt_script(MNEMONIC_OVERRIDES_FILE)) as file:
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

def set_cipher(cipher_file):
    print(f"setting {cipher_file}")
    while len(cipher := input(f"{alphabet} should correpond to:\n")) != 26:
        print("len 26 required")
    with open(wrt_script(cipher_file), "w") as file:
        file.write(cipher)
    return cipher

def try_get_cipher(cipher_file):
  if not path_exists_wrt_script(cipher_file):
      return False, f"{cipher_file} doesn't exist"
  with open(wrt_script(cipher_file), "r") as file:
      s = file.read().strip()
      if len(s) != 26:
          return False, f"cipher should have length 26. read {cipher_file} to be:\n{s}"
      return True, s

def get_cipher_set_if_needed(cipher_file):
    success, cipher_or_error = try_get_cipher(cipher_file)
    if success:
        cipher = cipher_or_error
    else:
        print(cipher_or_error)
        cipher = set_cipher(cipher_file)
    return {k:v for k, v in zip(alphabet, cipher, strict=True)}

def common_words():
  if not path_exists_wrt_script(CACHE_FILE):
      subprocess.run(["wget", WORD_SOURCE, "-O", CACHE_FILE])

  with open(wrt_script(CACHE_FILE), "r") as file:
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
        print(f"? {translated}")
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

def translate(s, reverse=False, error_on_unspecified_char=True):
    m_ = m
    if reverse:
        m_ = {v:k for k, v in m.items()}
    def translate_char(c):
        if c in m_:
            return m_[c]
        elif error_on_unspecified_char:
            raise ValueError(f"{c} {m_}")
        else:
            return c
    return "".join(map(translate_char, s))

def main():
    parser = argparse.ArgumentParser()
    # flag of all subcommands
    parser.add_argument("-i", "--input-cipher-file", default=DEFAULT_CIPHER_FILE)

    # flag of the "quiz" subcommand
    parser.add_argument("-l", "--letters-mode", action="store_true")

    # TODO: these should be subcommands (using subparsers) instead of flags
    # the lack of any of the following indicates the "quiz" subcommand
    parser.add_argument("-c", "--cheatsheet", action="store_true")
    parser.add_argument("-s", "--set-cipher", action="store_true")
    parser.add_argument("-t", "--translate-mode", action="store_true")

    # this should be a flap called --reverse to translate mode
    parser.add_argument("-u", "--untranslate-mode", action="store_true")

    args = parser.parse_args()

    global m
    if args.set_cipher:
        m = set_cipher(args.input_cipher_file)
    else:
        m = get_cipher_set_if_needed(args.input_cipher_file)

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

    if args.translate_mode:
        for line in list(sys.stdin):
            print(translate(line, error_on_unspecified_char=False), end='')
        return
    
    if args.untranslate_mode:
        for line in list(sys.stdin):
            print(translate(line, reverse=True, error_on_unspecified_char=False), end='')
        return

    play_game(args.letters_mode)

main()
