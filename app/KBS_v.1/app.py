import json
import os
import sys

# Muat Rule Base
RULE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rule_base.json")

def muat_rule_base():
    if not os.path.exists(RULE_FILE):
        print(f"[ERROR] File '{RULE_FILE}' tidak ditemukan.")
        print("Pastikan rule_base.json berada di folder yang sama dengan script ini.")
        sys.exit(1)
    with open(RULE_FILE, "r") as f:
        data = json.load(f)
    print(f"[OK] {len(data)} rule berhasil dimuat dari rule_base.json\n")
    return data

# Helpers
def cek_kondisi(nilai, kondisi):
    """Cek apakah nilai memenuhi kondisi (bisa berupa nilai exact atau range min/max)."""
    if isinstance(kondisi, dict):
        if "min" in kondisi and kondisi["min"] is not None:
            if nilai < kondisi["min"]:
                return False
        if "max" in kondisi and kondisi["max"] is not None:
            if nilai > kondisi["max"]:
                return False
        return True
    return nilai == kondisi

def hitung_sp(semester):
    """Hitung jumlah surat peringatan (SP) berdasarkan semester."""
    if semester <= 8:  return 0
    if semester <= 10: return 1
    if semester <= 12: return 2
    return 3

def hitung_semester_tidak_aktif(tab):
    """Tentukan kategori semester tidak aktif berturut (dipakai R1-R4)."""
    if tab >= 4: return 4
    return tab

# Forward Chaining
def inferensi(wm, rules):
    """Jalankan forward chaining, kembalikan rule pertama yang cocok."""
    for rule in rules:
        match = True
        for attr, kondisi in rule["conditions"].items():
            if attr not in wm:
                match = False
                break
            if not cek_kondisi(wm[attr], kondisi):
                match = False
                break
        if match:
            return rule
    return None

# Input dari User
def tanya(prompt, tipe=str, pilihan=None, min_val=None, max_val=None):
    """Minta input dari user dengan validasi."""
    while True:
        try:
            raw = input(prompt).strip()
            if not raw:
                print("  Input tidak boleh kosong.")
                continue

            nilai = tipe(raw)

            if pilihan and nilai not in pilihan:
                print(f"  Pilih salah satu: {', '.join(str(p) for p in pilihan)}")
                continue
            if min_val is not None and nilai < min_val:
                print(f"  Input tidak valid. Nilai minimal: {min_val}")
                continue
            if max_val is not None and nilai > max_val:
                print(f"  Input tidak valid. Nilai maksimal: {max_val}")
                continue

            return nilai

        except ValueError:
            print(f"  Input tidak valid. Masukkan tipe {tipe.__name__}.")

