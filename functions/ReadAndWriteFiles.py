import functions.Imports as imp

def saveFile(list_or_df, file_name, kind = 'list'):
    
    if kind == 'list':
        with open(f'files/{file_name}.txt', mode='w') as file:
            imp.json.dump(list_or_df, file)
            
    else:
        df = imp.pd.DataFrame(list_or_df)
        df.to_excel(f'files/{file_name}.xlsx', index=False)
        
def readFile(file_name): 
    
    with open(f"files/{file_name}.txt", "r") as file:
        lines = file.read()

    new_list = imp.json.loads(lines)

    return new_list