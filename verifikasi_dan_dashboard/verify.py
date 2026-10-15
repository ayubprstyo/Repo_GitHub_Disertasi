import json, sys, math, pandas as pd, numpy as np
SP='./'
G=SP+'gh/IJIES_Reproducible_Routing_GitHub_READY_FINAL/IJIES_Reproducible_Routing/'
sys.path.insert(0,G)
from src.data import build_canonical_mapping
mp,cust,_=build_canonical_mapping(SP+'outs/04_audit_outputs/customer_day_stops_preprocessed.csv')
parent={(r.delivery_date,r.virtual_stop_id):r.parent_physical_node for r in mp.itertuples()}
def lm(p,col):
    df=pd.read_csv(p); o={}
    for d,g in df.groupby('delivery_date'): o[d]=dict(zip(zip(g.origin_id,g.destination_id),g[col]))
    return o
P50=lm(SP+'mx/combined_travel_time_matrix_p50_long.csv','travel_time_min_p50')
DI=lm(SP+'mx/combined_osrm_distance_matrix_km_long.csv','distance_km')
M={'p50':1.0,'p85':1.1559,'p95':1.2935}
def res(d,n): return 'DEPOT_1' if n=='DEPOT_1' else parent[(d,n)]
def tt(d,i,j,q):
    a,b=res(d,i),res(d,j)
    if a==b: return 0.0
    v=P50[d].get((a,b)); 
    if v is None: v=P50[d][(b,a)]
    return v*M[q]
def dist(d,i,j):
    a,b=res(d,i),res(d,j)
    if a==b: return 0.0
    v=DI[d].get((a,b)); 
    if v is None: v=DI[d][(b,a)]
    return v
def sim(d,seq,nfz,shock,start=480.0):
    isd=shock.startswith('delay'); rq='p50' if isd else shock
    da={'delay20':20.0,'delay30':30.0}.get(shock,0.0)
    t=start; prev='DEPOT_1'; pf=True; late=0; dd=0; det=[]; ot=0
    for k,n in enumerate(seq):
        fz=k<nfz; q='p50' if fz else rq
        x=tt(d,prev,n,q); dd+=dist(d,prev,n); t+=x
        if pf and not fz: t+=da
        arr=t; c=cust[(d,n)]
        if t<c['tw_start']: t=c['tw_start']
        l=max(0.0,t-c['tw_end']); late+=l
        det.append(dict(n=n,arr=arr,start=t,late=l,fz=fz,tw0=c['tw_start'],tw1=c['tw_end'],svc=c['service_min']))
        t+=c['service_min']; prev=n; pf=fz
    qb='p50' if pf else rq
    dd+=dist(d,prev,'DEPOT_1'); t+=tt(d,prev,'DEPOT_1',qb)
    return dict(late=late,dist=dd,end=t,det=det)
