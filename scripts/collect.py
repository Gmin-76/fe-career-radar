"""매일 한 번 실행: 회사 채용페이지(한국 공고), 모회사 주가, 뉴스를 모아 site/data/*.json 으로 저장.

외부 의존성 없이 표준 라이브러리만 씁니다. 한 소스가 실패해도 이전 데이터를 유지하고 상태만 기록합니다.
"""
import datetime as dt
import email.utils
import html
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*", "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}
KST = dt.timezone(dt.timedelta(hours=9))
TODAY = dt.datetime.now(KST).date().isoformat()


def http(url, data=None, extra=None, timeout=25):
    h = dict(UA)
    h.update(extra or {})
    if data is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout) as f:
        return f.read().decode("utf-8", "replace")


def read(name, default):
    try:
        return json.loads((DATA / f"{name}.json").read_text("utf-8"))
    except Exception:
        return default


def write(name, obj):
    (DATA / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1), "utf-8")


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


# ---------- 채용 ----------

def workday(host, tenant, site, company, search="", korea_only=True, detail_limit=25):
    base = f"https://{host}.myworkdayjobs.com"
    out, offset = [], 0
    while offset < 400:
        j = json.loads(http(f"{base}/wday/cxs/{tenant}/{site}/jobs",
                            {"limit": 20, "offset": offset, "searchText": search, "appliedFacets": {}}))
        posts = j.get("jobPostings", [])
        for p in posts:
            loc = p.get("locationsText", "")
            if korea_only and not re.search(r"korea|kr-|seoul|hwaseong|pyeongtaek|icheon|cheonan|yongin|giheung|osan|dongtan|suwon|asan|cheongju|gumi|bundang|pangyo|한국", (loc + " " + p.get("title", "")).lower()):
                continue
            out.append({"company": company, "title": p.get("title", ""), "location": loc,
                        "url": base + "/" + site + p.get("externalPath", ""), "path": p.get("externalPath", ""),
                        "posted": p.get("postedOn", ""), "source": "회사 채용페이지"})
        offset += 20
        if offset >= j.get("total", 0) or not posts:
            break
        time.sleep(0.5)
    for job in out[:detail_limit]:
        try:
            d = json.loads(http(f"{base}/wday/cxs/{tenant}/{site}{job['path']}"))
            job["text"] = strip_tags(d.get("jobPostingInfo", {}).get("jobDescription", ""))[:4000]
        except Exception:
            pass
        time.sleep(0.4)
    return out


def eightfold(base, domain, company, location="Korea"):
    out, start = [], 0
    while start < 300:
        q = urllib.parse.urlencode({"domain": domain, "query": "", "location": location, "start": start})
        j = json.loads(http(f"{base}/api/pcsx/search?{q}"))
        pos = j.get("data", {}).get("positions", [])
        for p in pos:
            if "KR" not in (p.get("standardizedLocations") or []) and not any("KR" in l for l in p.get("locations", [])):
                continue
            ts = p.get("postedTs")
            out.append({"company": company, "title": p.get("name", ""), "location": ", ".join(p.get("locations", [])),
                        "url": f"{base}/careers/job/{p.get('id')}" if not p.get("positionUrl") else base + p["positionUrl"],
                        "posted": dt.datetime.fromtimestamp(ts, KST).date().isoformat() if ts else "",
                        "source": "회사 채용페이지", "text": p.get("department", "")})
        start += len(pos)
        if not pos or start >= j.get("data", {}).get("count", 0):
            break
        time.sleep(0.5)
    return out


SOURCES = {
    "amat": lambda: workday("amat.wd1", "amat", "External", "amat", search="Korea"),
    "lam": lambda: eightfold("https://careers.lamresearch.com", "lamresearch.com", "lam"),
    # TEL(한국 법인 채용 사이트 미공개), ASML(자체 검색 페이지), Advantest(ADP)는 공개 목록 API가 없어 링크로 연결합니다.
}


def norm(s):
    return re.sub(r"[^0-9a-z가-힣]", "", s.lower())


