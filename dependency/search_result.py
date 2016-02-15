import json

class SearchResult:
    '''
    This class is designed to restore and display every item
    of search results.
    '''

    def __init__(self):
        self.url = ''
        self.title = ''
        self.content = ''

    def getURL(self):
        return self.url

    def setURL(self, url):
        self.url = url

    def getTitle(self):
        return self.title

    def setTitle(self, title):
        self.title = title

    def getContent(self):
        return self.content

    def setContent(self, content):
        self.content = content

    def printIt(self, prefix=''):
        print 'url\t->', self.url
        print 'title\t->', self.title
        print 'content\t->', self.content

    def writeFile_json(self, filename):
        file = open(filename, 'a')
        result_dict = {'url':self.url,'title':self.title,'content':self.content}
        result_json = json.dumps(result_dict,ensure_ascii=False,indent=2)
        try:
            file.write(result_json)
        except IOError as e:
            print 'file error:', e
        finally:
            file.close()
    def writeFile_txt(self, filename):
        file = open(filename, 'a')
        result = self.url + '\n'
        try:
            file.write(result)
        except IOError as e:
            print 'file error:', e
        finally:
            file.close()