import mysql.connector 

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="508622",
    database="content_bot"
)
cursor = conn.cursor()

cursor.execute("INSERT INTO topics (topic) VALUE (%s)", ("My first test topic",))
conn.commit()

cursor.execute("SELECT * FROM topics")
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()    