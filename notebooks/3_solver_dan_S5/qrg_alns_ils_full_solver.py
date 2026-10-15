from __future__ import annotations
import os, math, random, time, json, zipfile, shutil
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
STOPS_PATH = BASE / 'inputs/customer_day_stops_preprocessed.csv'
MATRIX_DIR = BASE / 'inputs/osrm_tomtom_saved_matrices_all_extracted'
OUT = BASE / 'outputs'
OUT.mkdir(exist_ok=True)
VEHICLE_WEIGHT_KG = 10000.0
VEHICLE_VOLUME_CM3 = 3992800.0
DEPOT_ID='DEPOT_1'
START_TIME_MIN=8*60
SERVICE_COL='service_time_min_baseline'
THETA1=10.0; THETA2=30.0
W=dict(distance=1.0, travel=0.10, lateness=8.0, risk=2.0, vehicle=30.0, capimb=3.0)
MAX_REMOVE=10; REMOVAL_FRACTION=0.12

def load_inputs():
    stops=pd.read_csv(STOPS_PATH)
    stops['delivery_date']=pd.to_datetime(stops['delivery_date']).dt.strftime('%Y-%m-%d')
    stops['node_id']=stops['customer_code'].astype(str)
    for c in ['total_weight','total_volume','tw_start_min','tw_end_min',SERVICE_COL]:
        stops[c]=pd.to_numeric(stops[c], errors='coerce').fillna(0.0)
    mats={}
    files={
        'd':('combined_osrm_distance_matrix_km_long.csv','distance_km'),
        'p50':('combined_travel_time_matrix_p50_long.csv','travel_time_min_p50'),
        'p85':('combined_travel_time_matrix_p85_long.csv','travel_time_min_p85'),
        'p95':('combined_travel_time_matrix_p95_long.csv','travel_time_min_p95'),
    }
    for key,(fn,val) in files.items():
        df=pd.read_csv(MATRIX_DIR/fn)
        df['delivery_date']=pd.to_datetime(df['delivery_date']).dt.strftime('%Y-%m-%d')
        mats[key]={}
        for date, g in df.groupby('delivery_date'):
            mats[key][date]={(str(r.origin_id),str(r.destination_id)): float(getattr(r,val)) for r in g.itertuples()}
    return stops, mats

def info_for_day(day):
    return {str(r.node_id): dict(weight=float(r.total_weight), volume=float(r.total_volume), tw_start=float(r.tw_start_min), tw_end=float(r.tw_end_min), service=float(getattr(r,SERVICE_COL)), customer_name=str(r.customer_name), lon=float(r.longitude), lat=float(r.latitude)) for r in day.itertuples()}

def cap_ok(route, info):
    return sum(info[n]['weight'] for n in route) <= VEHICLE_WEIGHT_KG + 1e-9 and sum(info[n]['volume'] for n in route) <= VEHICLE_VOLUME_CM3 + 1e-9

def q_select(pred_late):
    return 'p50' if pred_late <= THETA1 else ('p85' if pred_late <= THETA2 else 'p95')

def eval_route(route, md, info, mode='qrg'):
    tcur=START_TIME_MIN; prev=DEPOT_ID
    dist=travel=late_total=risk=0.0; detail=[]
    for seq,node in enumerate(route,1):
        d=md['d'].get((prev,node),1e6)
        pred_arr=tcur+md['p50'].get((prev,node),1e6)
        pred_late=max(0.0,pred_arr-info[node]['tw_end'])
        q = mode if mode in ('p50','p85','p95') else q_select(pred_late)
        tt=md[q].get((prev,node),1e6)
        arr=tcur+tt
        wait=max(0.0,info[node]['tw_start']-arr)
        late=max(0.0,arr-info[node]['tw_end'])
        dep=arr+wait+info[node]['service']
        dist += d; travel += tt; late_total += late; risk += {'p50':0,'p85':0.5,'p95':1.0}[q]*late
        detail.append({'sequence':seq,'node_id':node,'arrival_time_min':arr,'departure_time_min':dep,'wait_min':wait,'lateness_min':late,'quantile_used':q})
        tcur=dep; prev=node
    if route:
        dist += md['d'].get((prev,DEPOT_ID),0)
        q = 'p50' if mode == 'qrg' else mode
        travel += md[q].get((prev,DEPOT_ID),0)
    return dist, travel, late_total, risk, detail

def route_obj(route, md, info, mode='qrg'):
    d,t,l,r,_=eval_route(route,md,info,mode)
    if route:
        wt=sum(info[n]['weight'] for n in route)/VEHICLE_WEIGHT_KG
        vv=sum(info[n]['volume'] for n in route)/VEHICLE_VOLUME_CM3
        capimb=abs(wt-vv)
    else: capimb=0
    return W['distance']*d + W['travel']*t + W['lateness']*l + W['risk']*r + W['capimb']*capimb

