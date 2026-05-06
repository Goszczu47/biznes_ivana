import sqlite3

# Łączymy się z bazą (plik powstanie automatycznie)
conn = sqlite3.connect('warsztat.db')
c = conn.cursor()

# Tworzymy tabelę - to jak nagłówki w Excelu
c.execute('''
    CREATE TABLE IF NOT EXISTS zlecenia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        klient TEXT,
        auto TEXT,
        koszt_czesci REAL,
        koszt_podwykonawcy REAL,
        koszt_lawety REAL,
        cena_dla_klienta REAL,
        status TEXT
    )
''')

conn.commit()
conn.close()
print("Magazyn danych gotowy!")