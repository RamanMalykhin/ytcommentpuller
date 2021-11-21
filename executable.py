#!/usr/bin/env python
# coding: utf-8

# In[120]:


def importandbuild():
#API package import and key input

    from googleapiclient.discovery import build
    print('Input YT API key:')
    api_key = input()

    youtube = build('youtube','v3',developerKey = api_key)
    print('API key valid, resource build successful')
    return youtube

def ytidinput():
    #video ID input
    print('Input video ID:')
    ytid = input()
    return ytid

def pullandparse(youtube, ytid):
#this will store paginated toplevel comment json dictionaries
    dictlist = []

    #this makes the initial request for toplevel comments, if there is more than 100 comments it will have a nextPageToken
    dict_output = youtube.commentThreads().list(part="snippet,replies", videoId=ytid, maxResults = 100).execute()
    dictlist.append(dict_output)
    npt = dict_output.get('nextPageToken')

    #this keeps requesting new jsons with new nextPageTokens as long as the last json requested had one
    while npt:
        dict_output = youtube.commentThreads().list(part="snippet,replies", videoId=ytid, pageToken = npt, maxResults = 100).execute()
        dictlist.append(dict_output)
        npt = dict_output.get('nextPageToken')

    #this will store the actual output
    comments = []  

    #we loop through all output jsons and enter every thread (thread = toplevel comment)
    for dict in dictlist:
        for thread in dict['items']:
            onecomment = []
            #this takes the actual text of the comment and puts it into its own little list
            #reads the number of replies to the comment too
            commenttext = thread['snippet']['topLevelComment']['snippet']['textDisplay']
            replycount = thread['snippet']['totalReplyCount']
            onecomment.append(commenttext)

            #if the toplevel comment has replies, we'll need to request them
            if replycount>0:
                targettoplevelid = thread['snippet']['topLevelComment']['id']
                replydictlist = []
                #same logic as with toplevel comments
                #request initial 100 replies, if the json came back with a nextPageToken request again
                #keep requesting until json comes back without a nextPageToken
                reply_dict_output = youtube.comments().list(part="snippet", parentId = targettoplevelid, maxResults = 100).execute()
                replydictlist.append(reply_dict_output)
                replynpt = reply_dict_output.get('nextPageToken')
                while replynpt:
                    reply_dict_output = youtube.comments().list(part="snippet", parentId = targettoplevelid, pageToken = replynpt, maxResults = 100).execute()
                    replydictlist.append(reply_dict_output)
                    replynpt = reply_dict_output.get('nextPageToken')
                #loops through reply jsons, takes the actual text of the reply and puts it into yet another list
                #I guess I really like lists
                parsedreplies = []
                for replydict in replydictlist:
                    for comment in replydict['items']:
                        parsedreplies.append(comment['snippet']['textOriginal'])
                onecomment.append(parsedreplies)
                #this appends to the output with the comment
                #the output it structured like this
                #[['top level with no replies'],['top level with replies', ['reply1','reply2']], ...]
            comments.append(onecomment)
    print('comment extraction successful')
    return comments
        
def countandtest(comments, youtube, ytid):
#testing cell - run to check if all comments were pulled

    i = 0
    j = 0
    l = 0
    for element in comments:
        if len(element) == 1:
            i += 1
        if len(element) > 1:
            j += 1
        if len(element) > 1:
            l += len(element[1])       
    script_count = i+j+l

    video_output = youtube.videos().list(part="statistics", id=ytid).execute()
    native_count = int(video_output['items'][0]['statistics']['commentCount'])

    print('N comments according to YT API: ', native_count)
    print('N comments scraped: ', script_count)

#search all comments, output matching toplevels and index in comments
def search(comments):
    import fnmatch
    print('Input search term:')
    searchterm = input()
    pattern = '*'+searchterm+'*'

    results = []
    i = -1

    for commentthread in comments:
        i += 1
        if len(commentthread) > 1:
            toplevel = commentthread[0]
            flatthread = commentthread[1]
            flatthread.append(toplevel)
            if len(fnmatch.filter(flatthread,pattern))>0:
                resulttoplevel = commentthread[0]
                numofreplies = len(commentthread[1])
                results.append([i,[resulttoplevel],numofreplies])
        else:
            if fnmatch.fnmatch(commentthread[0],pattern):
                resulttoplevel = commentthread[0]
                numofreplies = 0
                results.append([i,[resulttoplevel],numofreplies])



    print('Searched for: \"', searchterm, '\". Results follow.')
    if len(results)>0:
        i = -1
        for result in results:
            i +=1
            print('--------------')
            print('Index :', i)
            print('Top-level comment :', result[1])
            print('Replies :', result[2])
    else:
        print('--------------')
        print('No results')
        
    return results

def deepdive(comments, results):
    print('Input search result index:')
    targetindex = int(input())
    targetthread = comments[results[targetindex][0]]
    print('Top-level comment:')
    print(targetthread[0])
    print('Replies:')
    if len(targetthread[1])>0:
        for reply in targetthread[1]:
            print('--------------')
            print(reply)
    else:
        print('--------------')
        print('No replies')
        
        
from googleapiclient.errors import HttpError

class quitflag( Exception ):
    pass

#we have essentially four stages
#on each stage user can go 1 step forward, 1 step backward (except #1), or quit
#1: get API key and build the resource
#2: get video ID, pull comments and test pull
#3: search comments, show toplevels with results
#4: output desired toplevel with all responses



while True:
    try:
        print('Input \'start\' to begin, or \'quit\' to quit:')
        command = input()
        if command == 'quit':
            raise quitflag
        elif command == 'start':
            youtube = importandbuild()
            while True:
                print('Input \'next\' to pull comments, \'back\' to input new API key, or \'quit\' to quit:')
                command = input()
                if command == 'quit':
                    raise quitflag
                if command == 'back':
                    break
                elif command == 'next':
                    ytid = ytidinput()
                    try:
                        comments = pullandparse(youtube, ytid)
                        countandtest(comments, youtube, ytid)
                        while True:
                            print('Input \'next\' to search pulled comments, \'back\' to pull comments, or \'quit\' to quit:')
                            command = input()
                            if command == 'next':
                                results = search(comments)
                                while True:
                                        print('Input \'next\' to examine a specific thread, \'back\' to search again, or \'quit\' to quit:')
                                        command = input()
                                        if command == 'next':                                            
                                            try:
                                                deepdive(comments, results)
                                            except IndexError:
                                                print('Incorrect index.')
                                            except ValueError:
                                                print('Index must be an integer')      
                                        elif command == 'back':
                                            break
                                        elif command == 'quit':
                                            raise quitflag
                            elif command == 'back':
                                break
                            elif command == 'quit':
                                raise quitflag
                            else:
                                print('Input not recognized.')

                    except HttpError:
                        print('Invalid video ID.')

                else:
                    print('Input not recognized.')
            else:
                print('Input not recognized.')
    except HttpError:
        print('API key invalid, please provide valid API key')
    except quitflag:
        break

