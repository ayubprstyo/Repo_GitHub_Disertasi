exec(open('verifikasi_dan_dashboard/verify.py').read())
import numpy as np
runs=pd.read_csv(SP+'nb/pk3/semua_run_S0-S4_3seed.csv')
best=runs.loc[runs.groupby(['scenario','delivery_date']).objective.idxmin()]
WC,VC=10000.0,3992800.0
out={};dist={}
for S in ['S0','S1','S2','S3','S4']:
    rows=[]
    for r in best[best.scenario==S].itertuples():
        f=SP+f'nb/ck_all/{S}_{r.delivery_date}_seed{r.seed}_routes.csv'; d=pd.read_csv(f); d=d[d.node_id!='DEPOT_1']
        for v,g in d.groupby('vehicle_id'):
            w=sum(cust[(r.delivery_date,n)]['weight'] for n in g.node_id); vo=sum(cust[(r.delivery_date,n)]['volume'] for n in g.node_id)
            rows.append((r.delivery_date,v,w/WC*100,vo/VC*100,len(g)))
    a=pd.DataFrame(rows,columns=['d','v','wu','vu','n']); out[S]=a
    print(S,len(a),'wu mean',round(a.wu.mean(),2),'vu mean',round(a.vu.mean(),2),'vu median',round(a.vu.median(),1),'max',round(a.vu.max(),1),
      'agg vu',round(a.vu.sum()/len(a),2),'<25%',round((a.vu<25).mean()*100,1),'25-50',round(((a.vu>=25)&(a.vu<50)).mean()*100,1),'50-75',round(((a.vu>=50)&(a.vu<75)).mean()*100,1),'75-100',round(((a.vu>=75)&(a.vu<=100.0001)).mean()*100,1),'>100',round((a.vu>100.0001).mean()*100,1),'stops/route',round(a.n.mean(),1))
print('--- cek definisi audit')
for S,a in out.items():
    print(S,'rata2 per-tanggal wu/vu',round(a.groupby('d').wu.mean().mean(),2),round(a.groupby('d').vu.mean().mean(),2),'| rata2 per-rute',round(a.wu.mean(),2),round(a.vu.mean(),2))
import json
J=json.load(open('dashboard/routes_v3_anonim.json'))
U={}
for S,a in out.items():
    vu=a.vu;U[S]={'n':int(len(a)),'wu':round(a.wu.mean(),2),'vu':round(vu.mean(),2),'vmed':round(vu.median(),1),'wmed':round(a.wu.median(),1),
     'b':[round(100*x,1) for x in [(vu<25).mean(),((vu>=25)&(vu<50)).mean(),((vu>=50)&(vu<75)).mean(),((vu>=75)&(vu<=100.0001)).mean(),(vu>100.0001).mean()]],
     'idle':round(float((100-vu.clip(upper=100)).sum()/100),1)}
J['meta']['util']=U
json.dump(J,open('dashboard/routes_v3_anonim.json','w'),separators=(',',':'));print(U)
