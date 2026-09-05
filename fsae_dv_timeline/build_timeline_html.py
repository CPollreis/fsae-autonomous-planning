#!/usr/bin/env python3
"""Build a self-contained comparison page from the research JSON.

Usage:  python3 build_timeline_html.py
Output: fsae_dv_timeline/dv_timeline_comparison.html
"""
import json, glob, os, re, html

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BASE, "results")
OUT = os.path.join(BASE, "dv_timeline_comparison.html")

NA = {"", "n/a", "na", "none", "not applicable", "-"}


def clean(v):
    """Normalize a field value to a display string."""
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, indent=2)
    return str(v).strip()


def is_empty(v):
    s = clean(v).lower().replace("[uncertain]", "").strip()
    return s in NA


def uncertain(v):
    return "[uncertain]" in clean(v).lower()


def months(v):
    """Extract (lo, hi) month count from prose like 'approximately 10-11 months'."""
    s = clean(v)
    if not s:
        return None
    # ranges first: "10-11 months", "12 to 14 months"
    m = re.search(r"(\d{1,3})\s*(?:-|–|to)\s*(\d{1,3})\s*month", s, re.I)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.search(r"(\d{1,3})\s*month", s, re.I)
    if m:
        return (int(m.group(1)), int(m.group(1)))
    return None


def start_year(v):
    m = re.search(r"(19|20)\d{2}", clean(v))
    return int(m.group(0)) if m else None


def entry_year(v):
    m = re.search(r"(19|20)\d{2}", clean(v))
    return int(m.group(0)) if m else None


CATEGORY_KEYS = {"basic_info", "history", "technical_features", "milestone_significance",
                 "competition_ecosystem", "performance_metrics", "lessons_learned",
                 "business_info", "market_positioning"}


def flatten(d):
    """Agents emit either a flat object or one nested by field category. Accept both."""
    if not isinstance(d, dict):
        return d
    out = {}
    for k, v in d.items():
        if k in CATEGORY_KEYS and isinstance(v, dict):
            out.update(v)
        else:
            out.setdefault(k, v)
    # a nested doc may also repeat a key at top level; nested wins only if top level was absent
    for k, v in d.items():
        if k not in CATEGORY_KEYS:
            out[k] = v
    return out


def load():
    teams, subs = [], []
    for f in sorted(glob.glob(os.path.join(RESULTS, "*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"  !! skipping {os.path.basename(f)}: {e}")
            continue
        d = flatten(d)
        d["_file"] = os.path.basename(f)
        if "subsystem" in clean(d.get("item_category")).lower():
            subs.append(d)
        else:
            teams.append(d)
    return teams, subs


def build_track(d):
    """Derive normalized Gantt bands (months from program start)."""
    sy = start_year(d.get("dv_program_start"))
    bands = []
    if sy:
        for e in d.get("year_by_year_timeline") or []:
            if not isinstance(e, dict):
                continue
            y = entry_year(e.get("year"))
            if y is None or y < sy:
                continue
            off = (y - sy) * 12
            bands.append({
                "off": off, "year": clean(e.get("year")),
                "phase": clean(e.get("phase_name")),
                "m": clean(e.get("mechanical_focus")),
                "e": clean(e.get("electrical_focus")),
                "s": clean(e.get("software_focus")),
                "mil": clean(e.get("milestone_achieved")),
                "res": clean(e.get("competition_result")),
                "has_m": not is_empty(e.get("mechanical_focus")),
                "has_e": not is_empty(e.get("electrical_focus")),
                "has_s": not is_empty(e.get("software_focus")),
            })
    run = months(d.get("months_concept_to_first_autonomous_run"))
    comp = months(d.get("months_concept_to_first_competition"))
    score = months(d.get("months_to_first_scoring_run"))
    return {
        "bands": bands,
        "run": run, "comp": comp, "score": score,
        "run_unc": uncertain(d.get("months_concept_to_first_autonomous_run")),
        "comp_unc": uncertain(d.get("months_concept_to_first_competition")),
        "start_year": sy,
    }


UMSAE = {
    "item_name": "UMSAE Driverless (TARGET)",
    "item_category": "Our Team",
    "university": "University of Manitoba",
    "country": "Canada",
    "dv_program_start": "2026-06",
    "is_us": True,
}


def main():
    teams, subs = load()
    for d in teams:
        d["_track"] = build_track(d)

    def sortkey(d):
        c = d["_track"]["comp"]
        return (c[1] if c else 999)
    teams.sort(key=sortkey)

    rules = {}
    cons = {}
    for name, tgt in (("rules_digest.json", "rules"), ("umsae_constraints.json", "cons")):
        p = os.path.join(BASE, name)
        if os.path.exists(p):
            v = json.load(open(p, encoding="utf-8"))
            if tgt == "rules":
                rules = v
            else:
                cons = v

    plan_p = os.path.join(BASE, "umsae_timeline.json")
    plan = json.load(open(plan_p, encoding="utf-8")) if os.path.exists(plan_p) else None
    payload = {"teams": teams, "subs": subs, "rules": rules, "cons": cons, "umsae": UMSAE, "plan": plan}
    data_js = json.dumps(payload, ensure_ascii=False)

    tpl = open(os.path.join(BASE, "_template.html"), encoding="utf-8").read()
    out = tpl.replace("/*__DATA__*/", "window.DV = " + data_js + ";")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)

    withcomp = sum(1 for d in teams if d["_track"]["comp"])
    print(f"Wrote {OUT}")
    print(f"  teams: {len(teams)} ({withcomp} with a parsed months-to-competition)")
    print(f"  subsystem deep dives: {len(subs)}")
    for d in teams:
        t = d["_track"]
        print(f"   - {d.get('item_name','?')[:42]:44} start={t['start_year']} run={t['run']} comp={t['comp']} bands={len(t['bands'])}")


if __name__ == "__main__":
    main()
