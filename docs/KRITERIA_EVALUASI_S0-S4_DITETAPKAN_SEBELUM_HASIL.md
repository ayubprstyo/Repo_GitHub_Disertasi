# Kriteria evaluasi S0-S4 (ditetapkan 2026-10-14 sebelum hasil S0-S3 selesai)

Disetujui penulis (Ayub Prasetyo) pada 2026-10-14. Tidak boleh diubah setelah hasil dilihat.

Pipeline: kode notebook QRG_ALNS_ILS_S4_S5_v5 (S0-S3 dengan fungsi run_s0_s4_scenarios, konfigurasi identik dengan S4 terkunci):
seed 11/22/33, 80 iterasi, 20 local-search trials, early stop 20, penalti buka kendaraan 1.000, maks 10 rute/hari,
batas selesai 18.00, split stop oversize. Rute terbaik per tanggal = objektif terendah antar seed (aturan pipeline).
S4 = s4_routes_best.csv (terkunci; direproduksi persis pada 2024-03-01 seed 33).

Yardstick bersama (semua skenario dievaluasi pada rute masing-masing):
 - p50 tetap, p85 tetap, p95 tetap (matriks saved matrix), ditambah evaluasi "own" sesuai laporan pipeline.

Kriteria "lebih baik" (S4 dibanding tiap S0, S1, S2, S3):
 1. Reliabilitas: total lateness dan OTD di bawah p50, p85, p95.
 2. Efisiensi: jarak total dan jumlah kendaraan-hari.
 3. Konsistensi: Wilcoxon berpasangan per tanggal (n=63), koreksi Holm atas seluruh perbandingan; laporkan menang/kalah/seri dan selisih median.
 4. Klaim "S4 lebih baik" hanya untuk metrik yang unggul konsisten dan signifikan; sisanya ditulis sebagai trade-off.
Tidak ada penyetelan parameter setelah melihat hasil.
