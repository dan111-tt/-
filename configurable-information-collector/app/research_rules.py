from __future__ import annotations
import re
from datetime import date, timedelta
from urllib.parse import urlparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH_TERMS = json.loads((ROOT / "config/search_terms.json").read_text(encoding="utf-8"))
COUNTRIES = {
    "cote d'ivoire":"科特迪瓦", "côte d'ivoire":"科特迪瓦", "ivory coast":"科特迪瓦", "科特迪瓦":"科特迪瓦",
    "south africa":"南非", "南非":"南非", "zambia":"赞比亚", "赞比亚":"赞比亚", "hong kong":"香港", "香港":"香港",
    "macao":"澳门", "macau":"澳门", "澳门":"澳门", "singapore":"新加坡", "新加坡":"新加坡",
    "indonesia":"印度尼西亚", "印尼":"印度尼西亚", "印度尼西亚":"印度尼西亚", "malaysia":"马来西亚", "马来西亚":"马来西亚",
    "philippines":"菲律宾", "菲律宾":"菲律宾", "thailand":"泰国", "泰国":"泰国", "myanmar":"缅甸", "缅甸":"缅甸",
    "saudi arabia":"沙特阿拉伯", "沙特":"沙特阿拉伯", "沙特阿拉伯":"沙特阿拉伯", "united arab emirates":"阿联酋",
    "uae":"阿联酋", "阿联酋":"阿联酋", "nigeria":"尼日利亚", "尼日利亚":"尼日利亚", "dr congo":"刚果（金）", "drc":"刚果（金）",
    "democratic republic of the congo":"刚果（金）", "刚果（金）":"刚果（金）", "brazil":"巴西", "brasil":"巴西", "巴西":"巴西",
    "russia":"俄罗斯", "russian federation":"俄罗斯", "россия":"俄罗斯", "俄罗斯":"俄罗斯"
}
TOPIC_ALIASES = {
    "建设工程与基础设施": ["建设工程", "工程建设", "工程行业", "基础设施", "基建", "construction", "infrastructure"],
    "通信与数字基础设施": ["通信", "通信工程", "电信", "数字基础设施", "telecom", "telecommunications"],
    "招投标与政府采购": ["招投标", "招标", "投标", "政府采购", "procurement", "tender"],
    "外国投资与公司经营": ["海外投资", "境外投资", "外国投资", "外资", "投资", "investment"],
    "劳动与用工": ["劳动", "用工", "劳工", "就业", "劳动用工", "employment", "labor", "labour"],
    "财税与金融": ["财税", "税务", "税收", "金融", "财务", "tax", "finance"],
    "环保与廉洁合规": ["环保", "环境", "廉洁", "反腐", "合规", "environment", "compliance"]
}

def country_name(value: str) -> str:
    return COUNTRIES.get(value.strip().lower(), value.strip())

MONTHS = {
    "january":1,"jan":1,"february":2,"feb":2,"march":3,"mar":3,"april":4,"apr":4,"may":5,"june":6,"jun":6,"july":7,"jul":7,"august":8,"aug":8,"september":9,"sep":9,"sept":9,"october":10,"oct":10,"november":11,"nov":11,"december":12,"dec":12,
    "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12,
    "มกราคม":1,"กุมภาพันธ์":2,"มีนาคม":3,"เมษายน":4,"พฤษภาคม":5,"มิถุนายน":6,"กรกฎาคม":7,"สิงหาคม":8,"กันยายน":9,"ตุลาคม":10,"พฤศจิกายน":11,"ธันวาคม":12
}

def parse_date_value(value: str):
    value = (value or "").strip()
    m = re.search(r"(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})日?", value)
    if m:
        try: return date(int(m[1]),int(m[2]),int(m[3]))
        except ValueError: return None
    m = re.search(r"(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(20\d{2})", value)
    if m:
        month = MONTHS.get(m[2].lower())
        try: return date(int(m[3]),month,int(m[1])) if month else None
        except ValueError: return None
    m = re.search(r"([A-Za-zÀ-ÿ]+)\s+(\d{1,2}),?\s+(20\d{2})", value)
    if m:
        month = MONTHS.get(m[1].lower())
        try: return date(int(m[3]),month,int(m[2])) if month else None
        except ValueError: return None
    return None

def extract_published_date(meta_value: str, structured_date: str, visible_text: str):
    parsed_meta=parse_date_value(meta_value)
    parsed_structured=parse_date_value(structured_date)
    if parsed_meta and parsed_structured and parsed_meta != parsed_structured:
        return None, "conflicting metadata dates; verify manually"
    if parsed_meta: return parsed_meta,"article metadata"
    if parsed_structured: return parsed_structured,"structured data"
    # Use visible page text only when it contains exactly one unique calendar date.
    candidates=set()
    for match in re.finditer(r"(?:20\d{2}[-/年.](?:0?[1-9]|1[0-2])[-/月.](?:0?[1-9]|[12]\d|3[01])日?|(?:0?[1-9]|[12]\d|3[01])\s+[A-Za-zÀ-ÿ]+\s+20\d{2}|[A-Za-zÀ-ÿ]+\s+(?:0?[1-9]|[12]\d|3[01]),?\s+20\d{2})", visible_text or ""):
        parsed=parse_date_value(match.group(0))
        if parsed: candidates.add(parsed)
    if len(candidates)==1: return candidates.pop(), "single visible date; verify manually"
    return None, "missing or ambiguous"

