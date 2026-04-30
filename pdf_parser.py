from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import os, json, re
import pdfplumber, pandas as pd

ENROLL_RE = re.compile(r"\b\d{2}[A-Z]{2}\d{3}UG\d{5}\b", re.I)
COLLEGE_CODE_RE = re.compile(r"\b[A-Z]{3}\d{5}\b", re.I)
SPECIAL_ZERO={"ZOO","000","00","0"}
SPECIAL_ABSENT={"AB","A B","AL"}
SPECIAL_CODE_NAME_MAP = {
    "24CS-BCAP-MA-01-01001": "PROGRAMMING IN C",
    "24CS-BCAP-MA-01-02002": "NETWORKING & INTERNET ENVIRONMENT",
    "24CS-BCAP-MI-01-01003": "C F & EMERGING TECHNOLOGIES",
    "24CS-BCAP-MU-01-01004": "PRACTICAL BASED ON MAJOR 1 & MAJOR 2",
    "24CS-BCAP-AE-01-01005": "CRITICAL THINKING AND PROBLEM SOLVING",
    "24CS-BCAP-SE-01-01006": "MATHS. & STAT. FOUNDATION OF COMPUTER SCIENCE",
    "24CS-BCAP-IK-01-01007": "MATHEMATICS IN ANCIENT INDIA: EXPLORING THE RICH HERITAGE OF VEDIC MATHEMATICS",
}

def detect_input_type(_pdf_path:str)->str: return "CR_REPORT"

def _safe_text(page):
    try: return page.extract_text() or ""
    except Exception: return ""

def _to_int_token(tok:str)->Optional[int]:
    if tok is None: return None
    t=str(tok).strip().upper()
    if not t or t in SPECIAL_ABSENT: return None
    if t in SPECIAL_ZERO: return 0
    if t.isdigit():
        try: return int(t)
        except Exception: return None
    return None

def _token_is_absent(tok:str)->bool:
    return tok is not None and str(tok).strip().upper() in SPECIAL_ABSENT

def pdf_contains_subjects(pdf_path:str, subjects:List[str], pages_to_check:int=2)->Tuple[bool,List[str],List[str]]:
    if not subjects: return True,[],[]
    subj=[s.strip() for s in subjects if s and str(s).strip()]
    if not subj: return True,[],[]
    found=set()
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages[:pages_to_check]:
                t=_safe_text(p).upper()
                for s in subj:
                    if s.upper() in t: found.add(s)
    except Exception:
        return True,[],[]
    missing=[s for s in subj if s not in found]
    return len(missing)==0, missing, sorted(found)

@dataclass
class SubjectDef:
    idx:int
    name:str
    cs_num:str
    col_prefix:str

def _load_subject_template_data()->dict:
    try:
        p=os.path.join(os.path.dirname(os.path.abspath(__file__)),"subject_template_example.json")
        if not os.path.exists(p): return {}
        with open(p,"r",encoding="utf-8") as f: data=json.load(f)
        if not isinstance(data,dict): return {}
        return {str(k).strip().upper(): str(v).strip() for k,v in data.items() if str(k).strip() and str(v).strip()}
    except Exception:
        return {}

TEMPLATE_MAP=_load_subject_template_data()

def _header_cut(text:str)->str:
    if not text: return ""
    idx=text.upper().find("SEAT NO.")
    return text[:idx] if idx>=0 else text

def _count_subjects_from_header(text:str)->int:
    mx=0
    for ln in text.splitlines():
        u=ln.upper()
        if any(label in u for label in ("THE TOTAL","INT TOTAL","PRA TOTAL","TOTAL")):
            mx=max(mx, len(re.findall(r"\d+\s*/\s*\d+", ln)))
    return mx

def _clean_subject_name(raw:str, code:str)->Tuple[str,str]:
    raw=re.sub(r"\s+"," ", raw).strip(" :-").replace("EXPLORINGTHE","EXPLORING THE")
    m=re.search(r"\bCS\s*[-–—]?\s*(\d{1,2})\b", raw, re.I)
    cs_short=f"CS{int(m.group(1)):02d}" if m else ""
    if code in SPECIAL_CODE_NAME_MAP: return SPECIAL_CODE_NAME_MAP[code], cs_short
    if cs_short and cs_short in TEMPLATE_MAP: return TEMPLATE_MAP[cs_short], cs_short
    raw=re.sub(r"^CS\s*[-–—]?\s*\d{1,2}\s*:\s*","", raw, flags=re.I).strip()
    return raw or code, cs_short

