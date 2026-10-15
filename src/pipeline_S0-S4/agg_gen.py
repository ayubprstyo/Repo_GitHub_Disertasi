import json, glob, re, itertools
import sys
SEEDS=[int(x) for x in sys.argv[1].split(',')]; S4SRC=sys.argv[2]; TAG=sys.argv[3]
exec(open('v5_lib.py').read())
from scipy.stats import wilcoxon
base_cfg = S4Config(capacity_weight_kg=CAPACITY_WEIGHT_KG, capacity_volume_cm3=CAPACITY_VOLUME_CM3, depot_start_min=DEPOT_START_MIN,
    route_end_target_min=ROUTE_END_TARGET_MIN, max_routes=MAX_ROUTES_PER_DAY, w_vehicle=VEHICLE_OPENING_PENALTY, iterations=S4_ITERATIONS,
    local_search_trials=S4_LOCAL_SEARCH_TRIALS, early_stop_patience=S4_EARLY_STOP, early_stop_min_iterations=20)
SP='./'
CK=SP+'nb/ck_all/'; lock=pd.read_csv(SP+'lock/s4_routes_best.csv')
runs={}
for f in glob.glob(CK+'S[0-4]_*_metrics.json'):
    m=re.match(r'.*/(S\d)_(\d{4}-\d\d-\d\d)_seed(\d+)_metrics.json',f)
    if int(m.group(3)) in SEEDS: runs.setdefault((m.group(1),m.group(2)),{})[int(m.group(3))]=json.load(open(f))['metrics']['objective']
dates=[d for d in repo.dates if all(len(runs.get((s,d),{}))==len(SEEDS) for s in (['S0','S1','S2','S3','S4'] if S4SRC=='ck' else ['S0','S1','S2','S3']))]
print('tanggal lengkap:',len(dates),'dari',len(repo.dates))
rows=[]
for d in dates:
    base=repo.get_instance(d); idx={n:i for i,n in enumerate(base.node_ids)}
    for s in ['S0','S1','S2','S3','S4']:
        if s=='S4' and S4SRC=='lock':
            g=lock[lock.delivery_date==d]; routes=[[idx[str(n)] for n in x.node_id if str(n)!='DEPOT_1'] for v,x in g.sort_values(['vehicle_id','sequence']).groupby('vehicle_id',sort=False)]
        else:
            sd=min(runs[(s,d)],key=lambda k:runs[(s,d)][k]); routes=_routes_from_checkpoint(Path(CK+f'{s}_{d}_seed{sd}_routes.csv'),_copy_instance_for_scenario(base,s))
        routes=[r for r in routes if r]; cfg=_config_for_scenario(base_cfg,s)
        for ev,mode in [('own','adaptive' if s=='S4' else 'p50'),('p50','p50'),('p85','p85'),('p95','p95')]:
            inst_e=_copy_instance_for_scenario(base,s) if ev=='own' else base
            m=evaluate_solution(routes,inst_e,cfg,mode=mode)
            rows.append(dict(date=d,scen=s,ev=ev,dist=m['distance_km'],travel=m['travel_time_min'],late=m['lateness_min'],on=m['on_time_count'],n=m['customer_count'],veh=m['vehicle_count'],overtime=m['overtime_min']))
df=pd.DataFrame(rows); df.to_csv(SP+f'nb/final_per_date_{TAG}.csv',index=False)
tot=df.groupby(['ev','scen']).agg(dist=('dist','sum'),travel=('travel','sum'),late=('late','sum'),on=('on','sum'),n=('n','sum'),veh=('veh','sum'),overtime=('overtime','sum')).reset_index()
tot['otd']=100*tot.on/tot.n; tot.to_csv(SP+f'nb/final_totals_{TAG}.csv',index=False)
pd.set_option('display.width',200)
for ev in ['own','p50','p85','p95']: print('\n== evaluasi',ev); print(tot[tot.ev==ev][['scen','dist','travel','late','otd','veh','overtime']].round(2).to_string(index=False))
# uji berpasangan S4 vs lain, Holm atas semua
res=[]
for ev in ['p50','p85','p95']:
    for metric in ['late','dist','veh']:
        p=df[df.ev==ev].pivot(index='date',columns='scen',values=metric)
        for o in ['S0','S1','S2','S3']:
            diff=p['S4']-p[o]
            try: pv=wilcoxon(p['S4'],p[o]).pvalue
            except Exception: pv=1.0
            res.append(dict(ev=ev,metric=metric,vs=o,median_diff=diff.median(),S4_lebih_kecil=int((diff<-1e-9).sum()),S4_lebih_besar=int((diff>1e-9).sum()),seri=int((diff.abs()<=1e-9).sum()),p=pv))
r=pd.DataFrame(res)
# Holm
order=r.p.argsort().values; m=len(r); adj=[0]*m; prev=0
for rank,i in enumerate(order): prev=max(prev,min(1,(m-rank)*r.p.iloc[i])); adj[i]=prev
r['p_holm']=adj; r.to_csv(SP+f'nb/final_paired_tests_{TAG}.csv',index=False); print('\n',r.round(4).to_string(index=False))