def solution_eval(routes, md, info, mode='qrg'):
    dist=travel=late=risk=0.0; rows=[]
    for vi,rt in enumerate(routes,1):
        d,t,l,r,det=eval_route(rt,md,info,mode)
        dist+=d; travel+=t; late+=l; risk+=r
        w=sum(info[n]['weight'] for n in rt); v=sum(info[n]['volume'] for n in rt)
        for row in det:
            row=row.copy(); row['vehicle_id']=f'VEH_{vi:03d}'; row['route_weight_kg']=w; row['route_volume_cm3']=v; rows.append(row)
    n=sum(len(r) for r in routes); on=sum(row['lateness_min'] <= 1e-9 for row in rows)
    obj=W['distance']*dist+W['travel']*travel+W['lateness']*late+W['risk']*risk+W['vehicle']*len(routes)
    return {'objective':obj,'distance':dist,'travel':travel,'lateness':late,'risk':risk,'vehicles':len(routes),'otd':100*on/n if n else 0.0,'detail':rows}

def greedy_insert(routes, node, md, info, mode='qrg'):
    best=None
    for ri,rt in enumerate(routes):
        old=route_obj(rt,md,info,mode)
        for pos in range(len(rt)+1):
            cand=rt[:pos]+[node]+rt[pos:]
            if not cap_ok(cand,info): continue
            delta=route_obj(cand,md,info,mode)-old
            if best is None or delta < best[0]: best=(delta,ri,cand)
    if info[node]['weight']<=VEHICLE_WEIGHT_KG and info[node]['volume']<=VEHICLE_VOLUME_CM3:
        delta=route_obj([node],md,info,mode)+W['vehicle']
        if best is None or delta < best[0]: best=(delta,len(routes),[node])
    if best is None:
        routes.append([node])
    else:
        _,ri,cand=best
        if ri==len(routes): routes.append(cand)
        else: routes[ri]=cand
    return routes

def initial_solution(nodes, md, info):
    routes=[]
    for node in sorted(nodes, key=lambda n:(info[n]['tw_end'], info[n]['tw_start'])):
        routes=greedy_insert(routes,node,md,info,'p50')
    return routes

def destroy(routes, md, info, rng, n_remove):
    all_nodes=[n for rt in routes for n in rt]
    op=rng.choice(['lateness_priority','random','worst_arc'])
    if op=='random': rem=rng.sample(all_nodes,min(n_remove,len(all_nodes)))
    elif op=='lateness_priority':
        ev=solution_eval(routes,md,info,'qrg')
        ranked=sorted([(row['lateness_min'], row['node_id']) for row in ev['detail']], reverse=True)
        positives=[n for l,n in ranked if l>0]
        rem=(positives + [n for n in all_nodes if n not in positives])[:min(n_remove,len(all_nodes))]
    else:
        vals=[]
        for rt in routes:
            for i,n in enumerate(rt):
                prev=DEPOT_ID if i==0 else rt[i-1]
                nxt=DEPOT_ID if i==len(rt)-1 else rt[i+1]
                saving=md['d'].get((prev,n),0)+md['d'].get((n,nxt),0)-md['d'].get((prev,nxt),0)
                vals.append((saving,n))
        rem=[n for _,n in sorted(vals, reverse=True)[:min(n_remove,len(all_nodes))]]
    remset=set(rem)
    new=[[n for n in rt if n not in remset] for rt in routes]
    new=[rt for rt in new if rt]
    return new, rem, op

def repair(routes, removed, md, info, rng):
    for node in sorted(removed, key=lambda n:(info[n]['tw_end'], rng.random())):
        routes=greedy_insert(routes,node,md,info,'qrg')
    return routes

def local_improve(routes, md, info, rng, attempts=60):
    routes=[list(r) for r in routes if r]
    best=solution_eval(routes,md,info,'qrg')['objective']
    for _ in range(attempts):
        cand=[list(r) for r in routes]
        if not cand: break
        move=rng.choice(['relocate','swap','two_opt'])
        if move=='relocate':
            r1=rng.randrange(len(cand));
            if not cand[r1]: continue
            i=rng.randrange(len(cand[r1])); node=cand[r1].pop(i)
            if not cand[r1]: cand.pop(r1)
            r2=rng.randrange(len(cand)+1)
            if r2==len(cand): cand.append([node])
            else: cand[r2].insert(rng.randrange(len(cand[r2])+1),node)
        elif move=='swap':
            if len(cand)<1: continue
            r1=rng.randrange(len(cand)); r2=rng.randrange(len(cand))
            if not cand[r1] or not cand[r2]: continue
            i=rng.randrange(len(cand[r1])); j=rng.randrange(len(cand[r2])); cand[r1][i], cand[r2][j]=cand[r2][j], cand[r1][i]
        else:
            r=rng.randrange(len(cand))
            if len(cand[r])<4: continue
            i,j=sorted(rng.sample(range(len(cand[r])),2)); cand[r][i:j+1]=list(reversed(cand[r][i:j+1]))
        cand=[rt for rt in cand if rt]
        if any(not cap_ok(rt,info) for rt in cand): continue
        obj=solution_eval(cand,md,info,'qrg')['objective']
        if obj < best - 1e-9:
            routes=cand; best=obj
    return routes

