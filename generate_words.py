from __future__ import annotations

import argparse
import random
import re
import string
from pathlib import Path

RX = re.compile(r"^[a-z]+$")
COMPLEX_BITS = ("tion", "sion", "ough", "eigh", "cial", "tial", "ph", "rh", "mn", "kn", "wr", "ei", "ie", "gue", "que")
STOPWORDS = {
    "the", "and", "for", "that", "you", "your", "are", "was", "were", "with", "this", "from", "have", "has",
    "had", "not", "but", "they", "their", "them", "she", "her", "him", "his", "our", "ours", "its", "who",
    "what", "when", "where", "why", "how", "can", "could", "would", "should", "will", "shall", "may",
    "might", "than", "then", "there", "here", "also", "into", "onto", "over", "under", "about", "after",
    "before", "because", "while", "during", "each", "other", "some", "such", "more", "most", "very",
}
ARTICLES = ("a", "an", "the")
RU_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}


def require_wordfreq():
    try:
        from wordfreq import top_n_list, zipf_frequency
    except Exception:
        print("wordfreq is required. Install it:")
        print("  python -m pip install wordfreq")
        raise SystemExit(2)
    return top_n_list, zipf_frequency


def normalize(word: str) -> str | None:
    word = re.sub(r"[^a-z]", "", word.strip().lower())
    if RX.match(word):
        return word
    return None


def collapse_repeated_letters(word: str) -> str:
    return re.sub(r"([a-z])\1+", r"\1", word)


def translit_ru(word: str) -> str | None:
    raw = "".join(RU_TO_LAT.get(ch, "") for ch in word.strip().lower())
    return normalize(raw)


def quality_from_word(word: str, zipf: float) -> int:
    complexity = len(word) + sum(2 for bit in COMPLEX_BITS if bit in word)
    if zipf >= 5.0 and complexity <= 6:
        return 1
    if zipf >= 4.45 and complexity <= 8:
        return 2
    if zipf >= 3.75 and complexity <= 10:
        return 3
    if zipf >= 3.0 and complexity <= 13:
        return 4
    return 5


def get_top(top_n_list, lang: str, n: int):
    try:
        return top_n_list(lang, n)
    except TypeError:
        return top_n_list(lang, n_top=n)


def collect_words(scan: int, min_q: int, max_q: int, max_piece_len: int, mode: str, dedupe_letters: bool) -> list[tuple[str, float, int]]:
    top_n_list, zipf_frequency = require_wordfreq()
    seen: set[str] = set()
    candidates: list[tuple[str, float, int]] = []

    if mode == "translit":

        for item in get_top(top_n_list, "ru", scan):
            w = translit_ru(item)
            if w and dedupe_letters:
                w = collapse_repeated_letters(w)
            if not w or w in seen or len(w) < 3 or len(w) > max_piece_len:
                continue
            seen.add(w)
            freq = zipf_frequency(item, "ru")
            q = quality_from_word(w, freq)
            if min_q <= q <= max_q:
                candidates.append((w, freq, q))
    else:
        for item in get_top(top_n_list, "en", scan):
            w = normalize(item)
            if w and dedupe_letters:
                w = collapse_repeated_letters(w)
            if not w or w in seen or w in STOPWORDS or len(w) > max_piece_len:
                continue
            seen.add(w)
            freq = zipf_frequency(item, "en")
            q = quality_from_word(w, freq)
            if min_q <= q <= max_q:
                candidates.append((w, freq, q))

    candidates.sort(key=lambda x: (-x[1], len(x[0]), x[0]))
    if min_q >= 4 or mode == "translit":
        random.shuffle(candidates)
    return candidates


def generate_random_letters(count: int, min_len: int, max_len: int, prefix: str = "", suffix: str = "") -> list[str]:
    prefix = clean_affix(prefix)
    suffix = clean_affix(suffix)
    fixed_len = len(prefix) + len(suffix)
    if fixed_len >= max_len:
        return []

    min_core_len = max(1, min_len - fixed_len)
    max_core_len = max(1, max_len - fixed_len)
    alphabet = string.ascii_lowercase
    result: list[str] = []
    seen: set[str] = set()
    attempts = max(count * 300, 5000)

    for _ in range(attempts):
        if len(result) >= count:
            break
        core_len = random.randint(min_core_len, max_core_len)
        name = prefix + "".join(random.choice(alphabet) for _ in range(core_len)) + suffix
        if min_len <= len(name) <= max_len and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def clean_affix(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.strip().lower())


def smart_article(next_word: str, prefer_the: bool) -> str:
    if prefer_the:
        return "the"
    if next_word[:1] in "aeiou":
        return "an"
    return "a"


def maybe_with_articles(words: list[str], add_articles: bool, min_len: int, max_len: int, prefix: str, suffix: str) -> str:
    if not add_articles:
        return prefix + "".join(words) + suffix


    variants: list[list[str]] = []
    if words:
        variants.append([smart_article(words[0], prefer_the=False)] + words)
    if len(words) >= 2:
        middle = [words[0]]
        for w in words[1:]:
            middle.extend([smart_article(w, prefer_the=True), w])
        variants.append(middle)
    if len(words) >= 3:
        mixed = [smart_article(words[0], prefer_the=False), words[0]]
        for w in words[1:]:
            if random.random() < 0.55:
                mixed.append(smart_article(w, prefer_the=True))
            mixed.append(w)
        variants.append(mixed)

    random.shuffle(variants)
    for parts in variants:
        name = prefix + "".join(parts) + suffix
        if min_len <= len(name) <= max_len:
            return name
    return prefix + "".join(words) + suffix


