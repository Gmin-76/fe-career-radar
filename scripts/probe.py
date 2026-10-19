"""채용 시스템 엔드포인트 탐색용 일회성 스크립트 (2차)."""
import json, re, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept": "application/json, text/html, */*"}

def req(url, data=None):
    h = dict(UA)
    if data is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    r = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(r, timeout=20) as f:
        return f.status, f.read().decode("utf-8", "replace")

def show(label, url, data=None, n=300):
    try:
        s, b = req(url, data)
        print(label, s, url, len(b), b[:n].replace("\n", " "))
        return b
    except Exception as e:
        print(label, "FAIL", url, e)
        return ""

b = show("TELPAGE", "https://www.tel.com/careers/", n=0)
print("TEL links", sorted(set(re.findall(r"tel\.wd3\.myworkdayjobs\.com/[A-Za-z0-9_/-]+", b)))[:10])
for site in ["TEL_Careers","External","TEL","TELCareers","tel_careers","TEL_External"]:
    u = f"https://tel.wd3.myworkdayjobs.com/wday/cxs/tel/{site}/jobs"
    show("TELWD", u, {"limit": 3, "offset": 0, "searchText": "Korea", "appliedFacets": {}}, 200)

for u in ["https://careers.lamresearch.com/api/apply/v2/jobs?domain=lamresearch.com&location=Korea&num=5",
          "https://careers.lamresearch.com/api/pcsx/search?domain=lamresearch.com&query=&location=Korea&start=0",
          "https://careers.lamresearch.com/api/apply/v2/jobs?domain=lamresearch.com&query=Korea&num=5"]:
    show("LAM", u, n=400)

a = show("ASMLPAGE", "https://www.asml.com/en/careers/find-your-job", n=0)
print("ASML api hints", sorted(set(re.findall(r"[\"'](/?api/[^\"']{3,80}|https://[^\"']*(?:api|search|jobs)[^\"']{0,80})[\"']", a)))[:20])
for u in ["https://www.advantest.com/en/careers", "https://www.advantest.com/en/about/careers/", "https://www.advantest.com/careers/", "https://www.advantest.com/ko/"]:
    p = show("ADVPAGE", u, n=0)
    if p:
        print("ADV hints", sorted(set(re.findall(r"[a-z0-9.-]*(?:myworkdayjobs|smartrecruiters|successfactors|greenhouse|lever\.co|eightfold|icims|taleo|avature|career)[a-z0-9./_-]*", p)))[:15])

show("STOOQ", "https://stooq.com/q/d/l/?s=asml.us&i=d", n=200)
show("YAHOO", "https://query1.finance.yahoo.com/v8/finance/chart/ASML?range=1y&interval=1d", n=300)
show("YAHOO2", "https://query2.finance.yahoo.com/v8/finance/chart/8035.T?range=5d&interval=1d", n=300)