def qrg_alns_ils(nodes, md, info, seed=42, n_iter=25):
    rng=random.Random(seed)
    current=initial_solution(nodes,md,info)
    current=local_improve(current,md,info,rng,attempts=40)
    cur_ev=solution_eval(current,md,info,'qrg')
    best=[list(r) for r in current]; best_ev=cur_ev.copy()
    rem=max(2,min(MAX_REMOVE,int(len(nodes)*REMOVAL_FRACTION)))
    temp=max(1.0,cur_ev['objective']*0.01)
    hist=[]
    for it in range(1,n_iter+1):
        partial, removed, op=destroy(current,md,info,rng,rem)
        cand=repair(partial,removed,md,info,rng)
        cand=local_improve(cand,md,info,rng,attempts=30)
        cand_ev=solution_eval(cand,md,info,'qrg')
        delta=cand_ev['objective']-cur_ev['objective']
        accept=delta<0 or rng.random()<math.exp(-delta/max(temp,1e-9))
        if accept:
            current=[list(r) for r in cand]; cur_ev=cand_ev
        if cand_ev['objective'] < best_ev['objective']:
            best=[list(r) for r in cand]; best_ev=cand_ev
        hist.append({'iteration':it,'operator':op,'current_objective':cur_ev['objective'],'best_objective':best_ev['objective'],'best_lateness':best_ev['lateness'],'best_otd':best_ev['otd']})
        temp *= 0.95
    return best, best_ev, pd.DataFrame(hist)

def run_all(n_iter=25, seed=42, dates=None):
    stops,mats=load_inputs()
    date_list=sorted(stops.delivery_date.unique()) if dates is None else dates
    seq_rows=[]; met_rows=[]; hist_all=[]
    for idx,date in enumerate(date_list,1):
        day=stops[stops.delivery_date==date].copy()
        info=info_for_day(day); nodes=day.node_id.tolist()
        md={k:mats[k][date] for k in ['d','p50','p85','p95']}
        routes,ev,hist=qrg_alns_ils(nodes,md,info,seed,n_iter)
        ev=solution_eval(routes,md,info,'qrg')
        met_rows.append({'delivery_date':date,'stop_count':len(nodes),'vehicles_used':ev['vehicles'],'total_distance_km':round(ev['distance'],4),'total_travel_time_min':round(ev['travel'],4),'total_lateness_min':round(ev['lateness'],4),'on_time_delivery_pct':round(ev['otd'],4),'risk_penalty':round(ev['risk'],4),'objective':round(ev['objective'],4)})
        for row in ev['detail']:
            seq_rows.append({'delivery_date':date,'vehicle_id':row['vehicle_id'],'sequence':row['sequence'],'node_id':row['node_id'],'method':'QRG_ALNS_ILS','seed':seed,'trigger_fraction':'','shock':'','arrival_time_min':round(row['arrival_time_min'],3),'departure_time_min':round(row['departure_time_min'],3),'lateness_min':round(row['lateness_min'],3),'quantile_used':row['quantile_used'],'route_weight_kg':round(row['route_weight_kg'],3),'route_volume_cm3':round(row['route_volume_cm3'],3)})
        hist.insert(0,'delivery_date',date); hist_all.append(hist)
        print(f'{idx:02d}/{len(date_list)} {date} stops={len(nodes)} veh={ev["vehicles"]} late={ev["lateness"]:.1f} OTD={ev["otd"]:.2f}')
    seq=pd.DataFrame(seq_rows); met=pd.DataFrame(met_rows); hist=pd.concat(hist_all, ignore_index=True)
    seq.to_csv(OUT/'full_sequences_qrg_alns_ils.csv',index=False,encoding='utf-8-sig')
    met.to_csv(OUT/'scenario_metrics_qrg_alns_ils_by_date.csv',index=False,encoding='utf-8-sig')
    hist.to_csv(OUT/'qrg_alns_ils_iteration_history.csv',index=False,encoding='utf-8-sig')
    agg=pd.DataFrame([{'method':'QRG_ALNS_ILS','seed':seed,'dates':len(date_list),'stop_count':int(met.stop_count.sum()),'vehicles_used':int(met.vehicles_used.sum()),'total_distance_km':round(met.total_distance_km.sum(),4),'total_travel_time_min':round(met.total_travel_time_min.sum(),4),'total_lateness_min':round(met.total_lateness_min.sum(),4),'on_time_delivery_pct':round(100*(seq.lateness_min<=1e-9).sum()/len(seq),4)}])
    agg.to_csv(OUT/'aggregate_metrics_qrg_alns_ils.csv',index=False,encoding='utf-8-sig')
    return seq, met, hist, agg

if __name__=='__main__':
    t=time.time(); seq,met,hist,agg=run_all(n_iter=25, seed=42); print('elapsed',time.time()-t); print(agg)
