import functions.Imports as imp
import functions.ReadAndWriteFiles as readWriteFile
import functions.Imdb_SQLite as SQL

def queryMovies():
    urls_list = []
    titles_list = []

    cookies = {'_session' : '{put_here_your_tracker}'}

    page = 1
    acabou = 0

    while acabou == 0:
        url = f'https://www.belasartesalacarte.com.br/my-list?page={page}'
        site = imp.requests.get(url, cookies = cookies)

        soup = imp.BeautifulSoup(site.content, 'html.parser')

        movies = soup.find_all('div', class_= 'browse-item-card')

        if movies == []:
            acabou = 1
        else:
            urls_list_1 = allMovies(movies,urls_list,titles_list)
            urls_list = urls_list_1
            page = page + 1

    return urls_list_1 

def allMovies(movies,urls_list,titles_list):
       
    for i in range(0,len(movies)):

        title= movies[i].find('strong').get_text().strip()
        ur = movies[i].find('a')
        ur = str(ur)
        index1 = ur.find('https://www.')
        index2 = ur.find('>')-1
        
        if title not in titles_list:
            titles_list.append(title)
            urls_list.append({'title':title,"url":ur[index1:index2]})
    
    return(urls_list)


def findOriginalTitle(urls_list):
    
    original_title_name = []
    new_movies_list = []
    
    for url_title in urls_list:
        
        url = url_title['url']
        site = imp.requests.get(f'{url}')
        soup = imp.BeautifulSoup(site.content, 'html.parser')
        
        try:
            original_title = soup.find('div', class_= 'contain padding-top-medium collection-description word-break').get_text().strip()

        except:
            try:
                original_title = soup.find('section', class_= ' text site-font-secondary-color site-link-primary-color-contain read-more-wrap').get_text().strip()   
            
            except:
                original_title = soup.find('section', class_= 'contain column small-16 margin-top-large').get_text().strip()

        if original_title not in original_title_name:
            original_title_name.append(original_title)
            indexs = [i for i in range(0,len(original_title)) if original_title[i] == '|']
           
            out =0
            ind=0
            while out == 0 and ind < len(indexs):
                if original_title[indexs[ind] + 1] != " ":
                    index_year_start = indexs[ind] + 1
                    index_year_final = indexs[ind] + 5

                else:
                    i = 1
                    while original_title[indexs[ind] + i] == " ":
                        index_year_start = indexs[ind] + i + 1
                        index_year_final = indexs[ind] + i + 5
                        i = i + 1

                try: 
                    int(original_title[index_year_start: index_year_final])
                    if original_title[index_year_start: index_year_final][3] != " ":
                        out = 1
                    else:
                        ind = ind + 1
                except:
                    ind = ind + 1
                        
            
            title_name = original_title[:indexs[0]-1]
            
            title = normalizeTitle(title_name)            
            
            new_movies_list.append({'portuguese_title':url_title['title'],
                                     'original_title':title,
                                     'year':original_title[index_year_start: index_year_final]})

    return new_movies_list


def normalizeTitle(title_name):
    
    title_name = title_name.upper()
    
    index= title_name.find("/")
    
    if index != -1:
        if title_name[index+1] == " ":
            title_name =title_name[index+2:]
        else: title_name = title_name[index+1:]
    
    replace = {"'":"","  ":" ","’":"","´":""}
    
    for key, value in replace.items():
        title_name= title_name.replace(key,value)
        
    return title_name


def updateMovieList(file_name):
    
    try:
        query_movies = readWriteFile.readFile(file_name)

        new_query_movies = queryMovies()
        
        new_titles = []
        titles_list = []
        
        for movie in new_query_movies:
            titles_list.append(movie['title'])

        for movie in query_movies: 
            if movie['portuguese_title'] not in titles_list:
                query_movies.remove(movie)

        titles_list = []
        for movie in query_movies:
            titles_list.append(movie['portuguese_title'])

        for movie in reversed(new_query_movies):
            if movie['title'] not in titles_list:          
                new_titles.append(movie)
               
        new_title_list = findOriginalTitle(new_titles)
      
        for movie in new_title_list:
            query_movies.insert(0,movie)
            
        readWriteFile.saveFile(query_movies,file_name)
 
    except:

        first_query = queryMovies()
        query_movies = findOriginalTitle(first_query)
        readWriteFile.saveFile(query_movies,file_name)
      
    print("List of movies updated (added and removed)")
    
    return query_movies


def updateIDList(file_name):
    new_query_movies = readWriteFile.readFile(file_name)
    titles_not_found = []

    for title in new_query_movies:
        find_id = str(title.keys()).find('id')

        if find_id == (-1) or title['id'] == '0000000000':

            query_movie = f"""SELECT * FROM titles WHERE UPPER(REPLACE(REPLACE(original_title,"'",""),",","")) \
                              LIKE '%{title['original_title']}%' \
                              AND premiered = {title['year']} \
                              AND type = 'movie' OR 'tvMovie'"""

            table_movie = imp.pd.read_sql_query(query_movie, SQL.conn)

            if len(table_movie) == 0:
                title, titles_not_found = lookForDifferentType(title,titles_not_found)

            elif len(table_movie) == 1:
                    title_id = table_movie['title_id'].values[0]
                    title.update({'id':title_id})

            else:
                query_movie = f"""SELECT * FROM titles WHERE UPPER(REPLACE(REPLACE(original_title,"'",""),",","")) \
                              = '{title['original_title']}' \
                              AND premiered = {title['year']} \
                              AND type = 'movie' OR 'tvMovie'"""

                table_movie = imp.pd.read_sql_query(query_movie, SQL.conn)


                if len(table_movie) == 1:
                    title_id = table_movie['title_id'].values[0]
                    title.update({'id':title_id})

                else: 
                    title, titles_not_found = lookForDifferentType(title,titles_not_found)

    if len(titles_not_found) != 0:
        for title in titles_not_found:
            print("Title not found:",title)
            

    print("IDs list uptaded")
    
    readWriteFile.saveFile(new_query_movies, file_name)
    
    return new_query_movies,titles_not_found


