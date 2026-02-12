#!/usr/bin/env python3
"""claude-top: TUI system & Claude Code usage monitor."""
import json, os, sys, shutil, subprocess, re, time
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

STATS = Path.home() / ".claude" / "stats-cache.json"
HISTORY = Path.home() / ".claude" / "history.jsonl"

# ANSI - blue window theme
RST  = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
BG   = "\033[48;5;17m"
FG   = "\033[97m"
YEL  = "\033[93m"
CYN  = "\033[96m"
GRN  = "\033[92m"
RED  = "\033[91m"
MAG  = "\033[95m"
WBLU = "\033[94m"

TL = "╔"; TR = "╗"; BL = "╚"; BR = "╝"
HZ = "═"; VT = "║"; MD = "╠"; MR = "╣"

def load_stats():
    with open(STATS) as f:
        return json.load(f)

def load_recent_messages():
    """Parse history.jsonl for recent message timestamps."""
    if not HISTORY.exists():
        return []
    timestamps = []
    with open(HISTORY) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if "timestamp" in d:
                    timestamps.append(d["timestamp"] / 1000)  # ms -> sec
            except:
                continue
    return timestamps

def get_system_stats():
    """Get CPU, memory, load from macOS."""
    info = {"cpu_user": 0, "cpu_sys": 0, "cpu_idle": 100,
            "mem_used": 0, "mem_total": 0, "load": [0, 0, 0]}
    try:
        out = subprocess.check_output(["top", "-l", "1", "-n", "0"],
                                       stderr=subprocess.DEVNULL, timeout=5).decode()
        for line in out.splitlines():
            if "CPU usage" in line:
                m = re.findall(r'([\d.]+)%', line)
                if len(m) >= 3:
                    info["cpu_user"] = float(m[0])
                    info["cpu_sys"] = float(m[1])
                    info["cpu_idle"] = float(m[2])
            if "PhysMem" in line:
                mu = re.search(r'(\d+)([MG]) used', line)
                mu2 = re.search(r'(\d+)([MG]) unused', line)
                if mu and mu2:
                    used = int(mu.group(1)) * (1024 if mu.group(2) == 'G' else 1)
                    free = int(mu2.group(1)) * (1024 if mu2.group(2) == 'G' else 1)
                    info["mem_used"] = used
                    info["mem_total"] = used + free
            if "Load Avg" in line:
                m = re.findall(r'[\d.]+', line)
                info["load"] = [float(x) for x in m[:3]]
    except:
        pass
    return info

# Box drawing helpers
def box_top(w):
    return f"{BG}{WBLU}{TL}{HZ * (w - 2)}{TR}{RST}"
def box_bot(w):
    return f"{BG}{WBLU}{BL}{HZ * (w - 2)}{BR}{RST}"
def box_sep(w):
    return f"{BG}{WBLU}{MD}{HZ * (w - 2)}{MR}{RST}"
def box_line(text, w):
    vis = len(re.sub(r'\033\[[^m]*m', '', text))
    pad = max(w - 4 - vis, 0)
    return f"{BG}{WBLU}{VT}{RST}{BG} {text}{' ' * pad} {WBLU}{VT}{RST}"

def hp_bar(val, mx, width, warn_low=False):
    """Bar that turns red when HIGH usage (warn_low=False) or LOW (warn_low=True)."""
    if mx == 0:
        return f"{DIM}{'·' * width}{RST}"
    ratio = min(val / mx, 1.0)
    filled = int(ratio * width)
    if warn_low:
        c = GRN if ratio > 0.5 else (YEL if ratio > 0.2 else RED)
    else:
        c = GRN if ratio < 0.5 else (YEL if ratio < 0.8 else RED)
    return f"{c}{'█' * filled}{DIM}{'░' * (width - filled)}{RST}"