def build_queries(countries: list[str], configured: list[dict], topics: list[str], keywords: list[str], start: date, end: date):
    """Build a repeatable broad-recall plan: legal discovery + sector clusters + native terms."""
    grouped={}
    for source in configured: grouped.setdefault(country_name(source["country"]),[]).append(source)
    selected_topics=topics or list(SEARCH_TERMS["topics"].keys())
    topic_terms=[]
    normalized_topics=[]
    for topic in selected_topics:
        matched=[canonical for canonical,aliases in TOPIC_ALIASES.items()
                 if topic==canonical or any(alias.lower() in topic.lower() for alias in aliases)]
        if topic in SEARCH_TERMS["topics"]: matched=[topic]
        normalized_topics.extend(matched)
        if not matched: topic_terms.append(topic)
    # Broad fallback protects recall when user phrasing does not match the controlled vocabulary.
    if not normalized_topics: normalized_topics=list(SEARCH_TERMS["topics"].keys())
    topic_terms.extend(keywords)
    topic_terms=list(dict.fromkeys(topic_terms))
    queries=[]
    # Expand discovery by country; never truncate to the first three user keywords.
    for country in countries:
        aliases=SEARCH_TERMS["countries"].get(country,{"aliases":[country],"native_terms":[]})
        names=aliases.get("aliases",[country])
        hosts=list(dict.fromkeys(s["host"] for s in sorted(grouped.get(country,[]),key=lambda x:0 if x.get("level")=="P0" else 1)))
        namestr=" OR ".join(f'"{x}"' for x in names[:4])
        legal_terms=list(dict.fromkeys(SEARCH_TERMS["legal_signals"][:10]+SEARCH_TERMS.get("legal_by_country",{}).get(country,[])))
        legal=" OR ".join(f'"{x}"' for x in legal_terms)
        queries.append({"country":country,"cluster":"laws_and_gazettes","query":f'({namestr}) ({legal}) after:{(start-timedelta(days=1)).isoformat()} before:{(end+timedelta(days=1)).isoformat()}','domains':hosts})
        # Keep each topic cluster separate so a tax or labor hit is not crowded out by construction terms.
        clusters={
            "construction_telecom_procurement":["建设工程与基础设施","通信与数字基础设施","招投标与政府采购"],
            "investment_labor_tax_compliance":["外国投资与公司经营","劳动与用工","财税与金融","环保与廉洁合规"]
        }
        native=aliases.get("native_terms",[])
        for cluster, topic_names in clusters.items():
            terms=[]
            for name in topic_names:
                if name in normalized_topics:
                    terms.extend(SEARCH_TERMS["topics"][name])
            terms.extend(topic_terms)
            terms=list(dict.fromkeys(terms))[:14]
            local=" OR ".join(f'"{x}"' for x in native[:10])
            terms_q=" OR ".join(f'"{x}"' for x in terms)
            q=f'({namestr}) ({terms_q}) after:{(start-timedelta(days=1)).isoformat()} before:{(end+timedelta(days=1)).isoformat()}'
            if local: q+=f' ({local})'
            queries.append({"country":country,"cluster":cluster,"query":q,"domains":hosts})
    return queries

def build_general_queries(regions: list[str], industries: list[str], scope: list[str], keywords: list[str], start: date, end: date, domains: list[str] | None = None):
    """Create discovery queries from the task's own inputs; no sector/country defaults."""
    date_filter=f'after:{(start-timedelta(days=1)).isoformat()} before:{(end+timedelta(days=1)).isoformat()}'
    quote=lambda values:" OR ".join(f'"{v.strip()}"' for v in values if v.strip())
    industry_q=quote(industries)
    scope_q=quote(scope)
    keyword_q=quote(keywords)
    queries=[]
    for region in regions:
        region_q=f'"{region.strip()}"'
        clusters=[("industry_scope",[industry_q,scope_q,keyword_q]),
                  ("industry",[industry_q,keyword_q]),
                  ("scope",[scope_q,keyword_q])]
        for cluster,parts in clusters:
            terms=" ".join(f'({part})' for part in parts if part)
            queries.append({"region":region,"cluster":cluster,"query":f'{region_q} {terms} {date_filter}'.strip(),"domains":domains or []})
    return queries

def draft_signal(text: str):
    return bool(re.search(r"征求意见稿|草案|\bdraft\b|\bproposed\b|projet de loi|projeto de lei|ร่าง(?:กฎหมาย|พระราชบัญญัติ)", text or "", re.I))

def source_for_url(url: str, configured: list[dict]):
    host=(urlparse(url).hostname or "").lower()
    return next((s for s in sorted(configured,key=lambda x:len(x["host"]),reverse=True) if host==s["host"] or host.endswith("."+s["host"])),None)

