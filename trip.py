# -*- coding: utf-8 -*-
import re
import urllib.request

from bs4 import BeautifulSoup
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from slack.web.classes import extract_json
from slack.web.classes.blocks import *

SLACK_TOKEN = 'xoxb-691611233895-689776341893-kwjXWbjNnhnpmmLzajmyfy8L'
SLACK_SIGNING_SECRET = '281042679b3063ccc449370fccf080a6'

app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)

# 크롤링한 지역 담기 위한 변수
input_dist = []

# 크롤링 함수 구현하기
def _crawl_city_chart(text):
    
    # <@U0LAN0Z89> 순천
    city = text.split()[1] + "가볼만한곳"
    print("Extraction Province : " + city)
    dist = urllib.parse.quote(city)
    places=[]

    if text in text:

        url = 'https://m.search.naver.com/search.naver?sm=mtp_hty.top&where=m&query=' + dist
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")

        places.append(":slack:" + "*   " + text.split()[1] + " 여행지 추천 명소*   "+ ":slack:\n")
        dist_url = 'https://m.search.naver.com/search.naver?where=m&query='

        # Name of Randmark
        i = 0
        for place in (soup.find_all("div", class_="info_tit")):
            i = i + 1
            dist_url = dist_url + place.find('strong', class_='tit').get_text()
            places.append("*" + str(i) + "위*" + " : " + "<" + dist_url + "|" + "*" + place.find('strong', class_='tit').get_text() + "*" + ">")
            input_dist.append(place.find('strong', class_='tit').get_text())
            dist_url = 'https://m.search.naver.com/search.naver?where=m&query='

        # Explanation of Randmark
        j = 0
        for info in (soup.find_all("div", class_="info_txt")):
            j = j + 1
            x = "          " + info.find('span', class_='txt').get_text().strip()
            places.insert((3*j-1), x)
            # HashTag
            y = info.find('div', class_='keyword_list').get_text()
            y = y.split(" ")

            arr = ("          " + "`" + y[1] + "`") + " " + ("`" + y[2] + "`") + " " + ("`" + y[3] + "`")
            places.insert((3*j), arr)

    return u'\n' .join(places)
    
def _image_extraction(text):
    
    # <@U0LAN0Z89> 순천
    city = text.split()[1] + "가볼만한곳"
    dist = urllib.parse.quote(city)

    block1 = []
    block2 = []
    
    if text in text:

        url = 'https://m.search.naver.com/search.naver?sm=mtp_hty.top&where=m&query=' + dist
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")
    
    # Image Insertion
    for pic in soup.find_all('div', class_="thumb"):
        img_block = ImageBlock(
           image_url = pic.find('img').get("data-src"),
            alt_text = "Image Loading Failed"
        )
        block1.append(img_block)

    for txt in (soup.find_all("div", class_="info_tit")):
        txt_block = SectionBlock(
           text = txt.find('strong', class_='tit').get_text()
        )
        block2.append(txt_block)

    return block1

# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]

    message = _crawl_city_chart(text)
    block = _image_extraction(text)

    slack_web_client.chat_postMessage(
        channel=channel,
        text=message
    )

    slack_web_client.chat_postMessage(
        channel=channel,
        blocks=extract_json(block)
    )

# / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"
    
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)