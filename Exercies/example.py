import sqlite3

connection = sqlite3.connect("../Sham.db")
cursor = connection.cursor()

cursor.execute("SELECT * FROM events WHERE date='2088-10-15'")
rows = cursor.fetchall()
print(rows)