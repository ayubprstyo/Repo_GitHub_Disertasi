DT-RoMon v3 (dashboard). Buka DT_RoMon_v3.html di peramban (perlu internet untuk peta dan garis jalan), lalu pilih routes_v3_anonim.json dan s5_blocks.json.
Tab: Ringkasan S0-S4 (63 tanggal), Peta dan urutan rute (pilih S0-S4 per hari, urutan, jam tiba, linimasa), Koreksi S5 (rute NR=S4 dan koreksi FR/RG/SA).
Data anonim: kode pelanggan diganti, nama dihapus, koordinat diacak sekitar 0,4-1 km. Jam tiba memakai evaluasi sendiri tiap skenario (matriks skenario itu).
Total tiap skenario cocok dengan Bab IV (S4 = rute terkunci S5, identik untuk 63 tanggal).

PEMBARUAN v3.1 (jam tiba dan linimasa pada tab Koreksi S5)
- routes_v3_anonim.json kini memuat jam tiba tiap stop untuk NR, FR, RG, SA pada setiap blok (days[INSTANCE_k].t) serta jendela waktu dan waktu layanan tiap stop (nodes[].a, .b, .s).
- Jam tiba dihitung ulang dengan aturan simulator IJIES (src/simulator.py): berangkat dari depo 08:00, prefiks beku pada p50, sisa rute pada p85 (p50 x 1,1559) atau p95 (p50 x 1,2935), atau p50 dengan jeda 20/30 menit di batas stop beku.
- Verifikasi: total lateness dan jarak hasil hitung ulang dicocokkan dengan nr_fr_rg_sa_block_level.csv pada 7.344 blok (51 instance x 3 pemicu x 4 gangguan x 3 seed x 4 metode); selisih terbesar 5,7e-14 menit.
- Matriks waktu tempuh tidak disertakan; hanya jam tiba hasil simulasi, sehingga geometri jalan asli tidak terbuka.
- Ini replay pada tingkat Digital Model, bukan routing real-time.

v3.2: simulasi replay pada tab Koreksi S5 (tombol Putar, penggeser jam, kecepatan 6/15/40 menit per detik). Posisi kendaraan diinterpolasi lurus antar stop menurut jam tiba dan jam berangkat hasil simulasi IJIES, jadi hanya perkiraan; bukan GPS dan bukan real-time. Penghitung "terlayani/terlambat/lateness berjalan" memakai jam tiba yang sama dengan linimasa.

v3.3 (final): tab "Per tanggal" (63 hari x S0-S4, 8 metrik, urut dan cari, baris total tepat dari agregat Bab IV); kartu "Sebaran per blok" di tab Koreksi S5 (membaik/sama/memburuk terhadap NR pada 1.836 blok per metode); banner data anonim pada tab peta.

v3.4: tab "Per tanggal" dirancang ulang sebagai dashboard (pilihan 8 metrik, grafik tren per hari dengan kursor, jumlah hari terbaik per skenario, statistik ringkas, tabel berwarna menurut peringkat pada hari itu). Tab "Ringkasan S0-S4" menambah peta trade-off (lateness tolok ukur p50/p85/p95 terhadap kendaraan-hari atau jarak, dengan garis skenario yang tidak didominasi) dan matriks peringkat per metrik. Keduanya deskriptif; tidak menyatakan S4 unggul.

v3.5: kartu "Utilisasi muatan per rute" pada Ringkasan S0-S4. routes_v3_anonim.json memuat meta.util (sebaran utilisasi volume per rute, rata-rata dan median, utilisasi berat, ruang kosong) yang dihitung dari rute terbaik tiap tanggal dan permintaan per stop (aturan pemecahan stop IJIES). Gunakan JSON dan HTML versi ini bersama.

v3.6: kartu 'Kondisi normal dan kondisi stres' (OTD p50, p85, p95 dan selisih S3 terhadap S4) pada Ringkasan; catatan tab S5 bahwa hasil S5 adalah NR terhadap FR/RG/SA pada rute S4 dan tidak dibandingkan dengan S2/S3.