def _extract_subjects_from_first_page(first_text:str)->List[SubjectDef]:
    text=first_text or ""
    header=_header_cut(text)
    flat=re.sub(r"\s+"," ", header)
    code_pat=re.compile(r"((?:\d{2}(?:CS|SI)-BCAP-[A-Z]{2}-\d{2}-\d{5}))\s*:\s*", re.I)
    matches=list(code_pat.finditer(flat))
    n=_count_subjects_from_header(text) or len(matches) or 1
    subs=[]
    for i,m in enumerate(matches[:n]):
        start=m.end(); end=matches[i+1].start() if i+1<len(matches) else len(flat)
        code=m.group(1).upper()
        name, cs_short = _clean_subject_name(flat[start:end], code)
        subs.append(SubjectDef(i, name, cs_short or code, f"s{i+1:02d}"))
    if subs: return subs
    return [SubjectDef(i, f"SUBJECT {i+1}", "", f"s{i+1:02d}") for i in range(n)]

def _find_student_starts(lines:List[str])->List[int]:
    starts=[i for i,ln in enumerate(lines) if ENROLL_RE.search(ln)]
    out=[]; last=-999
    for i in starts:
        if i-last>1: out.append(i); last=i
    return out

def _extract_name_from_line(line:str)->Tuple[str,str]:
    m=ENROLL_RE.search(line)
    enroll=m.group(0).upper().strip() if m else ""
    if not m: return "",""
    rest=line[m.end():]
    stop=len(rest)
    for pat in (COLLEGE_CODE_RE, ENROLL_RE, re.compile(r"\bPASS\b"), re.compile(r"\bFAIL\b"), re.compile(r"\bABSENT\b")):
        mm=pat.search(rest)
        if mm: stop=min(stop, mm.start())
    name=rest[:stop]
    name=re.sub(r"[^A-Z() .]"," ", name.upper())
    name=re.sub(r"\s{2,}"," ", name).strip()
    return enroll, name

def _extract_right_panel_metrics(block_lines:List[str]):
    first_line=block_lines[0].upper() if block_lines else ""
    result="PASS" if re.search(r"\bPASS\b", first_line) else "FAIL" if re.search(r"\bFAIL\b", first_line) else "ABSENT" if re.search(r"\bABSENT\b", first_line) else "ELIGIBLE" if re.search(r"\bWH[_\s]ELI\b|\bELIGIBLE\b|\bWHOLE\s*ELI\b", first_line, re.I) else "UNKNOWN"
    block_text="\n".join(block_lines).upper()
    m=re.search(r"(\d+)\s*/\s*550", block_text); total_550=m.group(1) if m else ""
    m=re.search(r"(\d+(?:\.\d+)?)\s*%", block_text); percentage=m.group(1) if m else ""
    decs=[x for x in re.findall(r"\b\d+\.\d+\b", block_text) if x!=percentage]
    small=[x for x in decs if float(x)<=10.0]
    sgpa=small[0] if small else ""
    cgpa=small[1] if len(small)>1 and small[1]!=small[0] else ""
    return result,total_550,percentage,sgpa,cgpa

def _collect_mark_tokens(line:str,label:str,needed:int)->List[str]:
    u=line.upper(); pos=u.find(label)
    if pos<0: return []
    vals=[]
    for tok in line[pos+len(label):].split():
        up=tok.strip().upper()
        if re.fullmatch(r"(AB|AL|ZOO|\d{1,3})", up):
            vals.append(up)
            if len(vals)>=needed: break
    return vals

def _collect_grade_tokens(line:str,needed:int)->List[str]:
    vals=[]
    for tok in line.split():
        up=tok.strip().upper()
        if re.fullmatch(r"\d+/[A-Z+]+/\d+(?:\([^)]+\))?|AB", up):
            vals.append(up)
            if len(vals)>=needed: break
    return vals

