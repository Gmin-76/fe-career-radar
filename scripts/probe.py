"""채용 시스템 엔드포인트 탐색용 일회성 스크립트 (3차)."""
import json, re, time, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9"}

def req(url, data=None, extra=None):
    h = dict(UA); h.update(extra or {})
    if data is not None:
        h["Content-Type"] = "application/json"; data = json.dumps(data).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=20) as f:
        return f.status, f.read().decode("utf-8", "replace")

def show(label, url, data=None, n=300, extra=None):
    try:
        s, b = req(url, data, extra); print(label, s, url, len(b), b[:n].replace("\n", " ")); return b
    except Exception as e:
        print(label, "FAIL", url, e); return ""

for site in ["TKL_Career", "TKL_Careers", "TEK_Career", "TKR_Career", "TELK_Career", "TEL_Korea"]:
    show("TELWD", f"https://tel.wd3.myworkdayjobs.com/wday/cxs/tel/{site}/jobs", {"limit": 3, "offset": 0, "searchText": "", "appliedFacets": {}}, 250)

a = show("ASMLPAGE", "https://www.asml.com/en/careers/find-your-job", n=0)
print("ASML hints", sorted(set(re.findall(r"(?:data-[a-z-]*(?:api|endpoint|url|src)[a-z-]*=\"[^\"]{4,120}\"|/api/[A-Za-z0-9/_.-]{3,80}|[a-z0-9.-]+\.(?:algolia|algolianet)\.[a-z]+|[a-z]*vacanc[a-z]*)", a)))[:25])

k = show("ADVKR", "https://www.advantest.com/career-kr/", n=0)
print("ADV KR hints", sorted(set(re.findall(r"https?://[^\"' >]*(?:myworkdayjobs|successfactors|smartrecruiters|greenhouse|lever\.co|eightfold|icims|taleo|avature|jobs|recruit|saramin|jobkorea|incruit)[^\"' >]*", k)))[:20])
c = show("ADVCX", "https://www.advantest.com/careers/", n=0)
print("ADV cx", sorted(set(re.findall(r"https?://[^\"' >]*advantestcareers[^\"' >]*", c)))[:10])

show("NASDAQ", "https://api.nasdaq.com/api/quote/ASML/info?assetclass=stocks", n=300, extra={"Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"})
show("NASDAQH", "https://api.nasdaq.com/api/quote/ASML/chart?assetclass=stocks", n=200, extra={"Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"})
for i in range(2):
    show("YAHOO", "https://query2.finance.yahoo.com/v8/finance/chart/8035.T?range=1y&interval=1wk", n=200); time.sleep(3)
show("GOOGFIN", "https://www.google.com/finance/quote/8035:TYO", n=0)
show("KABUTAN", "https://kabutan.jp/stock/kabuka?code=8035", n=0)