def fmt_num(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def fmt_mem(mb):
    if mb >= 1024:
        return f"{mb/1024:.1f}G"
    return f"{mb}M"

def calc_level(total_msg):
    lv = 1
    needed = 100
    remaining = total_msg
    while remaining >= needed:
        remaining -= needed
        lv += 1
        needed = int(needed * 1.4)
    return lv, remaining, needed

def draw(data, timestamps, sys_info, oneshot=False):
    cols, rows = shutil.get_terminal_size((80, 24))
    w = min(cols, 80)
    daily = data.get("dailyActivity", [])
    tokens = data.get("dailyModelTokens", [])
    model_usage = data.get("modelUsage", {})
    total_msg = data.get("totalMessages", 0)
    total_sess = data.get("totalSessions", 0)

    lines = []
    def add(s=""):
        lines.append(s)

    now_ts = time.time()
    now = datetime.now()
    bw = max(w - 38, 10)

    # ═══ Title ═══
    add(box_top(w))
    ts = now.strftime("%H:%M:%S")
    add(box_line(f"{BOLD}{FG}Claude Code の ぼうけんのしょ{RST}{BG}            {DIM}{ts}{RST}", w))

    # ═══ System Monitor ═══
    add(box_sep(w))
    cpu_used = sys_info["cpu_user"] + sys_info["cpu_sys"]
    add(box_line(f"{FG}C P U{RST}{BG}  {hp_bar(cpu_used, 100, bw)} "
                 f"{YEL}{cpu_used:5.1f}%{RST}{BG} {DIM}usr:{sys_info['cpu_user']:.0f} sys:{sys_info['cpu_sys']:.0f}{RST}", w))

    mem_pct = (sys_info["mem_used"] / sys_info["mem_total"] * 100) if sys_info["mem_total"] > 0 else 0
    add(box_line(f"{CYN}M E M{RST}{BG}  {hp_bar(mem_pct, 100, bw)} "
                 f"{YEL}{mem_pct:5.1f}%{RST}{BG} {DIM}{fmt_mem(sys_info['mem_used'])}/{fmt_mem(sys_info['mem_total'])}{RST}", w))

    ld = sys_info["load"]
    add(box_line(f"{MAG}LOAD {RST}{BG}  {DIM}1m{RST}{BG} {YEL}{ld[0]:.2f}{RST}{BG}  "
                 f"{DIM}5m{RST}{BG} {YEL}{ld[1]:.2f}{RST}{BG}  "
                 f"{DIM}15m{RST}{BG} {YEL}{ld[2]:.2f}{RST}", w))

    # ═══ Rate Limit Monitor (THE MAIN EVENT) ═══
    add(box_sep(w))
    add(box_line(f"{BOLD}{YEL}▸ まほうりょく のこり  {DIM}（レートリミット）{RST}", w))
    add(box_sep(w))

    # Count messages in various time windows
    msg_1h = sum(1 for t in timestamps if now_ts - t < 3600)
    msg_3h = sum(1 for t in timestamps if now_ts - t < 10800)
    msg_5h = sum(1 for t in timestamps if now_ts - t < 18000)
    today_start = now.replace(hour=0, minute=0, second=0).timestamp()
    msg_today = sum(1 for t in timestamps if t >= today_start)

    # Show hourly breakdown for recent hours
    recent_hours = []
    for h_ago in range(5, -1, -1):
        start = now_ts - (h_ago + 1) * 3600
        end = now_ts - h_ago * 3600
        count = sum(1 for t in timestamps if start <= t < end)
        hour_label = (now - timedelta(hours=h_ago)).strftime("%H時")
        recent_hours.append((hour_label, count))

    mx_hour = max((c for _, c in recent_hours), default=1)
    hbw = max(w - 30, 8)

    for label, count in recent_hours:
        is_current = label == now.strftime("%H時")
        marker = f"{RED}▶{RST}{BG}" if is_current else " "
        add(box_line(f"{marker}{FG}{label}{RST}{BG} {hp_bar(count, mx_hour, hbw)} "
                     f"{YEL}{count:>4}{RST}", w))

    add(box_sep(w))

    # Summary
    add(box_line(f" {FG}1じかん{RST}{BG} {YEL}{msg_1h:>5}{RST}{BG}  "
                 f"{FG}3じかん{RST}{BG} {YEL}{msg_3h:>5}{RST}{BG}  "
                 f"{FG}5じかん{RST}{BG} {YEL}{msg_5h:>5}{RST}{BG}  "
                 f"{FG}きょう{RST}{BG} {YEL}{msg_today:>5}{RST}", w))

    # Warning message based on usage intensity
    if msg_1h > 80:
        warn = f"{RED}{BOLD}⚠ まほうりょくが のこりわずか！ しばらくやすもう！{RST}"
    elif msg_1h > 40:
        warn = f"{YEL}△ けっこう つかっている… ペースにちゅうい{RST}"
    elif msg_1h > 0:
        warn = f"{GRN}○ まだまだ よゆうが ある！{RST}"
    else:
        warn = f"{DIM}  ── まだ たたかいは はじまっていない ──{RST}"
    add(box_line(warn, w))

    # ═══ Party (Models) - compact ═══
    add(box_sep(w))
    lv, exp_cur, exp_next = calc_level(total_msg)
    add(box_line(f"{BOLD}{YEL}▸ なかまたち{RST}{BG}    "
                 f"{FG}Lv{RST}{BG} {YEL}{lv}{RST}{BG}  "
                 f"{FG}EXP{RST}{BG} {YEL}{exp_cur}{RST}{BG}/{DIM}{exp_next}{RST}{BG}  "
                 f"{FG}そうメッセージ{RST}{BG} {YEL}{fmt_num(total_msg)}{RST}", w))
    add(box_sep(w))
    model_names = {
        "claude-sonnet-4-5-20250929": ("ソネット  ", "そうりょ", CYN),
        "claude-opus-4-5-20251101":   ("オーパス45", "せんし ", MAG),
        "claude-opus-4-6":            ("オーパス46", "ゆうしゃ", GRN),
    }
    total_out = sum(m.get("outputTokens", 0) for m in model_usage.values())
    mbw = max(w - 44, 8)
    for mid, info in model_usage.items():
        name, job, color = model_names.get(mid, (mid[:9], "?? ", FG))
        out = info.get("outputTokens", 0)
        add(box_line(f"{color}{name}{RST}{BG}{DIM}({job}){RST}{BG} "
                     f"{hp_bar(out, total_out, mbw)} "
                     f"{YEL}{fmt_num(out):>6}{RST}", w))

    # ═══ Footer ═══
    add(box_sep(w))
    if not oneshot:
        add(box_line(f"{DIM}q:にげる  r:リロード  2びょうごとに こうしん{RST}", w))
    else:
        add(box_line(f"{DIM}python3 claude_top.py でリアルタイムかんし{RST}", w))
    add(box_bot(w))

    # Render
    if not oneshot:
        sys.stdout.write("\033[H\033[J")
    sys.stdout.write("\n".join(lines[:rows]) + "\n")
    sys.stdout.flush()

def main():
    if not STATS.exists():
        print(f"Error: {STATS} not found")
        sys.exit(1)

    oneshot = "--once" in sys.argv

    if oneshot:
        data = load_stats()
        timestamps = load_recent_messages()
        sys_info = get_system_stats()
        draw(data, timestamps, sys_info, oneshot=True)
        return

    os.system("stty -echo -icanon min 1 time 0 2>/dev/null")
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        data = load_stats()
        timestamps = load_recent_messages()
        sys_info = get_system_stats()
        draw(data, timestamps, sys_info)
        import select
        last_full_reload = time.time()
        while True:
            rlist, _, _ = select.select([sys.stdin], [], [], 2.0)
            if rlist:
                ch = sys.stdin.read(1)
                if ch in ('q', 'Q', '\x03'):
                    break
                elif ch in ('r', 'R'):
                    data = load_stats()
                    timestamps = load_recent_messages()
            # Refresh system stats every tick, full reload every 30s
            sys_info = get_system_stats()
            if time.time() - last_full_reload > 30:
                data = load_stats()
                timestamps = load_recent_messages()
                last_full_reload = time.time()
            draw(data, timestamps, sys_info)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        os.system("stty sane 2>/dev/null")

if __name__ == "__main__":
    main()