def lookForDifferentType(title,titles_not_found):
        
    query_movie = f"""SELECT * FROM titles WHERE REPLACE(REPLACE(original_title,"'",""),",","") \
                      LIKE '%{title['original_title'].lower()}%' \
                      AND premiered = {title['year']} """

    table_movie = imp.pd.read_sql_query(query_movie, SQL.conn)

    if len(table_movie) == 0:
        try:
            title, titles_not_found = apiRequest(title,titles_not_found)
        except:
            print("Maybe the name of the title is wrong")
            print(title)
            
            title.update({'id':'0000000000'})
            titles_not_found.append(title)
            
    elif len(table_movie) == 1:
            title_id = table_movie['title_id'].values[0]
            title.update({'id':title_id})

    else:
        query_movie = f"""SELECT * FROM titles WHERE UPPER(REPLACE(REPLACE(original_title,"'",""),",","")) \
                      = '{title['original_title']}' \
                      AND premiered = {title['year']} """

        table_movie = imp.pd.read_sql_query(query_movie, SQL.conn)


        if len(table_movie) == 1:
            title_id = table_movie['title_id'].values[0]
            title.update({'id':title_id})

        else: 
            try:
                title, titles_not_found = apiRequest(title,titles_not_found)
            except:
                print("Maybe the name of the title is wrong")
                print(title)
                
                title.update({'id':'0000000000'})
                titles_not_found.append(title)

    return title,titles_not_found

def apiRequest(title,titles_not_found):

    ids_list = []

    if title not in titles_not_found:

            title_name = title["original_title"]
            year = title["year"]


            url = imp.requests.get(f'https://imdb-api.com/en/API/SearchTitle/{API_KEY}/{title_name} {year}')
            results = url.json().get("results")

            if results != []:
                if len(results) == 1:
                    id_original = results[0]['id']           
                    title.update({"id":id_original})

                else:
                    for i in results:
                        if i['description'].strip()[1:5] == f"{year}":
                            title_name = normalizeTitle(['title'])
                            ids_list.append((i['id'],title_name))

                    if len(ids_list) == 1:
                        title.update({'id':ids_list[0][0]})
                    else:
                        for i in ids_list:
                            if(i[1] == title_name):
                                title.update({'id':i[0]})

                find_id = str(title.keys()).find('id')

                if find_id == (-1):
                    if title not in titles_not_found:
                            title.update({'id':'0000000000'})
                            titles_not_found.append(title)

            else:
                if title not in titles_not_found:
                    title.update({'id':'0000000000'})
                    titles_not_found.append(title)
                            
    return title, titles_not_found

def updateRatingVotesList(file_name):
    
    new_query_movies = readWriteFile.readFile(file_name)

    for title in new_query_movies:
        find_id = str(title.keys()).find('id')
        find_rating = str(title.keys()).find('rating')
        if find_id != (-1):
            if find_rating == (-1) or title['rating'] == '0':

                query_movie = f"""SELECT * FROM ratings WHERE title_id = '{title['id']}'"""

                table_movie = imp.pd.read_sql_query(query_movie, SQL.conn)

                if len(table_movie) == 1:
                    rating = table_movie['rating'].values[0]
                    votes = table_movie['votes'].values[0]

                    title.update({'rating': f'{rating}', 
                                   'votes': f'{votes}'})
                else:
                    title.update({'rating': '0', 
                                   'votes': '0'})
                    print('!'*100)
                    print("Ratings and Votes not found for: ",title)
                    print('!'*100)
                 
        else:
            print("ID not found for:",title)
            
    print('Rating and votes list uptaded')
    

    readWriteFile.saveFile(new_query_movies,file_name)


def modifyInfoTitle(title, info_correta, file_name, kind = "name"):
    
    new_query_movies = readWriteFile.readFile(file_name)
    
    try:
        index = new_query_movies.index(title)
        final = 'Title successfully updated!'

        if kind == 'name':
            new_query_movies[index].update({'original_title':info_correta})

        elif kind == 'year':
            new_query_movies[index].update({'year':info_correta})

        elif kind == 'id':
            new_query_movies[index].update({'id':info_correta})

        elif kind == 'rating':
            new_query_movies[index].update({'rating':info_correta})

        elif kind == 'votes':
            new_query_movies[index].update({'votes':info_correta})

        else:
            final = 'Invalid Type!'
        
        print(final)
        
        if final != 'Invalid Type!':
            print("title:", new_query_movies[index])
    
    except:
        print("Title not found")
        
    readWriteFile.saveFile(new_query_movies,file_name)



def sortList(file_name):
    oldlist = readWriteFile.readFile(file_name)
   
    newlist = sorted(oldlist, key=lambda r: r['rating'],reverse=True) 
    
    readWriteFile.saveFile(newlist,file_name,kind='df')
    readWriteFile.saveFile(newlist,file_name)

    print("Titles list sort by rating")
    return newlist


def uptadeTilesList(file_name):
    
    updateMovieList(file_name)
    updateIDList(file_name)
    updateRatingVotesList(file_name)
    sortList(file_name)
    
    print('-'*100)
    print("Completed Process")

