# TG Names Roller

[![Windows](https://img.shields.io/badge/Windows-supported-0078D6?logo=windows&logoColor=white)](./README.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](./README.md)
[![GUI](https://img.shields.io/badge/Interface-GUI%20%2B%20CLI-4B8BBE)](./README.md)
[![Languages](https://img.shields.io/badge/Languages-RU%20%2F%20EN-2ea44f)](./README.md)

Русская версия: [README.md](./README.md)

> [!WARNING]
> This software is provided strictly for educational and research purposes.
> It is not intended for brute force activity, platform abuse, bypassing service restrictions, or any other misuse that may violate platform rules.
> All results are analytical only and may require manual verification.

## Why this project exists and what it does

**TG Names Roller** helps users discover rare, interesting, and potentially free usernames across multiple platforms.

It is useful if you want to:
- search for unusual username ideas for Telegram, Fragment, and other services
- generate custom candidate lists using flexible rules
- quickly filter out busy usernames
- look for short, rare, or stylistically fitting usernames for a specific use case

Supported check targets:
- Telegram
- Fragment
- Instagram
- X
- TikTok
- YouTube
- GitHub

## How it works

The workflow is split into two stages:

1. **Candidate generation**
   - the program builds a list of usernames using configurable rules
   - it can generate names from English words, transliterated Russian words, or random Latin letters
   - you can control length, word rarity, number of words, prefix, and suffix

2. **Username checking**
   - the program takes a prepared username list and checks it against selected platforms
   - busy names are filtered out
   - free names can be exported to a separate file
   - checking order can be changed: in order, random, shortest first, or longest first

From an end user perspective, this means the tool helps you first assemble strong candidates and then quickly separate promising usernames from unavailable ones.

## Main features

### Username generator

- generate usernames from English words
- generate usernames from transliterated Russian words
- generate random strings made of Latin letters
- configure total username length
- configure how many words each username contains
- choose word quality from more common to rarer words
- add a custom prefix
- add a custom suffix
- optionally insert `a`, `an`, `the`
- collapse repeated letters inside individual words
- use `seed` for reproducible generation
- control dictionary scan depth through `scan`

### Username checker

- check username lists across multiple platforms
- select exactly which services to include
- run parallel checks with configurable workers
- limit how many lines are processed
- configure delay between checks
- export FREE usernames to `found.txt`
- hide `BUSY` lines if needed
- support pause and graceful stop behavior

### Interface

- GUI launch through `run_gui.bat`
- CLI launch for manual control
- **Russian and English interface support**
- config save and load
- autosave of the latest settings

## Available filters and search settings

The project provides flexible controls for shaping the desired username:

- **Username length**
  - exact length
  - minimum and maximum length

- **Word rarity**
  - quality range from more popular words to rarer words

- **Words per username**
  - single word usernames
  - multi-word usernames

- **Generation source**
  - English words
  - transliterated Russian words
  - random Latin letters

- **Username form**
  - custom prefix
  - custom suffix
  - articles
  - repeated-letter collapsing

- **Checking filters**
  - platform selection
  - line limit
  - check order
  - worker count
  - delay between requests

## Launch methods

### Option 1. GUI launch

1. Open the project folder.
2. On the first run, install dependencies with `install_deps.bat`.
3. Then launch `run_gui.bat`.

You can also launch the GUI directly through `TG Names Roller.pyw`.

### Option 2. CLI launch

First install dependencies:

```bat
install_deps.bat
```

Then use console commands for generation and checking.

## Console commands for installation and launch

### Install dependencies

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Launch GUI

```bat
run_gui.bat
```

### Example: generate usernames

```bat
.venv\Scripts\python.exe generate_words.py --out words.txt --count 300 --min-len 5 --max-len 10 --min-quality 3 --max-quality 5 --min-words 1 --max-words 2 --generator-mode translit --prefix neo --suffix x
```

### Example: check usernames

```bat
.venv\Scripts\python.exe tg_fragment_username_checker.py --wordlist words.txt --check-telegram --check-fragment --check-instagram --check-x --check-tiktok --check-youtube --check-github --workers 4 --delay 0.2 --order random --found-out found.txt
```

## Short file overview

### Core files

- `tg_names_roller_gui.py`
  - main graphical interface
  - combines generator, checker, configs, and UI settings

- `generate_words.py`
  - CLI username generator
  - creates username lists using length, quality, generation mode, prefix, suffix, and other parameters

- `tg_fragment_username_checker.py`
  - CLI username checker
  - checks username lists across selected services and prints `FREE`, `BUSY`, `UNKNOWN`

- `TG Names Roller.pyw`
  - lightweight launcher for opening the GUI without manually running the main `.py` file

### Helper files

- `run_gui.bat`
  - quick Windows launcher for the GUI version

- `install_deps.bat`
  - installs dependencies into the local `.venv`

- `requirements.txt`
  - Python dependency list for the project

### Folders and data files

- `configs/`
  - saved configs and latest UI state

- `assets/`
  - graphical assets used by the application

- `words.txt`
  - generated or prepared username list for checking

- `found.txt`
  - exported FREE usernames

## Who this project is for

This project may be useful for:
- username niche researchers and resellers
- users looking for a rare nickname for a personal brand
- people who want to test username ideas across several platforms
- users who need a local GUI tool without heavy setup

## Notes

- some platforms may respond inconsistently or apply request limits
- some usernames still require manual verification before use
- higher `workers` and lower `delay` increase the chance of hitting limits

## Screenshots

You can add screenshots of the interface, generator, and checker results here.
