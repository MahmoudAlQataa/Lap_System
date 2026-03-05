###########################
# عمليات قاعدة البيانات #
###########################

import sqlite3 
from config import DB_NAME 

def getdb() :
    # فتح اتصال بقاعدة البيانات #
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_key = on")
    return conn