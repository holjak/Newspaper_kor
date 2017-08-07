from newspaper import Article
from selenium import webdriver
from bs4 import BeautifulSoup
import urllib.request
import time
import re



day = 11

while day < 16:
    flag = 0
    naverNews = []
    daumNews = []
    strDay = ''
    if day < 10:
        strDay = '0' + str(day)
    else:
        strDay = str(day)
    day += 1
    print (str(day-1) + '일')
    search_index = 1
    i = 0

    while 1:
        search_index = i*10 + 1
        i += 1
        #네이버링크 만들기
        targetlink1 = 'https://search.naver.com/search.naver?ie=utf8&where=news&query='
        search_keyword = '%EC%9C%A1%EC%95%84%EC%A2%85%ED%95%A9%EC%A7%80%EC%9B%90%EC%84%BC%ED%84%B0'
        targetlink2 = '&sm=tab_pge&sort=0&photo=0&field=0&reporter_article=&pd=3&ds=2017.07.'+ strDay +'&de=2017.07.'+ strDay +'&docid=&nso=so:r,p:from201707'+strDay+'to201707' + strDay +',a:all&mynews=0&cluster_rank=0&start='
        targetlink3 = '&refresh_start=0'
        naverURL = targetlink1 + search_keyword + targetlink2 + str(search_index) + targetlink3
        #네이버 검색결과 긁어오기
        dataNaver = urllib.request.urlopen(naverURL).read()
        bs1 = BeautifulSoup(dataNaver, 'html.parser')

        #검색결과의 갯수 파싱
        index_div = bs1.findAll('div', {'class','title_desc all_my'})
        index_span = index_div[0].findAll('span')
        index_num = str(index_span[0].text)
        numbers = re.findall("\d+", index_num)

        naver_list = bs1.findAll('a', {'class', '_sp_each_title'})
        print(naverURL)
        #검색결과 링크 리스트 만들기
        for l in naver_list:
            naverNews.append(l.get('href'))

        if search_index+10 > int(numbers[2]):
            break


    #인덱스 초기화
    search_index = 1
    i = 0
    flag = 0
    while 1:
        search_index = 1 + i
        i += 1
        #다음링크만들기
        link1 = 'http://search.daum.net/search?w=news&nil_search=btn&DA=PGD&enc=utf8&cluster=y&cluster_page=1&q='
        search_keyword = '%EC%9C%A1%EC%95%84+%EC%A2%85%ED%95%A9%EC%A7%80%EC%9B%90%EC%84%BC%ED%84%B0'
        link2 = '&sd=201707'+ strDay +'000000&ed=201707'+ strDay +'235959&period=u&p='
        daumURL = link1 + search_keyword + link2 + str(search_index)

        print(daumURL)
        #다음은 request로 할 시 빈페이지를 리턴하므로 가상브라우저로 긁음
        if search_index == 1:
            driver = webdriver.Chrome(executable_path="C:/Program Files (x86)/Google/Chrome/Application/chromedriver1")
            driver.implicitly_wait(1)
        driver.get(daumURL)
        driver.implicitly_wait(1)
        #다음 뉴스목록 긁기
        daum_list = driver.find_elements_by_class_name('f_link_b')

        #뉴스 갯수 긁기

        index_span = driver.find_elements_by_id('resultCntArea')
        #print(index_span[0].text)
        numbers = re.findall("\d+", index_span[0].text)

        #검색 목록 리스트 만들기
        for l in daum_list:
            #if l.get('href') == daumNews[0]:
            #    break #딱 목록이 10개인 경우 첫 링크가 같은지를 조사
            daumNews.append(l.get_attribute('href'))

        if (search_index)*10 > int(numbers[2]):
            break

    #다음네이버 링크를 하나의 리스트로 합치기
    urlList = []
    urlList = naverNews + daumNews

    print(len(urlList))
    li = list(set(urlList))
    print(len(li))

    f = open(strDay + "NewsPaper_.csv", 'w')

    for l in li:
        article = Article(l)

        article.download()
        time.sleep(1)
        article.html
        article.parse()

        f.write("<url>  ")
        f.write(l)
        f.write("\n")

        f.write("<title>  ")
        for t in article.title:
            try:
                f.write(str(t))
            except:
                f.write("타이틀 에러")
        f.write("\n")

        f.write("<content>  ")
        for a in article.text:
            try:
                f.write(str(a))
            except:
                f.write("[컨텐츠 에러]")
        f.write("\n")

        f.write("<authors>  ")
        if article.authors is not None:
            for b in article.authors:
                try:
                    f.write(str(b))
                except:
                    f.write("[저자 에러]")
        f.write("\n")

        f.write("\n---------------------------------------\n")
    f.close()
    print("finish" + strDay)


