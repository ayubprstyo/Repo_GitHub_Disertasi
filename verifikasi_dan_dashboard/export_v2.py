"""export_v2.py - DT-RoMon v2: ekspor (1) rute pra-dispatch terkunci (NR) dari berkas urutan arsip dan
(2) hasil blok S5 final dari CSV IJIES, untuk penampil DT_RoMon_v2.html.
Tidak ada eksperimen yang dijalankan ulang; hanya membaca berkas.
  python export_v2.py --stops customer_day_stops_preprocessed.csv --sequences full_sequences.csv \
         --blocks nr_fr_rg_sa_block_level.csv --out routes_v2.json --blocks-out s5_blocks.json [--anonymize]
Rute pra-dispatch terkunci (NR) diambil dari --sequences. Urutan koreksi FR/RG/SA diambil HANYA dari --s5-sequences (berkas pasca-perbaikan,
dicocokkan dengan moved_stops pada CSV blok final); berkas urutan pra-perbaikan tidak boleh dipakai untuk FR/RG/SA.
"""
import argparse, json
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--stops', required=True); ap.add_argument('--sequences', required=True)
ap.add_argument('--s5-sequences', help='urutan rute S5 pasca-perbaikan (51 tanggal held-out)'); ap.add_argument('--blocks'); ap.add_argument('--out', default='routes_v2.json'); ap.add_argument('--blocks-out', default='s5_blocks.json')
ap.add_argument('--anonymize', action='store_true')
ap.add_argument('--depot-lon', type=float, default=106.816403); ap.add_argument('--depot-lat', type=float, default=-6.553882)
a = ap.parse_args()
st = pd.read_csv(a.stops); sq = pd.read_csv(a.sequences); sq = sq[sq.method == 'NR']
dates = sorted(sq.delivery_date.unique()); ca = {}
def cid(c): return c if not a.anonymize else ca.setdefault(c, 'C%04d' % (len(ca)+1))
s5 = pd.read_csv(a.s5_sequences) if a.s5_sequences else None
out = {'meta': {'depot': [a.depot_lon, a.depot_lat], 'anonymized': a.anonymize}, 'days': {}}
for i, d in enumerate(dates):
    inst = 'INSTANCE_%03d' % (i+1)
    sd = st[st.delivery_date == d].set_index('customer_code'); g = sq[sq.delivery_date == d]
    ref = g[(g.trigger_fraction == 0.25) & (g['shock'] == 'p85') & (g.seed == 101)].sort_values(['vehicle_id', 'sequence'])
    ids = list(dict.fromkeys(ref.node_id)); idx = {n: j for j, n in enumerate(ids)}; nodes = []
    for n in ids:
        p = n.split('__SPLIT')[0]; sp = n.split('__SPLIT')[1] if '__SPLIT' in n else ''; r = sd.loc[p]
        nodes.append({'id': cid(p) + ('__SPLIT' + sp if sp else ''), 'lon': float(r.longitude), 'lat': float(r.latitude),
                      'w': float(r.total_weight), 'v': float(r.total_volume), 'name': '' if a.anonymize else str(r.customer_name)})
    route = {v: [idx[n] for n in y.node_id] for v, y in ref.groupby('vehicle_id')}
    frozen = {}
    for (tf, sh, sdd), y in g.groupby(['trigger_fraction', 'shock', 'seed']):
        frozen['%s|%s|%s' % (tf, sh, sdd)] = {v: int(z.served_frozen.sum()) for v, z in y.groupby('vehicle_id')}
    runs = {}
    if s5 is not None:
        h = s5[(s5.delivery_date == d) & (s5.method != 'NR')]
        for (tf, sh, sdd, m), y in h.groupby(['trigger_fraction', 'shock', 'seed', 'method']):
            runs['%s|%s|%s|%s' % (tf, sh, sdd, m)] = {v: [[idx[n] for n in z.sort_values('sequence').node_id], int(z.served_frozen.sum())] for v, z in y.groupby('vehicle_id')}
    out['days'][inst] = {'date': inst if a.anonymize else d, 'nodes': nodes, 'route': route, 'frozen': frozen, 'runs': runs}
json.dump(out, open(a.out, 'w'), separators=(',', ':')); print('ok', a.out, len(out['days']), 'hari')
if a.blocks:
    b = pd.read_csv(a.blocks); cols = ['delivery_date', 'trigger_fraction', 'shock', 'seed', 'method', 'total_distance_km', 'total_travel_time_min',
        'total_lateness_min', 'otd_num', 'otd_den', 'rsi', 'moved_stops', 'remaining_stops', 'n_harm_vehicles', 'block_fully_unchanged', 'block_any_harm']
    b = b[cols]; b['block_fully_unchanged'] = b.block_fully_unchanged.astype(int); b['block_any_harm'] = b.block_any_harm.astype(int)
    json.dump({'columns': cols, 'rows': b.values.tolist(), 'note': 'Hasil blok S5 final IJIES (51 instance held-out); rata-rata dihitung per instance lalu antar instance.'},
              open(a.blocks_out, 'w'), separators=(',', ':'), default=float); print('ok', a.blocks_out, len(b), 'blok')