def _extract_marks_table(block_lines:List[str], subjects:List[SubjectDef]):
    n=len(subjects)
    has_pra_header=any("PRA TOTAL" in ln.upper() for ln in block_lines)
    practical_indices=[i for i,s in enumerate(subjects) if re.search(r"PRACTICAL|PROJECT", s.name, re.I)]
    the_vals=[""]*n; int_vals=[""]*n; pra_vals=[""]*n; tot_vals=[""]*n; grade_vals=[""]*n
    def map_vals(vals,indices):
        out=[""]*n
        for v,idx in zip(vals,indices): out[idx]=v
        return out
    tot_idx=-1
    for idx,ln in enumerate(block_lines):
        u=ln.upper()
        if "THE TOTAL" in u:
            vals=_collect_mark_tokens(ln,"THE TOTAL",n)
            if has_pra_header and practical_indices and len(vals)<n:
                non=[i for i in range(n) if i not in practical_indices]
                the_vals=map_vals(vals,non)
            else:
                the_vals=map_vals(vals,list(range(n)))
        elif "INT TOTAL" in u:
            int_vals=map_vals(_collect_mark_tokens(ln,"INT TOTAL",n), list(range(n)))
        elif "PRA TOTAL" in u:
            vals=_collect_mark_tokens(ln,"PRA TOTAL",n)
            if practical_indices and len(vals)<=len(practical_indices):
                pra_vals=map_vals(vals, practical_indices)
            else:
                pra_vals=map_vals(vals, list(range(n)))
        elif re.search(r"\bTOT\b", u):
            tot_vals=map_vals(_collect_mark_tokens(ln,"TOT",n), list(range(n))); tot_idx=idx
    if tot_idx>=0:
        for j in range(tot_idx+1, min(tot_idx+4, len(block_lines))):
            vals=_collect_grade_tokens(block_lines[j],n)
            if vals:
                grade_vals=map_vals(vals, list(range(n))); break
    for i in range(n):
        if not str(tot_vals[i]).strip():
            nums=[v for v in (_to_int_token(x) for x in [the_vals[i],int_vals[i],pra_vals[i]]) if v is not None]
            if nums: tot_vals[i]=str(sum(nums))
            elif all(_token_is_absent(x) or not str(x).strip() for x in [the_vals[i],int_vals[i],pra_vals[i]]): tot_vals[i]="ABSENT"
    has_pra=any(v for v in pra_vals)
    return the_vals,int_vals,(pra_vals if has_pra else None),tot_vals,grade_vals

def parse_cr_pdf(pdf_path:str, return_meta:bool=False):
    rows=[]
    with pdfplumber.open(pdf_path) as pdf:
        first_text=_safe_text(pdf.pages[0]) if pdf.pages else ""
        subjects=_extract_subjects_from_first_page(first_text)
        for page in pdf.pages:
            text=_safe_text(page)
            if not text: continue
            lines=[ln.rstrip() for ln in text.splitlines() if ln.strip()]
            starts=_find_student_starts(lines)
            for si,start in enumerate(starts):
                end=starts[si+1] if si+1<len(starts) else len(lines)
                block_lines=lines[start:end]
                enroll,name=_extract_name_from_line(lines[start])
                if not enroll:
                    m=ENROLL_RE.search("\n".join(block_lines))
                    if not m: continue
                    enroll=m.group(0).upper().strip()
                result,total_550,percentage,sgpa,cgpa=_extract_right_panel_metrics(block_lines)
                the_vals,int_vals,pra_vals,tot_vals,grade_vals=_extract_marks_table(block_lines,subjects)
                row={"enrollment_no":enroll,"name":name,"result":result,"total_marks_550":total_550,"percentage":percentage,"sgpa":sgpa,"cgpa":cgpa}
                has_pra=pra_vals is not None
                for i,s in enumerate(subjects):
                    pref=s.col_prefix
                    row[f"{pref}_the_total"]=the_vals[i] if i<len(the_vals) else ""
                    row[f"{pref}_int_total"]=int_vals[i] if i<len(int_vals) else ""
                    if has_pra: row[f"{pref}_pra_total"]=pra_vals[i] if i<len(pra_vals) else ""
                    row[f"{pref}_total"]=tot_vals[i] if i<len(tot_vals) else ""
                    row[f"{pref}_grade_token"]=grade_vals[i] if i<len(grade_vals) else ""
                rows.append(row)
    df=pd.DataFrame(rows)
    if not df.empty and "enrollment_no" in df.columns:
        df["__name_len"]=df["name"].astype(str).str.len()
        df=df.sort_values(["enrollment_no","__name_len"],ascending=[True,False]).drop_duplicates(subset=["enrollment_no"],keep="first").drop(columns=["__name_len"],errors="ignore").reset_index(drop=True)
    meta={"pdf_path":pdf_path,"subjects":[{"name":s.name,"cs_num":s.cs_num,"col_prefix":s.col_prefix} for s in subjects]}
    return (df,meta) if return_meta else df