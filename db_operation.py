import sqlite3

conn = sqlite3.connect('transactions.db')

cursor = conn.cursor()

# cursor.execute('''
#                    DROP TABLE transactions;           
#                ''')

# cursor.execute('''
               
               
#     CREATE TABLE transactions (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         start_date TEXT,
#         end_date TEXT,
#         INCOME REAL,
#         TRANSFER_IN REAL,
#         TRANSFER_OUT REAL,
#         LOAN_PAYMENTS REAL,
#         BANK_FEES REAL,
#         ENTERTAINMENT REAL,
#         FOOD_AND_DRINK REAL,
#         GENERAL_MERCHANDISE REAL,
#         HOME_IMPROVEMENT REAL,
#         MEDICAL REAL,
#         PERSONAL_CARE REAL,
#         GENERAL_SERVICES REAL,
#         GOVERNMENT_AND_NON_PROFIT REAL,
#         TRANSPORTATION REAL,
#         TRAVEL REAL,
#         RENT_AND_UTILITIES REAL,
#         PAYMENT REAL,
#         TRANSFER REAL,
#         RECREATION REAL,
#         TOTAL REAL
#         );
# ''')

# cursor.execute('''
# ALTER TABLE transactions
# ADD COLUMN RECREATION REAL
# ''')

cursor.execute('''
DELETE FROM sqlite_sequence WHERE name='transactions'
''')

conn.commit()


conn.close()