from __future__ import annotations

import argparse
import html
import random
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

USERNAME_RE_TEMPLATE = r"^[a-z]{{{min_len},{max_len}}}$"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
]

SERVICE_PRIORITY = ["instagram", "tiktok", "x", "youtube", "telegram", "github", "fragment"]
SERVICE_LABELS = {
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "x": "X",
    "youtube": "YouTube",
    "telegram": "Telegram",
    "github": "GitHub",
    "fragment": "Fragment",
}


def fetch(url: str, timeout: int = 15) -> tuple[int, str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "ignore")
            return r.status, raw, ""
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore") if e.fp else ""
        return e.code, body, f"HTTPError: {e.code}"
    except Exception as e:
        return 0, "", f"{type(e).__name__}: {e}"


def looks_limited(code: int | str | None, error: str = "") -> bool:
    if code in {401, 403, 429, 500, 502, 503, 504}:
        return True
    low = (error or "").lower()
    return any(bit in low for bit in ("timed out", "timeout", "too many requests", "rate", "reset", "remote end closed"))


def clean_text(s: str) -> str:
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def parse_fragment_status(username: str, body: str) -> tuple[str, str]:
    text = clean_text(body).lower()
    if "already claimed this username on telegram" in text:
        return "claimed_telegram", "Fragment: already claimed on Telegram"

    m = re.search(
        r'<span class="tm-section-header-status[^"]*\s(tm-status-[^"]+)"[^>]*>(.*?)</span>',
        body,
        flags=re.S | re.I,
    )
    if m:
        css = m.group(1).lower()
        label = clean_text(m.group(2)).lower()
        if "avail" in css or "available" in label:
            if "place bid" in body.lower() or "start auction" in body.lower():
                return "available_bid", "Fragment: available, minimum bid page"
            return "available", f"Fragment status: {label}"
        if "unavail" in css:
            if "sold" in label:
                return "sold", "Fragment: sold"
            if "auction" in label:
                return "auction", f"Fragment: {label}"
            if "not for sale" in text:
                return "not_for_sale", "Fragment: not for sale"
            return "unavailable", f"Fragment status: {label or 'unavailable'}"

    row_pat = rf'<tr[^>]+data-username="@{re.escape(username)}"[^>]*>(.*?)</tr>'
    row = re.search(row_pat, body, flags=re.S | re.I)
    if row:
        text = clean_text(row.group(1)).lower()
        if "not for sale" in text:
            return "not_for_sale", "Fragment search row: not for sale"
        if "unavailable" in text:
            return "unavailable", "Fragment search row: unavailable"
        if "sold" in text:
            return "sold", "Fragment search row: sold"
        if "auction" in text:
            return "auction", "Fragment search row: auction"
        return "unknown", f"Fragment row found: {text[:120]}"

    if "place bid and start auction" in text:
        return "available_bid", "Fragment: place bid button found"
    if "not for sale" in text:
        return "not_for_sale", "Fragment: not for sale"
    return "unknown", "Fragment: status not parsed"


def parse_tme_status(username: str, body: str, code: int) -> tuple[str, str]:
    if code in (404, 410):
        return "not_found", f"t.me HTTP {code}"
    low = body.lower()
    if "tgme_page_title" in low or "tgme_page_extra" in low:
        return "exists", "t.me public page has title/extra"
    if "tgme_username_link" in low and f"domain={username}" in low:
        return "not_found", "t.me generic resolve/contact page"
    if "username not found" in low:
        return "not_found", "t.me says username not found"
    return "unknown", "t.me status not parsed"


def parse_instagram_status(username: str, body: str, code: int) -> tuple[str, str]:
    if code in (404, 410):
        return "not_found", f"Instagram HTTP {code}"
    low = body.lower()
    if f'"username":"{username}"' in low or f"(@{username})" in low:
        return "exists", "Instagram profile markers found"
    if '"profile_id":"' not in low and 'property="og:title"' not in low and 'property="og:description"' not in low:
        title = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.I | re.S)
        if title and clean_text(title.group(1)).lower() == "instagram":
            return "generic", "Instagram returned generic page without profile markers"
    return "unknown", "Instagram status not parsed"