def kumpulkan_input():
    """Kumpulkan semua data yang diperlukan dari user."""
    print("=" * 55)
    print("  RISIKO GAGAL STUDI MAHASISWA INFORMATIKA UKDW")
    print("  Metode: Forward Chaining | Rule Base: 51 Rules")
    print("=" * 55)
    print()

    data = {}

    print("  --- Kondisi Kualitatif ---")

    data["status_keuangan_bermasalah"] = tanya(
        "  Status keuangan bermasalah? (Ya/Tidak): ",
        pilihan=["Ya", "Tidak"]
    )

    data["sanksi_akademik"] = tanya(
        "  Sanksi akademik?\n"
        "    [1] Tidak Ada\n"
        "    [2] Skors\n"
        "    [3] Tindak Kriminal\n"
        "  Pilih (1/2/3): ",
        tipe=int,
        pilihan=[1, 2, 3]
    )
    data["sanksi_akademik"] = {1: "Tidak Ada", 2: "Skors", 3: "Tindak Kriminal"}[data["sanksi_akademik"]]

    print()
    print("  --- Data Akademik ---")

    data["semester"] = tanya(
        "  Jumlah semester yang telah ditempuh (4-14): ",
        tipe=int, min_val=4, max_val=14
    )

    data["ipk"] = tanya(
        "  IPK saat ini (0.00 - 4.00): ",
        tipe=float, min_val=0.0, max_val=4.0
    )

    tab = tanya(
        "  Jumlah semester tidak aktif berturut-turut: ",
        tipe=int, min_val=0, max_val=14
    )

    data["mk_wajib"] = tanya(
        "  Jumlah MK wajib yang sudah lulus (0-36): ",
        tipe=int, min_val=0, max_val=36
    )

    data["mk_profil"] = tanya(
        "  Jumlah MK pilihan wajib profil yang sudah lulus: ",
        tipe=int, min_val=0
    )

    data["mk_prodi"] = tanya(
        "  Jumlah MK pilihan bebas prodi yang sudah lulus: ",
        tipe=int, min_val=0
    )

    data["mk_nonbidang"] = tanya(
        "  Jumlah MK pilihan bebas non-bidang (0-3): ",
        tipe=int, min_val=0, max_val=3
    )

    jumlah_sp            = hitung_sp(data["semester"])
    total_mk_pilihan     = data["mk_profil"] + data["mk_prodi"] + data["mk_nonbidang"]
    total_matkul         = data["mk_wajib"] + total_mk_pilihan
    semester_tidak_aktif = hitung_semester_tidak_aktif(tab)
    tidak_aktif_berturut = "Ya" if tab >= 2 else "Tidak"

    wm = {
        "status_keuangan_bermasalah":    data["status_keuangan_bermasalah"],
        "sanksi_akademik":               data["sanksi_akademik"],
        "semester_tidak_aktif_berturut": tab,
        "semester_tidak_aktif":          semester_tidak_aktif,
        "tidak_aktif_berturut":          tidak_aktif_berturut,
        "jumlah_sp":                     jumlah_sp,
        "ipk":                           data["ipk"],
        "jmlh_matkul_wajib":             data["mk_wajib"],
        "total_matkul":                  total_matkul,
        "semester":                      data["semester"],
    }

    derived = {
        "Jumlah SP"        : jumlah_sp,
        "Total MK Pilihan" : total_mk_pilihan,
        "Total MK"         : total_matkul,
    }

    return wm, derived

# Tampilkan Hasil
DESKRIPSI = {
    "Tinggi": (
        "Mahasiswa ini terindikasi BERISIKO TINGGI untuk gagal studi.\n"
        "Diperlukan intervensi segera dari pihak akademik, bimbingan\n"
        "konseling, dan evaluasi menyeluruh terhadap kondisi akademik\n"
        "maupun non-akademik."
    ),
    "Sedang": (
        "Mahasiswa ini berada pada tingkat RISIKO SEDANG.\n"
        "Perlu perhatian dan pembinaan dari dosen pembimbing akademik\n"
        "untuk mencegah penurunan performa lebih lanjut."
    ),
    "Rendah": (
        "Mahasiswa ini berada pada tingkat RISIKO RENDAH.\n"
        "Kondisi akademik masih dalam batas yang baik. Tetap diperlukan\n"
        "pemantauan berkala untuk menjaga performa."
    ),
}

def tampilkan_hasil(rule, derived):
    risiko = rule["risiko"] if rule else "Tidak Terklasifikasi"
    rule_id = rule["id"] if rule else "-"

    print()
    print("=" * 55)
    print("  HASIL INFERENSI")
    print("=" * 55)
    print()
    print(f"  Rule yang terpicu : {rule_id}")
    print(f"  Tingkat Risiko    : {risiko.upper()}")
    print()

    if risiko in DESKRIPSI:
        for baris in DESKRIPSI[risiko].split("\n"):
            print(f"  {baris}")
    else:
        print("  Data tidak cocok dengan rule manapun dalam basis")
        print("  pengetahuan. Periksa kembali kelengkapan data.")

    print()
    print("  --- Nilai Turunan ---")
    for k, v in derived.items():
        print(f"  {k:<20}: {v}")
    print()
    print("=" * 55)

# Entry Point
def main():
    rules = muat_rule_base()

    while True:
        try:
            wm, derived = kumpulkan_input()
            rule = inferensi(wm, rules)
            tampilkan_hasil(rule, derived)
        except KeyboardInterrupt:
            print("\n\nProgram dihentikan.")
            break

        print()
        lagi = input("Periksa mahasiswa lain? (ya/tidak): ").strip().lower()
        if lagi not in ["ya", "y"]:
            print("Program selesai.")
            break
        print()

if __name__ == "__main__":
    main()