def collect_jobs():
    prev = read("jobs", {"jobs": []})
    first_seen = {j["id"]: j.get("firstSeen", TODAY) for j in prev.get("jobs", [])}
    prev_by_co = {}
    for j in prev.get("jobs", []):
        prev_by_co.setdefault(j["company"], []).append(j)
    jobs, status = [], {}
    companies = [c["id"] for c in read("companies", {"companies": []})["companies"]]
    for cid in companies:
        fn = SOURCES.get(cid)
        if not fn:
            status[cid] = {"ok": False, "msg": "자동 수집 경로 없음, 채용페이지 링크로 연결"}
            continue
        try:
            got = fn()
            jobs += got
            status[cid] = {"ok": True, "count": len(got), "msg": ""}
        except Exception as e:  # 실패하면 어제 데이터를 유지
            jobs += prev_by_co.get(cid, [])
            status[cid] = {"ok": False, "msg": f"수집 실패, 이전 데이터 유지: {e}"[:200]}
    merged = {}
    for j in jobs:
        key = norm(j["company"] + j["title"] + j["location"].split(",")[0])
        if key in merged:
            m = merged[key]
            m["sources"] = sorted(set(m["sources"]) | {j.get("source", "")} | set(j.get("sources", [])))
            continue
        j = dict(j)
        j.pop("path", None)
        j["id"] = key
        j["sources"] = sorted({j.pop("source", None)} - {None} | set(j.get("sources", [])))
        j["firstSeen"] = first_seen.get(key, TODAY)
        merged[key] = j
    write("jobs", {"updated": dt.datetime.now(dt.timezone.utc).isoformat(), "jobs": sorted(merged.values(), key=lambda x: (x["firstSeen"], x["company"]), reverse=True), "status": status})
    return status


# ---------- 뉴스 ----------

def collect_news():
    prev = read("news", {"items": {}})
    items = dict(prev.get("items", {}))
    for c in read("companies", {"companies": []})["companies"]:
        q = urllib.parse.quote(f'"{c["newsQuery"]}" when:14d')
        try:
            root = ET.fromstring(http(f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"))
            arr = []
            for it in root.iter("item"):
                title = it.findtext("title", "")
                src = it.findtext("source", "")
                if src and title.endswith(" - " + src):
                    title = title[: -len(src) - 3]
                pub = it.findtext("pubDate", "")
                try:
                    pub = email.utils.parsedate_to_datetime(pub).astimezone(KST).isoformat()
                except Exception:
                    pass
                arr.append({"title": title, "link": it.findtext("link", ""), "source": src, "date": pub})
            items[c["id"]] = sorted(arr, key=lambda x: x["date"], reverse=True)[:8]
        except Exception as e:
            print("news fail", c["id"], e)
        time.sleep(1)
    write("news", {"updated": dt.datetime.now(dt.timezone.utc).isoformat(), "items": items})


# ---------- 주가 ----------

def stock_quote(stock):
    """야후 파이낸스 공개 차트 데이터(주간 종가 1년)."""
    last_err = None
    for attempt in range(3):
        try:
            j = json.loads(http(f"https://query2.finance.yahoo.com/v8/finance/chart/{stock['yahoo']}?range=1y&interval=1wk"))
            r = j["chart"]["result"][0]
            m = r["meta"]
            closes = [c for c in r["indicators"]["quote"][0]["close"] if c is not None]
            price = m.get("regularMarketPrice") or closes[-1]
            prev = m.get("previousClose") or m.get("chartPreviousClose")
            d1 = json.loads(http(f"https://query2.finance.yahoo.com/v8/finance/chart/{stock['yahoo']}?range=5d&interval=1d"))
            dc = [c for c in d1["chart"]["result"][0]["indicators"]["quote"][0]["close"] if c is not None]
            if len(dc) >= 2:
                prev = dc[-2]
            return {"price": round(price, 2), "currency": m.get("currency", stock["currency"]),
                    "date": dt.datetime.fromtimestamp(m["regularMarketTime"], KST).date().isoformat(),
                    "chg1d": round((price / prev - 1) * 100, 2) if prev else None,
                    "chg1y": round((price / closes[0] - 1) * 100, 1) if closes else None,
                    "history": [round(c, 2) for c in closes], "source": "Yahoo Finance"}
        except Exception as e:
            last_err = e
            time.sleep(5 * (attempt + 1))
    raise last_err


def collect_stocks():
    prev = read("stocks", {"items": {}})
    items = dict(prev.get("items", {}))
    for c in read("companies", {"companies": []})["companies"]:
        try:
            items[c["id"]] = stock_quote(c["stock"])
        except Exception as e:
            print("stock fail", c["id"], e)
        time.sleep(2)
    write("stocks", {"updated": dt.datetime.now(dt.timezone.utc).isoformat(), "items": items})


if __name__ == "__main__":
    print("jobs", collect_jobs())
    collect_news()
    collect_stocks()
