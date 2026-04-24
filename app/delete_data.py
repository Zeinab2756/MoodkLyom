import sqlite3

conn = sqlite3.connect("moodmate.db")
cursor = conn.cursor()

# delete all rows
cursor.execute("DELETE FROM moods")

conn.commit()
conn.close()

print("✅ All moods deleted successfully")