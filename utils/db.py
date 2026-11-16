import sqlite3
import openpyxl
import os

DB_PATH = "data/database.db"
EXCEL_PATH = "data/baza.xlsx"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kk_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stir TEXT,
            korxona TEXT,
            manzil TEXT,
            fiscal TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stir ON kk_data(stir);")
    conn.commit()
    conn.close()

def clean_str(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if s.startswith("'"):
        s = s[1:].strip()
    if s.endswith(".0"):
        s = s[:-2].strip()
    return s

def sync_excel_to_db():
    if not os.path.exists(EXCEL_PATH):
        print(f"XATOLIK: {EXCEL_PATH} fayli topilmadi!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM kk_data")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Excel fayldan ma'lumotlar bazaga yuklanmoqda, biroz kuting...")
        wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
        sheet = wb.active
        
        rows_iter = sheet.iter_rows(values_only=True)
        headers = next(rows_iter, None)
        
        fiscal_col_idx = -1
        stir_col_idx = 0
        
        if headers:
            for idx, h in enumerate(headers):
                h_str = str(h).lower() if h else ""
                if "стир" in h_str or "инн" in h_str:
                    stir_col_idx = idx
                if "фискал модул" in h_str or "фискал" in h_str:
                    fiscal_col_idx = idx
        
        batch = []
        total_added = 0
        
        for row in rows_iter:
            if not row or len(row) <= stir_col_idx:
                continue
                
            stir = clean_str(row[stir_col_idx])
            if not stir or not stir.isdigit():
                continue
                
            korxona = clean_str(row[2]) if len(row) > 2 and row[2] else "Noma'lum"
            manzil = clean_str(row[11]) if len(row) > 11 and row[11] else ""
            
            # FAFAQAT "Фискал модул рақами" ustunidan yoki qatordagi haqiqiy fiskal modulni qidiramiz
            fiscal = ""
            if fiscal_col_idx != -1 and len(row) > fiscal_col_idx:
                val = clean_str(row[fiscal_col_idx])
                # Fiskal modul formati tekshiriladi (masalan: VG, LG, UZ va hokazo harflar bilan boshlanishi kerak)
                if val and len(val) >= 10:
                    fiscal = val
            
            # Agar ustun topilmasa yoki bo'sh bo'lsa, qatordagi to'g'ri keluvchi katakni qidiramiz
            if not fiscal:
                for cell in reversed(row):
                    val = clean_str(cell)
                    # Faqatgina harf bilan boshlanib raqam bilan davom etadigan (fiskal modul formatidagi) qiymatni olamiz
                    if val and len(val) >= 10 and val[:2].isalpha() and val[2:].isdigit():
                        fiscal = val
                        break

            if fiscal:
                batch.append((stir, korxona, manzil, fiscal))
                
            if len(batch) >= 10000:
                cursor.executemany("INSERT INTO kk_data (stir, korxona, manzil, fiscal) VALUES (?, ?, ?, ?)", batch)
                conn.commit()
                total_added += len(batch)
                batch = []
                
        if batch:
            cursor.executemany("INSERT INTO kk_data (stir, korxona, manzil, fiscal) VALUES (?, ?, ?, ?)", batch)
            conn.commit()
            total_added += len(batch)
            
        wb.close()
        print(f"Muvaffaqiyatli yakunlandi! Bazaga jami {total_added} ta yozuv qo'shildi.")
        
    conn.close()

def find_fiscal_by_stir(stir: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT korxona, manzil, fiscal FROM kk_data WHERE stir = ?", (stir.strip(),))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "korxona": row[0],
            "manzil": row[1],
            "fiscal": row[2]
        })
    return results  