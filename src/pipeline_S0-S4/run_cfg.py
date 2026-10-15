import sys, json, time
sys.argv_saved=sys.argv
exec(open('v5_lib.py').read())
cid=sys.argv_saved[1]; part=sys.argv_saved[2]  # part: cal/test
th1,th2,wr=[float(x) for x in sys.argv_saved[3].split(',')]
base_cfg = S4Config(capacity_weight_kg=CAPACITY_WEIGHT_KG, capacity_volume_cm3=CAPACITY_VOLUME_CM3, depot_start_min=DEPOT_START_MIN,
    route_end_target_min=ROUTE_END_TARGET_MIN, max_routes=MAX_ROUTES_PER_DAY, w_vehicle=VEHICLE_OPENING_PENALTY, iterations=S4_ITERATIONS,
    local_search_trials=S4_LOCAL_SEARCH_TRIALS, early_stop_patience=S4_EARLY_STOP, early_stop_min_iterations=20,
    theta1_lateness_min=th1, theta2_lateness_min=th2, w_risk=wr)
import os
dates=json.load(open('sens/split.json'))['calibration' if part=='cal' else 'test']
dates=dates[int(os.environ.get('DP','0'))::int(os.environ.get('DN','1'))]
ck='sens/ck/'+cid if cid!='orig' else 'ck_all'
t0=time.time()
run_s0_s4_scenarios(repo, dates, base_cfg, {'S4':[11,22,33]}, ck, scenarios=('S4',), force_recompute=False)
print('DONE',cid,time.time()-t0)
