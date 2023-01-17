import functions.Imports as imp

conn = imp.sqlite3.connect("imdb.db")

def howImdbTablesAreOrganized():
    
    conn = imp.sqlite3.connect("imdb.db")
    tabels = imp.pd.read_sql_query("SELECT NAME AS 'Table_Name' FROM sqlite_master WHERE type = 'table'", conn)

    tabels = tabels["Table_Name"].values.tolist()

    dict_tabel = {}

    for tabel in tabels:

        query = "PRAGMA TABLE_INFO({})".format(tabel)
        result = imp.pd.read_sql_query(query, conn)
        dict_tabel.update({tabel:result})

        print(tabel)
        display(result)
      
        
        print("-"*100)
        print("\n")