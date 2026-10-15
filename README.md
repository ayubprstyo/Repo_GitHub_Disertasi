# Disertasi: Digital Twin-Based Risk-Aware Routing melalui Quantile Risk-Guided ALNS-ILS

Kode pendamping disertasi Ayub Prasetyo (Universitas Gunadarma; pembimbing: Sarifuddin Madenda, Ernastuti, Murni):
*Pengembangan Kerangka Digital Twin-Based Risk-Aware Routing melalui Quantile Risk-Guided ALNS-ILS untuk Time-Dependent Multi-Dimensional Capacity Vehicle Routing Problem pada Distribusi Kosmetik Perkotaan*.

> **Data konfidensial tidak disertakan.** Data order, koordinat pelanggan, dan saved matrix berasal dari distributor dan tidak dapat dipublikasikan tanpa persetujuan pemilik data. Notebook di repositori ini sudah dibersihkan dari keluaran sel. Paket `ijies_package/` menyediakan jalur reproduksi dengan data ber-identitas samar. Dashboard memakai data yang telah dianonimkan (kode pelanggan diganti, koordinat diacak sekitar 0,4 sampai 1 km, sehingga peta ilustratif).

## Peta isi

| Folder | Isi | Hasil pada naskah |
|---|---|---|
| `notebooks/1_matriks_waktu_tempuh/` | Pembentuk matriks OSRM dan TomTom, kalibrasi kuantil empiris global, contoh ilustratif peta | Bab III Sub-bab 3.6, Bab IV Sub-bab 4.3 |
| `notebooks/2_pipeline_S0-S5/v5_Two_Stage_Batched_Colab.ipynb` | Pipeline S0 sampai S4 (S4 = QRG-ALNS-ILS) dua tahap dan S5 batch; **notebook v5 utama** | Bab IV Tabel 4.19 sampai 4.28b |
| `notebooks/2_pipeline_S0-S5/v5_Upload_Only_Colab.ipynb` | Varian v5 tanpa Google Drive (unggah manual); algoritma sama | idem |
| `notebooks/2_pipeline_S0-S5/riwayat_versi_awal/` | Versi awal (v1 sampai v4, End_to_End); dipertahankan untuk jejak riwayat, digantikan v5 | tidak dipakai untuk angka final |
| `notebooks/3_solver_dan_S5/` | Solver QRG-ALNS-ILS dan paket eksperimen S5 (`s5_core.py`) | Bab III 3.12, verifikasi rute S5 terkunci |
| `src/pipeline_S0-S4/` | Kode yang dijalankan untuk rerun S0 sampai S4: `v5_lib.py` (bagian pustaka notebook v5 Two-Stage, tanpa sel eksekusi tahap), `run_scen3.py`, `agg_gen.py`, `agg_final.py`, `test_repro.py`, `run_cfg.py` | Bab IV Sub-bab 4.6 sampai 4.12 |
| `ijies_package/` | Paket reproduksibilitas IJIES (20265681): notebook 00 sampai 11 dan 99, `src/`, `configs/`, data ber-identitas samar | Bab IV Sub-bab 4.13 sampai 4.18 |
| `verifikasi_dan_dashboard/` | Skrip menghitung ulang jam tiba dengan simulator IJIES dan mencocokkan 7.344 blok, utilisasi muatan, pembangun data dashboard | Sub-bab 3.18.7, 4.19.7, Tabel 4.28c |
| `dashboard/` | DT-RoMon v3 (HTML, data anonim, keluaran blok S5) | Sub-bab 3.18.7, 4.19.7 |
| `docs/` | Kriteria evaluasi S0 sampai S4 yang ditetapkan sebelum hasil dilihat | Bab III Sub-bab 3.16 |

## Catatan penting

- `src/pipeline_S0-S4/v5_lib.py` adalah bagian pustaka dari notebook v5 Two-Stage dengan jalur berkas disesuaikan; isi algoritma tidak diubah. Notebook asli tetap ada di `notebooks/2_pipeline_S0-S5/`.
- Hasil S5 final di naskah berasal dari `ijies_package/`, bukan dari `notebooks/3_solver_dan_S5/S5_Soft_Computing_Experiment_Colab.ipynb`.
- Dashboard bekerja pada tingkat Digital Model (impor manual, tanpa telemetri) dan bukan routing real-time. Untuk menjalankan: letakkan `DT_RoMon_v3.html`, `routes_v3_anonim.json`, dan `s5_blocks.json` dalam satu folder lalu buka HTML di browser (peta memerlukan internet).
- Skrip di `verifikasi_dan_dashboard/` membaca data konfidensial dan jalur kerja relatif; sesuaikan jalur sebelum dijalankan. Skrip ini tidak dapat dijalankan tanpa data tersebut.
- Lisensi belum ditetapkan; tambahkan berkas `LICENSE` sesuai keputusan penulis dan kampus.
- Tautan ke makalah: IJIES (20265681) dan ICITISEE belum terbit; cantumkan tautan setelah tersedia.