def parse_x_status(username: str, body: str, code: int) -> tuple[str, str]:
    if code in (404, 410):
        return "not_found", f"X HTTP {code}"
    low = body.lower()
    if f'"screen_name":"{username}"' in low:
        return "exists", "X profile markers found"
    if f'"errors":{{"{username}":' in low and '"code":50' in low:
        return "not_found", "X reported unknown user"
    if f'"errors":{{"{username}":' in low and '"code":63' in low:
        return "exists", "X account is suspended"
    if f'"fetchstatus":{{"{username}":"failed"' in low and '"code":63' in low:
        return "exists", "X account is suspended"
    if f'"fetchstatus":{{"{username}":"failed"' in low:
        return "not_found", "X fetch by screen name failed"
    return "unknown", "X status not parsed"


def parse_tiktok_status(username: str, body: str, code: int) -> tuple[str, str]:
    if code in (404, 410):
        return "not_found", f"TikTok HTTP {code}"
    low = body.lower()
    if f'"uniqueid":"{username}"' in low and '"userinfo":' in low:
        return "exists", "TikTok profile markers found"
    if '"webapp.user-detail":{"statuscode":10221' in low or '"webapp.user-detail":{"statuscode":10202' in low:
        return "not_found", "TikTok reported unknown user"
    return "unknown", "TikTok status not parsed"


def parse_youtube_status(username: str, body: str, code: int) -> tuple[str, str]:
    if code in (404, 410):
        return "not_found", f"YouTube HTTP {code}"
    low = body.lower()
    if f"https://www.youtube.com/@{username}" in low or 'property="og:title"' in low:
        return "exists", "YouTube channel page found"
    return "unknown", "YouTube status not parsed"


def parse_github_status(username: str, body: str, code: int) -> tuple[str, str]:
    if code in (404, 410):
        return "not_found", f"GitHub HTTP {code}"
    low = body.lower()
    if code == 200 and f"/{username}" in low:
        return "exists", "GitHub profile page found"
    return "unknown", "GitHub status not parsed"


def service_url(service: str, username: str) -> str:
    if service == "telegram":
        return f"https://t.me/{username}"
    if service == "fragment":
        return f"https://fragment.com/username/{username}"
    if service == "instagram":
        return f"https://www.instagram.com/{username}/"
    if service == "x":
        return f"https://x.com/{username}"
    if service == "tiktok":
        return f"https://www.tiktok.com/@{username}"
    if service == "youtube":
        return f"https://www.youtube.com/@{username}"
    if service == "github":
        return f"https://github.com/{username}"
    raise ValueError(f"Unknown service: {service}")


def parse_service_status(service: str, username: str, body: str, code: int) -> tuple[str, str]:
    if service == "telegram":
        return parse_tme_status(username, body, code)
    if service == "fragment":
        return parse_fragment_status(username, body)
    if service == "instagram":
        return parse_instagram_status(username, body, code)
    if service == "x":
        return parse_x_status(username, body, code)
    if service == "tiktok":
        return parse_tiktok_status(username, body, code)
    if service == "youtube":
        return parse_youtube_status(username, body, code)
    if service == "github":
        return parse_github_status(username, body, code)
    return "unknown", f"Unknown parser for {service}"


def is_busy(service: str, status: str) -> bool:
    if service == "fragment":
        return status in {"available", "available_bid", "auction", "sold", "claimed_telegram", "unavailable"}
    if service == "telegram":
        return status == "exists"
    return status == "exists"


def is_free(service: str, status: str) -> bool:
    if service == "fragment":
        return status == "not_for_sale"
    if service == "telegram":
        return status == "not_found"
    return status == "not_found"


def selected_services(args: argparse.Namespace) -> list[str]:
    selected = []
    for service in SERVICE_PRIORITY:
        if getattr(args, f"check_{service}", False):
            selected.append(service)
    return selected


