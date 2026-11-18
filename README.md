# MCR - The Black Parade: Pepe The Drum Major (ASCII Art Animation)

Animasi seni ASCII interaktif bertema gelap (*Dark Gothic Aesthetic*) menggunakan **Pygame**, menampilkan maskot legendaris **Pepe the Drum Major** dari album *The Black Parade* oleh **My Chemical Romance**.

---

## 🌟 Fitur Utama

- **Detail Tinggi & Palet Asli (152×124 Grid, 4.007 Karakter ASCII):**
  - Seragam hitam *charcoal* khas The Black Parade dengan kontur tepi dingin (*dual-rim lighting*).
  - Tengkorak & tangan gading tua (*aged gothic bone*) dengan rongga mata gelap.
  - Kepang dada perak (*frogging ribs*) dengan efek kilau berjalan (*travelling glint*).
- **Ujung Mayoret Kuning Keemasan (*Golden Baton & Mace*):**
  - Kepala gada bawah (*mace bulb*) dan pucuk atas tongkat mayoret memancarkan cahaya kuning keemasan terang dengan halo berputar dan percikan komet.
- **Bulan Sabit Bersinar (*Radiant Crescent Moon*):**
  - Bulan sabit dengan *additive bloom glow*, 3 cincin halo konsentris, serta berkas sinar bulan (*moonbeams*) yang menyorot ke arah Pepe.
- **Transisi Masuk Bergaya Black Hole & Gerakan Langkah Berwibawa:**
  - Siluet menggambar diri sendiri memutar $\rightarrow$ riak energi dari dada $\rightarrow$ gelombang kejut (*shockwave ring*) $\rightarrow$ gerakan langkah tegap tentara (*0.36 Hz*) yang tenang dan halus.
- **Kembang Api ASCII Bervariasi (Detik 20 ke Atas):**
  - Variasi ketinggian (*rendah, sedang, tinggi*) dan ukuran ledakan (*kecil, sedang, besar*).
  - Dilengkapi **Pelindung Siluet Pepe (*2D Distance Transform*)** agar kembang api meledak di belakang siluet dan tidak pernah menutupi karakter ASCII.

---

## 🎮 Kontrol Keyboard

| Tombol | Fungsi |
|---|---|
| **F11** | Ganti layar penuh (*Fullscreen*) / Jendela (*Windowed*) |
| **Space** | Jeda (*Pause*) / Lanjutkan (*Resume*) |
| **R** | Ulangi animasi dari detik `0.0s` (*Restart intro reveal*) |
| **F** | Lompat langsung ke detik `20.0s` (*Uji cepat Kembang Api*) |
| **S** | Simpan tangkapan layar (*Screenshot PNG*) |
| **Esc** | Keluar dari aplikasi |

---

## 🚀 Cara Menjalankan

### Persyaratan
- Python 3.10+
- Pygame (`pip install pygame`)

### Menjalankan
Klik ganda file `run_mcr.bat` atau jalankan via terminal:
```bash
python mcr.py
```
*(Atau menggunakan path Python spesifik jika diperlukan)*
