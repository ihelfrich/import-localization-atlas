#!/usr/bin/env python3
"""Global multi-country classification from CEPII BACI (HS22, 2022-2023 avg).
For every material importer vs China, compute the same dependence/scale/complexity
scoring as the Saudi pipeline, and emit one compact JSON per country + an index,
for the lazy-loading web tool. Values in BACI are thousand-USD."""
import os, glob, json, zipfile
import numpy as np, pandas as pd

BASE = "/Users/ian/Downloads/global_import_tool"
BACI = os.path.join(BASE, "baci")
SUP  = BASE                                  # support files (pci, hs6_codes) live here
OUTD = os.path.join(BASE, "docs", "data"); os.makedirs(OUTD, exist_ok=True)
YEARS = [2022, 2023]
MIN_CHINA_USD = 200e6                         # only reporters with material China imports

# ---- unzip if needed ----
zf = os.path.join(BACI, "BACI_HS22_V202601.zip")
if not glob.glob(os.path.join(BACI, "BACI_HS22_Y2023*.csv")):
    print("unzipping BACI...")
    with zipfile.ZipFile(zf) as z: z.extractall(BACI)

cc = pd.read_csv(glob.glob(os.path.join(BACI, "country_codes*.csv"))[0])
# normalize column names
cc.columns = [c.lower() for c in cc.columns]
isocol = "country_iso3" if "country_iso3" in cc.columns else [c for c in cc.columns if "iso3" in c][0]
namecol = "country_name" if "country_name" in cc.columns else [c for c in cc.columns if "name" in c][0]
codecol = "country_code" if "country_code" in cc.columns else cc.columns[0]
CHN = int(cc.loc[cc[isocol]=="CHN", codecol].iloc[0])
code2iso  = dict(zip(cc[codecol], cc[isocol]))
code2name = dict(zip(cc[codecol], cc[namecol]))
print("China BACI code:", CHN)

# ---- aggregate M_china and M_world per (importer, product), mean over years ----
china_parts, world_parts = [], []
for y in YEARS:
    f = glob.glob(os.path.join(BACI, f"BACI_HS22_Y{y}*.csv"))[0]
    df = pd.read_csv(f, usecols=["i","j","k","v"], dtype={"i":"int32","j":"int32","k":"int32","v":"float64"})
    world_parts.append(df.groupby(["j","k"], sort=False)["v"].sum().rename("v").reset_index().assign(y=y))
    ch = df[df["i"]==CHN]
    china_parts.append(ch.groupby(["j","k"], sort=False)["v"].sum().rename("v").reset_index().assign(y=y))
    print(f"year {y}: rows={len(df):,}")
    del df
world = pd.concat(world_parts).groupby(["j","k"], sort=False)["v"].mean().rename("M_world").reset_index()
china = pd.concat(china_parts).groupby(["j","k"], sort=False)["v"].mean().rename("M_china").reset_index()
m = world.merge(china, on=["j","k"], how="left")
m["M_china"] = m["M_china"].fillna(0.0)
m["M_world"] = np.maximum(m["M_world"], m["M_china"])
m["M_china"] *= 1000.0; m["M_world"] *= 1000.0     # thousUSD -> USD
m["hs6"] = m["k"].astype(str).str.zfill(6)

# ---- complexity + names ----
pci  = pd.read_csv(os.path.join(SUP,"pci_hs6.csv"), dtype={"hs6":str}); pci["hs6"]=pci["hs6"].str.zfill(6)
pci4 = pd.read_csv(os.path.join(SUP,"pci_hs4_fallback.csv"), dtype={"hs4":str}); pci4["hs4"]=pci4["hs4"].str.zfill(4)
codes= pd.read_csv(os.path.join(SUP,"hs6_codes.csv"), dtype=str); codes["hs6"]=codes["hs6"].str.zfill(6)
codes["desc"]=codes["desc"].str.replace(r"^[0-9]+ - ","",regex=True)
pcimap  = dict(zip(pci["hs6"], pci["pci"]))
namemap = dict(zip(pci["hs6"], pci["product_name"]))
pci4map = dict(zip(pci4["hs4"], pci4["pci_hs4"]))
descmap = dict(zip(codes["hs6"], codes["desc"]))
chapmap = dict(zip(codes["hs6"], codes["chapter"]))

def winsor(s):
    q=s.quantile([0.01,0.99]); return s.clip(q.iloc[0],q.iloc[1])
def mm(s):
    lo,hi=np.nanmin(s),np.nanmax(s)
    return pd.Series(np.where(np.isnan(s),np.nan,50.0),index=s.index) if hi<=lo else 100*(s-lo)/(hi-lo)
W=dict(dep=0.417,sca=0.250,cpx=0.333)

def score_country(g):
    g=g.copy()
    g["PCI"]=g["hs6"].map(pcimap)
    miss=g["PCI"].isna(); g.loc[miss,"PCI"]=g.loc[miss,"hs6"].str[:4].map(pci4map)
    g["D"]=np.where(g["M_world"]>0,g["M_china"]/g["M_world"],np.nan)
    g["logM"]=np.log10(g["M_china"].clip(lower=1))
    g["zD"]=mm(winsor(g["D"])); g["zS"]=mm(winsor(g["logM"])); g["zC"]=mm(winsor(g["PCI"]))
    Z=g[["zD","zS","zC"]].to_numpy(); w=np.array([W["dep"],W["sca"],W["cpx"]])
    pres=~np.isnan(Z); wsum=pres@w; contrib=np.where(np.isnan(Z),0,Z)@w
    g["CPS"]=np.where(wsum>0,contrib/wsum,np.nan)
    g["EXP"]=0.6*g["zD"]+0.4*g["zS"]; g["SOPH"]=g["zC"]
    return g

def r1(x): return None if pd.isna(x) else round(float(x),1)
def r2(x): return None if pd.isna(x) else round(float(x),2)
def r3(x): return None if pd.isna(x) else round(float(x),3)

index=[]
for j, g in m.groupby("j"):
    china_total=g["M_china"].sum()
    if china_total < MIN_CHINA_USD: continue
    iso=code2iso.get(j); name=code2name.get(j)
    if not isinstance(iso,str): continue
    g=g[g["M_china"]>0]
    if len(g)<30: continue
    g=score_country(g).sort_values("CPS",ascending=False)
    recs=[]
    for _,r in g.iterrows():
        nm=namemap.get(r["hs6"]) or descmap.get(r["hs6"]) or r["hs6"]
        recs.append([r["hs6"], str(nm)[:70], chapmap.get(r["hs6"],r["hs6"][:2]),
                     r1(r["M_china"]/1e6), r1(r["D"]*100), r2(r["PCI"]),
                     r3(r["zD"]), r3(r["zS"]), r3(r["zC"]), r3(r["EXP"]), r3(r["SOPH"]),
                     1 if r["M_china"]>5e6 else 0])
    json.dump(recs, open(os.path.join(OUTD,f"{iso}.json"),"w"), separators=(",",":"))
    nA=int(((g["EXP"]>=60)&(g["SOPH"].fillna(-1)>=60)).sum())
    index.append({"iso":iso,"name":name,"china_bn":round(china_total/1e9,2),
                  "n":len(g),"nA":nA,"share":round(china_total/g["M_world"].sum()*100)})
index.sort(key=lambda d:-d["china_bn"])
json.dump(index, open(os.path.join(BASE,"docs","index.json"),"w"), separators=(",",":"))
top = ", ".join("{}({:.0f}b)".format(d["iso"], d["china_bn"]) for d in index[:8])
print("wrote {} country files. Top: {}".format(len(index), top))
