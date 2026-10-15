exec(open('verifikasi_dan_dashboard/verify.py').read())
import glob
sq=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(SP+'s5pk/b0*/s5_batch_0*_sequences.csv'))]); sq=sq[sq.method=='NR']
alld=sorted(sq.delivery_date.unique())
src='dashboard/routes_v3_anonim.json'
J=json.load(open(src)); days=J['days']
B=pd.read_csv(G+'data_deidentified/experiment_outputs/nr_fr_rg_sa_block_level.csv')
Bk={(r.delivery_date,r.trigger_fraction,r.shock,r.seed,r.method):r for r in B.itertuples()}
nb=0;mx=0
for k,day in days.items():
    d=alld[int(k[-3:])-1]
    g=sq[(sq.delivery_date==d)&(sq.trigger_fraction==0.25)&(sq['shock']=='p85')&(sq.seed==101)].sort_values(['vehicle_id','sequence'])
    ids=list(dict.fromkeys(g.node_id)); assert len(ids)==len(day['nodes'])
    for i,n in enumerate(ids):
        c=cust[(d,n)]; nd=day['nodes'][i]; nd['a']=round(float(c['tw_start']),2); nd['b']=round(float(c['tw_end']),2); nd['s']=round(float(c['service_min']),2)
    if not day['runs']: continue
    T={}
    for key in day['frozen']:
        tf,sh,sd=key.split('|'); fz=day['frozen'][key]
        for m in ['NR','FR','RG','SA']:
            o={}; tot=0
            for v,route in day['route'].items():
                if m=='NR': seq,nf=route,fz[v]
                else:
                    r=day['runs'].get(f'{key}|{m}')
                    seq,nf=(r[v] if r else (route,fz[v]))
                s=sim(d,[ids[i] for i in seq],nf,sh); tot+=s['late']
                o[v]=[round(x['arr'],2) for x in s['det']]
            ref=Bk[(k,float(tf),sh,int(sd),m)]; mx=max(mx,abs(tot-ref.total_lateness_min)); nb+=1
            T[f'{key}|{m}']=o
    day['t']=T
J['meta']['version']='v3.1 (jam tiba S5)'
J['meta']['s5time']={'start':480,'p85':1.1559,'p95':1.2935,'delay20':20,'delay30':30,'checked_blocks':nb,'max_abs_diff_lateness':mx}
out='dashboard/routes_v3_anonim.json'
json.dump(J,open(out,'w'),separators=(',',':'))
import os; print(nb,mx,os.path.getsize(out)/1e6,'MB')
