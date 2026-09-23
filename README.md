# MarketLens — Team 2

Implementasi **intelligence engine dan Research Relevance** berdasarkan PRD v0.3 dan kontrak unified response di [repo Team 1](https://github.com/Mighty-Phoenix-team/Team-1). Kode ini memakai data dari `GET /api/assets/{symbol}` milik Team 1. Tidak ada API key Sectors di kode Team 2.

## Status yang jujur

- **Selesai:** engine deterministik, evidence terstruktur, formula relevance, profile tersimpan di SQLite, universe Discovery yang dapat dikonfigurasi, My Assets, endpoint detail, paket structured grounding untuk explanation layer, cache respons upstream, dan fallback reasoning tanpa LLM.
- **Belum terintegrasi end-to-end:** kontrak dan fixture telah dicocokkan dengan repo Team 1, tetapi backend live dengan kredensial Sectors belum dijalankan bersama Team 2. `sample_payload_BBCA.json` identik secara isi dengan fixture di repo Team 1.
- **Belum dibuat:** frontend Next.js dan pemanggilan LLM untuk `Explain with AI`. P0 engine/API dapat berjalan tanpa LLM. Klaim “produk MVP penuh sudah selesai” saat ini tidak akurat.
- **Batas data:** sample BBCA hanya mempunyai satu observasi harga/volume dan flow. Engine menolak menyebut perubahan harga/volume dari satu titik. Foreign flow dihitung sebagai *imbalance level* pada tanggal observasi, bukan “turned positive” atau tren.

## Menjalankan

Jalankan backend Team 1 lebih dulu di port 8000 sesuai README reponya. Kunci `SECTORS_API_KEY` hanya disimpan di lingkungan backend Team 1. Lalu dari folder ini, jalankan Team 2 di terminal terpisah:

```powershell
python -m pip install -r requirements.txt
$env:MARKETLENS_ASSET_API_BASE_URL = "http://127.0.0.1:8000"
$env:MARKETLENS_DISCOVERY_UNIVERSE = "BBCA,BBRI,BMRI,TLKM,ASII"
python -m uvicorn marketlens.api:app --host 127.0.0.1 --port 8001
```

`MARKETLENS_ASSET_API_BASE_URL` adalah **origin** backend Team 1, tanpa `/api/assets`. Ticker universe di atas adalah contoh dari lima ticker yang tertulis di audit, bukan daftar yang disisipkan di kode. Sesuaikan dengan ticker yang benar-benar didukung backend. Rentang profil dibatasi 2–90 hari karena backend Team 1 menyebut maksimum histori 90 hari dari Sectors. `MARKETLENS_DB_PATH` (default `marketlens.sqlite3`) dan `MARKETLENS_CACHE_TTL_SECONDS` (default 300) opsional. Swagger tersedia di `http://127.0.0.1:8001/docs`.

Alur API:

1. `POST /api/profiles` dengan `{"sectors":["Financials"],"research_focus":["growth","market_activity"],"horizon_days":30}`.
2. `GET /api/profiles/{id}/discovery` untuk Your Relevance Findings.
3. `PUT /api/profiles/{id}/assets/BBCA` untuk menyimpan aset; ticker lain boleh dimasukkan tanpa harus tampil di Discovery.
4. `GET /api/profiles/{id}/assets` atau `GET /api/profiles/{id}/assets/BBCA/finding` untuk analisis aset memakai engine yang sama.
5. `PUT /api/profiles/{id}` mengubah riset; `DELETE /api/profiles/{id}/assets/BBCA` menghapus aset.
6. `GET /api/profiles/{id}/assets/BBCA/explanation-context` menyiapkan research profile, finding, evidence, sumber, waktu, limitations, dan batas klaim untuk layer penjelasan. Endpoint ini **tidak** memanggil LLM.

## Metode dan asumsi

Engine memakai tiga kelompok evidence terverifikasi dari audit:

| Kelompok | Metrik | Syarat | Ambang normalisasi |
|---|---|---|---:|
| Fundamental | pertumbuhan revenue, earnings, dan EPS dari company report | nilai numerik tersedia | 10% |
| Market Activity | perubahan harga, perubahan volume | dua tanggal berbeda, baseline positif | 5% harga; 50% volume |
| Investor Flow | `net_foreign_inflow / (foreign_buy_idr + foreign_sell_idr)` | satu tanggal serta buy/sell valid | 20% |

Nilai `strength` per metrik = `min(abs(value) / threshold, 1)`. Kekuatan setiap kelompok = nilai tertinggi dari metrik yang tersedia dalam kelompok tersebut. Semua magnitudo **direction-neutral**: penurunan besar tidak dinilai sebagai kualitas investasi positif. Ambang dan bobot berada di `marketlens/methodology.json`; ini asumsi metodologis MVP, belum dikalibrasi secara empiris.

`Research Relevance = 10 × [Σ(group strength × focus weight) / Σ(focus weight)] × (available groups / 3) × sector factor`, dibulatkan dua desimal. Bobot focus 1 untuk kelompok yang dipilih, 0,4 untuk lainnya; bila focus kosong, semuanya 1. Sector factor 1 bila tidak ada filter sektor atau sektor cocok, 0,5 bila tidak cocok. `horizon_days` mengatur rentang tanggal yang diminta ke Team 1; data di luar rentang seharusnya dipotong oleh backend tersebut. Sorting Discovery adalah skor menurun lalu ticker alfabetis. Aset tanpa evidence tidak ditampilkan sebagai finding Discovery.

Setiap evidence mengandung value, baseline bila relevan, periode, metode, sumber endpoint, observed timestamp bila tersedia, dan waktu retrieval. Jika sumber tidak menyertakan tanggal periode laporan keuangan, engine hanya menampilkan periode “year-over-year quarter (source supplied)” dan tidak mengarang tanggal. `limitations` meneruskan batasan Team 1 dan menambahkan keterbatasan metode. Tidak ada inferensi sebab-akibat, prediksi, atau rekomendasi transaksi.

## Batas MVP dan structured grounding

Roadmap dua dashboard tertanggal 23 September 2026 masih berupa revisi yang belum disetujui final. Arah yang dapat diterapkan sekarang: Intelligence Dashboard dan Watchlist/My Assets memakai engine yang sama; layer penjelasan menerima paket terstruktur dari endpoint `explanation-context`. Paket ini hanya berisi data terukur dan secara eksplisit menyatakan bahwa penyebab perubahan market/foreign flow belum diketahui dari evidence tersebut. LLM, bila nanti dihubungkan, harus menjelaskan paket itu tanpa mengarang penyebab atau angka.

Document Intelligence/RAG (dokumen perusahaan, embedding, vector database, retrieval), comparison antardashboard, dan historical research memory adalah pengembangan setelah dua dashboard stabil. Pilihan fokus `Stability` dan `Dividend` yang disebut di roadmap belum dimasukkan ke scoring sampai metrik pendukungnya diverifikasi dan perubahan scope disetujui.

## Kontrak yang perlu dikonfirmasi saat integrasi

- Repo Team 1 saat dicek menyediakan struktur `symbol`, `company`, `market`, `foreign_flow`, `limitations`, `source_endpoints` dan meneruskan parameter `start`/`end`. Harga/volume/flow historis harus berupa array berisi `observed_at` ISO date.
- Repo Team 1 tersedia, tetapi endpoint live dan kunci Sectors tidak tersedia di folder ini. Jalankan uji integrasi terhadap backend asli sebelum demo.
- Sample payload adalah **fixture pengujian**, bukan live market data. Jangan sajikan sebagai data aktual di UI/demo.
- Cache saat ini proses lokal. Bila beberapa worker/deployment dipakai, gunakan cache bersama bila perlu membatasi kredit secara konsisten.

## Tes

```powershell
python -m pytest -q
```
