exec(open('verifikasi_dan_dashboard/verify.py').read())
import glob, pickle
sq=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(SP+'s5pk/b0*/s5_batch_0*_sequences.csv'))]); sq=sq[sq.method=='NR']
alld=sorted(sq.delivery_date.unique())
J=json.load(open('dashboard/routes_v3_anonim.json'))['days']
B=pd.read_csv(G+'data_deidentified/experiment_outputs/nr_fr_rg_sa_block_level.csv')
Bk={(r.delivery_date,r.trigger_fraction,r.shock,r.seed,r.method):r for r in B.itertuples()}
bad=0;n=0;maxd=0;out={}
for k,day in J.items():
    if not day['runs']: continue
    d=alld[int(k[-3:])-1]
    g=sq[(sq.delivery_date==d)&(sq.trigger_fraction==0.25)&(sq['shock']=='p85')&(sq.seed==101)].sort_values(['vehicle_id','sequence'])
    ids=list(dict.fromkeys(g.node_id)); assert len(ids)==len(day['nodes'])
    for key in day['frozen']:
        tf,sh,sd=key.split('|'); tf=float(tf); sd=int(sd); fz=day['frozen'][key]
        for m in ['NR','FR','RG','SA']:
            tot=0;dst=0; rr={}
            for v,route in day['route'].items():
                if m=='NR': seq=route; nf=fz[v]
                else:
                    r=day['runs'].get(f'{key.split("|")[0]}|{sh}|{sd}|{m}')
                    if r is None: seq=route; nf=fz[v]
                    else: seq,nf=r[v]
                    # NOTE original tf string format
                s=sim(d,[ids[i] for i in seq],nf,sh); tot+=s['late']; dst+=s['dist']
            ref=Bk.get((k,tf,sh,sd,m))
            if ref is None: continue
            n+=1; dl=abs(tot-ref.total_lateness_min); dd=abs(dst-ref.total_distance_km); maxd=max(maxd,dl)
            if dl>1e-3 or dd>1e-2:
                bad+=1
                if bad<=8: print('MISMATCH',k,tf,sh,sd,m,'late',round(tot,4),round(ref.total_lateness_min,4),'dist',round(dst,3),ref.total_distance_km)
print('checked',n,'bad',bad,'maxd',maxd)
