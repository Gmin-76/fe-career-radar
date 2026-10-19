"""채용 시스템 엔드포인트 탐색용 일회성 스크립트."""
import json, re, urllib.request

UA = {"User-Agent": "Mozilla/5.0 fe-career-radar (personal job tracker)", "Accept": "application/json, text/html"}

def req(url, data=None):
    h = dict(UA)
    if data is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    r = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(r, timeout=20) as f:
        return f.status, f.read().decode("utf-8", "replace")

WD = [("amat.wd1","amat","External"),("lamresearch.wd1","lamresearch","LAM"),("lamresearch.wd1","lamresearch","External"),
      ("lamresearch.wd5","lamresearch","LAM"),("advantest.wd3","advantest","External"),("advantest.wd1","advantest","External"),
      ("advantest.wd3","advantest","Advantest"),("asml.wd3","asml","ASML"),("tel.wd3","tel","External"),("tel.wd1","tel","TEL")]
for host, tenant, site in WD:
    u = f"https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    try:
        s, b = req(u, {"limit": 3, "offset": 0, "searchText": "Korea", "appliedFacets": {}})
        j = json.loads(b)
        print("WD OK", u, j.get("total"), [p.get("title") for p in j.get("jobPostings", [])][:3])
    except Exception as e:
        print("WD FAIL", u, e)

PAGES = ["https://www.asml.com/en/careers/find-your-job","https://careers.lamresearch.com/","https://www.advantest.com/en/careers/",
         "https://www.tel.com/careers/","https://www.tel.co.kr/","https://www.appliedmaterials.com/us/en/careers.html",
         "https://www.q-net.or.kr/crf005.do?id=crf00503&gSite=Q&gId=","https://stooq.com/q/l/?s=asml.us&f=sd2t2ohlcv&h&e=csv",
         "https://news.google.com/rss/search?q=ASML&hl=ko&gl=KR&ceid=KR:ko"]
for u in PAGES:
    try:
        s, b = req(u)
        hits = sorted(set(re.findall(r"[a-z0-9.-]*(?:myworkdayjobs|smartrecruiters|successfactors|greenhouse|lever\.co|phenompeople|eightfold|icims|taleo|avature|recruitee|jobs\.[a-z]+\.com)[a-z0-9./_-]*", b)))[:12]
        print("PAGE", s, u, len(b), hits, b[:200].replace("\n"," ") if "stooq" in u else "")
    except Exception as e:
        print("PAGE FAIL", u, e)