def check_one(username: str, services: list[str], timeout: int, delay: float) -> dict:
    if delay > 0:
        time.sleep(random.uniform(delay * 0.5, delay * 1.5))

    first_unknown: Optional[dict] = None
    checked_free: list[str] = []
    skipped_neutral: list[str] = []
    for service in services:
        url = service_url(service, username)
        code, body, error = fetch(url, timeout=timeout)
        if looks_limited(code, error):
            if first_unknown is None:
                first_unknown = {
                    "service": service,
                    "status": "limited",
                    "note": error or f"HTTP {code}",
                    "url": url,
                }
            continue
        if not body:
            if first_unknown is None:
                first_unknown = {
                    "service": service,
                    "status": "error",
                    "note": error or "Empty response",
                    "url": url,
                }
            continue
        status, note = parse_service_status(service, username, body, int(code) if isinstance(code, int) else 0)
        if service == "instagram" and status == "generic":
            skipped_neutral.append(service)
            continue
        if is_busy(service, status):
            return {
                "username": username,
                "result": "busy",
                "service": service,
                "status": status,
                "note": note,
                "url": url,
                "skipped_neutral": skipped_neutral,
            }
        if is_free(service, status):
            checked_free.append(service)
            continue
        if first_unknown is None:
            first_unknown = {
                "service": service,
                "status": status,
                "note": note,
                "url": url,
            }

    if checked_free and len(checked_free) + len(skipped_neutral) == len(services):
        return {
            "username": username,
            "result": "free",
            "services": checked_free,
            "skipped_neutral": skipped_neutral,
        }
    if first_unknown is not None:
        return {
            "username": username,
            "result": "unknown",
            **first_unknown,
            "skipped_neutral": skipped_neutral,
        }
    return {
        "username": username,
        "result": "unknown",
        "service": services[0] if services else "telegram",
        "status": "unknown",
        "note": "No decisive status",
        "url": service_url(services[0], username) if services else "",
        "skipped_neutral": skipped_neutral,
    }


def load_words(path: Path, min_len: int, max_len: int, limit: int | None) -> list[str]:
    rx = re.compile(USERNAME_RE_TEMPLATE.format(min_len=min_len, max_len=max_len))
    seen = set()
    words = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            w = line.strip().lower()
            if not rx.match(w):
                continue
            if w in seen:
                continue
            seen.add(w)
            words.append(w)
            if limit and len(words) >= limit:
                break
    return words


def display_url(url: str) -> str:
    return re.sub(r"^https?://", "", url).rstrip("/")