def generate(
    count: int,
    min_len: int,
    max_len: int,
    min_q: int,
    max_q: int,
    scan: int,
    seed: int | None = None,
    min_words: int = 1,
    max_words: int = 1,
    generator_mode: str = "english_words",
    add_articles: bool = False,
    dedupe_letters: bool = False,
    prefix: str = "",
    suffix: str = "",
) -> list[str]:
    if seed is not None:
        random.seed(seed)

    prefix = clean_affix(prefix)
    suffix = clean_affix(suffix)
    fixed_len = len(prefix) + len(suffix)
    if fixed_len >= max_len:
        return []

    if generator_mode == "random_letters":
        return generate_random_letters(count, min_len, max_len, prefix, suffix)

    pool = collect_words(scan, min_q, max_q, max_len - fixed_len, generator_mode, dedupe_letters)
    if not pool:
        return []

    words_by_len: dict[int, list[str]] = {}
    for w, _freq, _q in pool:
        words_by_len.setdefault(len(w), []).append(w)

    result: list[str] = []
    seen: set[str] = set()
    attempts = max(count * 200, 3000)

    for _ in range(attempts):
        if len(result) >= count:
            break
        n_words = random.randint(min_words, max_words)
        parts: list[str] = []
        for _i in range(n_words):

            used = fixed_len + sum(len(x) for x in parts)
            reserve = max(0, n_words - len(parts) - 1) * 2
            allowed = max_len - used - reserve
            possible = [w for length, arr in words_by_len.items() if length <= allowed for w in arr]
            if not possible:
                break
            parts.append(random.choice(possible))
        if len(parts) != n_words:
            continue
        name = maybe_with_articles(parts, add_articles, min_len, max_len, prefix, suffix)
        if not RX.match(name):
            continue
        if min_len <= len(name) <= max_len and name not in seen:
            seen.add(name)
            result.append(name)


    if min_words == max_words == 1 and generator_mode == "english_words" and not add_articles and not prefix and not suffix:
        simple = []
        for w, _freq, _q in pool:
            name = prefix + w + suffix
            if min_len <= len(name) <= max_len and name not in simple:
                simple.append(name)
            if len(simple) >= count:
                break
        return simple

    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Generate a-z username wordlist using wordfreq")
    p.add_argument("--out", default="words.txt", help="Output wordlist path")
    p.add_argument("--count", type=int, default=200)
    p.add_argument("--quality", type=int, choices=range(1, 6), help="Exact quality 1..5")
    p.add_argument("--min-quality", type=int, default=None)
    p.add_argument("--max-quality", type=int, default=None)
    p.add_argument("--length", type=int, help="Exact total username length")
    p.add_argument("--min-len", type=int, default=5)
    p.add_argument("--max-len", type=int, default=10)
    p.add_argument("--min-words", type=int, default=1)
    p.add_argument("--max-words", type=int, default=1)
    p.add_argument("--generator-mode", choices=("english_words", "translit", "random_letters"), default="english_words")
    p.add_argument("--include-translit", action="store_true")
    p.add_argument("--add-articles", action="store_true")
    p.add_argument("--dedupe-letters", action="store_true", help="Collapse repeated letters inside each word before composing usernames")
    p.add_argument("--prefix", default="")
    p.add_argument("--suffix", default="")
    p.add_argument("--scan", type=int, default=120000, help="How many top wordfreq tokens to scan")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    min_len, max_len = (args.length, args.length) if args.length else (args.min_len, args.max_len)
    min_q, max_q = (args.quality, args.quality) if args.quality else (
        args.min_quality if args.min_quality is not None else 1,
        args.max_quality if args.max_quality is not None else 5,
    )

    if min_len < 5 or max_len < min_len or max_len > 32:
        raise SystemExit("Bad length range")
    if min_q < 1 or max_q > 5 or max_q < min_q:
        raise SystemExit("Bad quality range")
    if args.min_words < 1 or args.max_words > 10 or args.max_words < args.min_words:
        raise SystemExit("Bad words range")

    generator_mode = args.generator_mode
    if args.include_translit and generator_mode == "english_words":
        generator_mode = "translit"

    result = generate(
        args.count,
        min_len,
        max_len,
        min_q,
        max_q,
        args.scan,
        args.seed,
        args.min_words,
        args.max_words,
        generator_mode,
        args.add_articles,
        args.dedupe_letters,
        args.prefix,
        args.suffix,
    )

    out = Path(args.out).expanduser()
    out.write_text("\n".join(result) + ("\n" if result else ""), encoding="utf-8")

    print(f"Generated {len(result)} usernames -> {out}")
    if generator_mode == "random_letters":
        print(f"Length: {min_len}..{max_len}, mode: random letters")
    else:
        print(f"Length: {min_len}..{max_len}, quality: {min_q}..{max_q}, words: {args.min_words}..{args.max_words}, scanned: {args.scan}")
    if generator_mode == "translit":
        print("Translit: only transliterated ru words from wordfreq")
    elif generator_mode == "random_letters":
        print("Source: random letters a-z")
    if args.add_articles:
        print("Articles: enabled")
    if args.dedupe_letters:
        print("Repeated letters: collapsed inside each word")
    if len(result) < args.count:
        print("Not enough usernames found. Try larger --scan or wider length/quality/words range.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
