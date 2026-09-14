#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_coords.py — 用教育局官方數據修正學校座標

用法：
    python3 fix_coords.py                    # 修正所有 *-aided.html 及 dss-private-schools.html
    python3 fix_coords.py tsuen-wan-aided.html kwai-tsing-aided.html
    python3 fix_coords.py --dry-run          # 只報告，不改檔案

做甚麼：
  1. 下載教育局官方「學校位置及資料」CSV（每月更新）
  2. 把 度分秒(D-M-S) 座標轉成小數
  3. 按中文校名比對，改寫 HTML 內 S[] 陣列的 lat / lng
  4. 列出未能比對的學校，讓你人手處理

資料來源：
  https://data.gov.hk/tc-data/dataset/hk-edb-schinfo-school-location-and-information
"""

import csv, io, os, re, sys, ssl, urllib.request

CSV_URL = ("http://www.edb.gov.hk/attachment/en/student-parents/sch-info/"
           "sch-search/sch-location-info/SCH_LOC_EDB.csv")
CACHE = "SCH_LOC_EDB.csv"

DRY = "--dry-run" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]


# ─────────────────────────────────────────────── 下載 / 讀取 CSV
def load_rows():
    if os.path.exists(CACHE):
        print(f"• 使用已下載的 {CACHE}")
        raw = open(CACHE, "rb").read()
    else:
        print(f"• 下載教育局資料 …")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req, context=ctx, timeout=120).read()
        open(CACHE, "wb").write(raw)
        print(f"  已儲存 {CACHE}（{len(raw):,} bytes）")

    # EDB 的 CSV 可能是 UTF-8-BOM 或 UTF-16
    for enc in ("utf-8-sig", "utf-16", "utf-16-le", "big5hkscs", "utf-8"):
        try:
            text = raw.decode(enc)
            if "LATITUDE" in text.upper() or "緯度" in text:
                print(f"  編碼：{enc}")
                return list(csv.DictReader(io.StringIO(text)))
        except Exception:
            continue
    sys.exit("✗ 無法解讀 CSV 編碼，請手動開啟檢查")


def dms_to_dec(v):
    """'22-22-19' 或 '22-22-19.5' → 22.372083 ；已是小數則直接回傳"""
    if v is None:
        return None
    v = str(v).strip()
    if not v:
        return None
    parts = re.split(r"[-:\s]+", v)
    try:
        if len(parts) >= 3:
            d, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return round(d + m / 60 + s / 3600, 7)
        return round(float(v), 7)
    except ValueError:
        return None


def pick(row, *names):
    """從 row 取第一個存在的欄位（大小寫/空格不敏感）"""
    norm = {re.sub(r"[^a-z\u4e00-\u9fff]", "", k.lower()): v
            for k, v in row.items() if k}
    for n in names:
        key = re.sub(r"[^a-z\u4e00-\u9fff]", "", n.lower())
        if key in norm and str(norm[key]).strip():
            return str(norm[key]).strip()
    return ""


def normalise(name):
    """統一校名：去空白、全形括號轉半形、去「上午/下午/全日校」後綴"""
    if not name:
        return ""
    n = name.strip()
    n = n.replace("（", "(").replace("）", ")")
    n = re.sub(r"\s+", "", n)
    n = re.sub(r"\((上午|下午|全日|上午校|下午校|全日校)\)$", "", n)
    return n


# ─────────────────────────────────────────────── 建立官方座標索引
def build_index(rows):
    idx = {}
    kept = 0
    for r in rows:
        level = pick(r, "LEVEL", "學校類別", "level-en", "levelen")
        # 只要小學（排除幼稚園、中學）
        if "PRIMARY" not in level.upper() and "小學" not in level:
            continue
        zh = pick(r, "中文名稱", "CHINESE NAME", "namezh", "name-zh")
        en = pick(r, "ENGLISH NAME", "英文名稱", "nameen", "name-en")
        lat = dms_to_dec(pick(r, "LATITUDE", "緯度"))
        lng = dms_to_dec(pick(r, "LONGITUDE", "經度"))
        if lat is None or lng is None:
            continue
        # 香港範圍粗檢
        if not (22.1 < lat < 22.6 and 113.8 < lng < 114.5):
            continue
        kept += 1
        for key in (normalise(zh), normalise(en).lower()):
            if key and key not in idx:
                idx[key] = (lat, lng, zh or en)
    print(f"• 官方小學座標：{kept} 筆，索引 {len(idx)} 個名稱")
    return idx


# ─────────────────────────────────────────────── 修補 HTML
SCHOOL_RE = re.compile(r"\{id:'([^']+)'.*?\}", re.S)


def fix_file(path, idx):
    html = open(path, encoding="utf-8").read()
    m = re.search(r"const S = \[.*?\n\];", html, re.S)
    if not m:
        print(f"  ✗ {path}: 找不到 const S = [...]")
        return
    block = m.group()

    stats = {"fixed": 0, "same": 0, "miss": 0}
    misses = []
    new_block = block

    for entry in SCHOOL_RE.finditer(block):
        chunk = entry.group()
        sid = entry.group(1)
        mn = re.search(r"name:'([^']*)'", chunk)
        me = re.search(r'eng:"([^"]*)"', chunk) or re.search(r"eng:'([^']*)'", chunk)
        mlat = re.search(r"lat:([\d.]+)", chunk)
        mlng = re.search(r"lng:([\d.]+)", chunk)
        if not (mn and mlat and mlng):
            continue

        zh, en = mn.group(1), (me.group(1) if me else "")
        hit = idx.get(normalise(zh)) or idx.get(normalise(en).lower())
        if not hit:
            stats["miss"] += 1
            misses.append(f"{sid}  {zh}")
            continue

        lat, lng, _ = hit
        old_lat, old_lng = float(mlat.group(1)), float(mlng.group(1))
        # 差距多少米（粗算：1度緯≈111km）
        dist = ((lat - old_lat) ** 2 + (lng - old_lng) ** 2) ** 0.5 * 111000

        if dist < 30:
            stats["same"] += 1
            continue

        fixed = chunk.replace(f"lat:{mlat.group(1)}", f"lat:{lat}") \
                     .replace(f"lng:{mlng.group(1)}", f"lng:{lng}")
        new_block = new_block.replace(chunk, fixed)
        stats["fixed"] += 1
        print(f"    ↻ {zh}  偏差 {dist:,.0f}m → 已修正")

    if not DRY and stats["fixed"]:
        open(path, "w", encoding="utf-8").write(html.replace(block, new_block))

    tag = "（dry-run，未寫入）" if DRY else ""
    print(f"  {path}: 修正 {stats['fixed']} · 本來正確 {stats['same']} · "
          f"未比對 {stats['miss']} {tag}")
    if misses:
        print("    未能比對（請人手查 EDB 校名是否一致）：")
        for x in misses:
            print("      -", x)


# ─────────────────────────────────────────────── main
def main():
    idx = build_index(load_rows())
    files = args or sorted(f for f in os.listdir(".")
                           if f.endswith("-aided.html")
                           or f == "dss-private-schools.html")
    if not files:
        sys.exit("✗ 找不到任何 *-aided.html")
    print(f"\n• 處理 {len(files)} 個檔案\n")
    for f in files:
        fix_file(f, idx)
    print("\n完成。建議用 git diff 檢查改動後再 push。")


if __name__ == "__main__":
    main()