def order_words(words: list[str], mode: str) -> list[str]:
    ordered = list(words)
    if mode == "random":
        ordered = random.sample(ordered, k=len(ordered))
    elif mode == "short_first":
        ordered.sort(key=lambda w: (len(w), w))
    elif mode == "long_first":
        ordered.sort(key=lambda w: (-len(w), w))
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser(description="Check English words as usernames across selected services")
    parser.add_argument("--wordlist", default="words.txt", help="Path to wordlist, one word per line")
    parser.add_argument("--min-len", type=int, default=5)
    parser.add_argument("--max-len", type=int, default=32)
    parser.add_argument("--workers", type=int, default=4, help="Parallel requests. Keep low to avoid limits")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--delay", type=float, default=0.2, help="Randomized delay per check")
    parser.add_argument("--limit", type=int, default=0, help="Max words to check, 0 means all")
    parser.add_argument("--check-telegram", action="store_true", help="Check Telegram via t.me HTML heuristic")
    parser.add_argument("--check-fragment", action="store_true", help="Check Fragment")
    parser.add_argument("--check-instagram", action="store_true", help="Check Instagram")
    parser.add_argument("--check-x", action="store_true", help="Check X / Twitter")
    parser.add_argument("--check-tiktok", action="store_true", help="Check TikTok")
    parser.add_argument("--check-youtube", action="store_true", help="Check YouTube")
    parser.add_argument("--check-github", action="store_true", help="Check GitHub")
    parser.add_argument("--pause-file", default="", help="If this file exists, checker waits before starting next requests")
    parser.add_argument("--stop-file", default="", help="If this file exists, checker flushes pending FREE usernames and stops")
    parser.add_argument("--found-out", default="", help="Append found FREE usernames to this file, one per line")
    parser.add_argument("--hide-busy", action="store_true", help="Do not print BUSY usernames")
    parser.add_argument("--order", choices=["in_order", "random", "short_first", "long_first"], default="in_order", help="Sequence of username checks")
    args = parser.parse_args()

    wordlist = Path(args.wordlist).expanduser()
    if not wordlist.exists():
        print(f"Wordlist not found: {wordlist}")
        print("Create words.txt next to this script, or pass --wordlist C:\\path\\to\\words.txt")
        return 2

    words = load_words(wordlist, args.min_len, args.max_len, args.limit or None)
    if not words:
        print("No valid words found after filtering")
        return 1
    words = order_words(words, args.order)

    services = selected_services(args)
    if not services:
        print("Nothing to check: enable at least one service")
        return 2

    enabled = [SERVICE_LABELS[s] for s in services]
    found_out = Path(args.found_out).expanduser() if args.found_out else None
    stop_path = Path(args.stop_file) if args.stop_file else None
    print(f"Loaded {len(words)} words. Checks: {', '.join(enabled)}. CSV output disabled, printing statuses.", flush=True)
    if found_out:
        print(f"FREE export: append to {found_out}", flush=True)
    if args.hide_busy:
        print("BUSY output hidden.", flush=True)
    print(
        "Check order: "
        + {
            "in_order": "in order",
            "random": "random",
            "short_first": "short first",
            "long_first": "long first",
        }[args.order],
        flush=True,
    )
    print("Service priority: " + ", ".join(enabled), flush=True)

    checked = 0
    found = 0
    instagram_ignored_warned = False
    pause_path = Path(args.pause_file) if args.pause_file else None
    found_buffer: list[str] = []
    next_index = 0
    pending = set()
    paused_logged = False

    def flush_found_buffer() -> None:
        nonlocal found_buffer
        if not found_out or not found_buffer:
            return
        try:
            found_out.parent.mkdir(parents=True, exist_ok=True)
            with found_out.open("a", encoding="utf-8", newline="") as f:
                for username in found_buffer:
                    f.write(f"@{username}\n")
            found_buffer = []
        except Exception as e:
            print(f"[export error] {type(e).__name__}: {e}", flush=True)

    def handle_row(row: dict):
        nonlocal checked, found, instagram_ignored_warned, found_buffer
        checked += 1

        if not instagram_ignored_warned and "instagram" in row.get("skipped_neutral", []):
            print("[!] Instagram returned a generic anti-bot page and was ignored for some usernames.", flush=True)
            instagram_ignored_warned = True

        def export_found() -> None:
            nonlocal found_buffer
            if not found_out:
                return
            found_buffer.append(row["username"])
            if len(found_buffer) >= 3:
                flush_found_buffer()

        if row["result"] == "busy":
            if args.hide_busy:
                print(f"[b] @{row['username']} -> BUSY | {SERVICE_LABELS[row['service']]} - {display_url(row['url'])}", flush=True)
            else:
                print(f"[-] @{row['username']} -> BUSY | {SERVICE_LABELS[row['service']]} - {display_url(row['url'])}", flush=True)
            return
        if row["result"] == "free":
            found += 1
            export_found()
            confirmed = ", ".join(SERVICE_LABELS[s] for s in row["services"])
            print(f"[+] @{row['username']} -> FREE ! {confirmed}", flush=True)
            return
        print(
            f"[?] @{row['username']} -> UNKNOWN | {SERVICE_LABELS[row['service']]} - {display_url(row['url'])} ({row['status']}: {row['note']})",
            flush=True,
        )

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        while next_index < len(words) or pending:
            if stop_path and stop_path.exists():
                flush_found_buffer()
                print("Stop requested. Finishing current requests and exiting.", flush=True)
                break
            while next_index < len(words) and len(pending) < max(1, args.workers):
                if stop_path and stop_path.exists():
                    flush_found_buffer()
                    print("Stop requested. Finishing current requests and exiting.", flush=True)
                    break
                if pause_path and pause_path.exists():
                    flush_found_buffer()
                    if not paused_logged:
                        print("Paused. Waiting for continue...", flush=True)
                        paused_logged = True
                    time.sleep(0.25)
                    continue
                if paused_logged:
                    print("Continued.", flush=True)
                    paused_logged = False
                w = words[next_index]
                next_index += 1
                pending.add(pool.submit(check_one, w, services, args.timeout, args.delay))

            if not pending:
                continue
            done, pending = wait(pending, timeout=0.25, return_when=FIRST_COMPLETED)
            for fut in done:
                handle_row(fut.result())
            if stop_path and stop_path.exists():
                break

    flush_found_buffer()
    print(f"Done. Checked: {checked}. Found: {found}.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
