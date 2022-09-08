import random
import json
from keras.models import load_model
from utils import tokenize, bag_of_words
import pickle
import numpy as np
import scrapy
from scrapy.crawler import CrawlerProcess
from googletrans import Translator
from flask import Flask, render_template, request, jsonify
import os

app=Flask(__name__)
location_=["Bien Hoa", "Binh Chanh", "Binh Tan", "Binh Thanh", "Can Tho", "Cau Giay", "Chuong My", "Cu Chi", "Da Nang", "Quan 12", "Quan 8", "Go Vap", "Hai Phong", "Ha Noi", "Ho Chi Minh", "Hue", "Nha Trang", "Quy Nhon", "Vung Tau"]
location_dict={
        "Biên Hòa": "Bien Hoa",
        "Bình Chánh": "Binh Chanh",
        "Bình Tân": "Binh Tan",
        "Bình Thạnh": "Binh Thanh",
        "Cần Thơ": "Can Tho",
        "Cầu Giấy": "Cau Giay",
        "Chương Mỹ": "Chuong My",
        "Củ Chi": "Cu Chi",
        "Đà Nẵng": "Da Nang",
        "Quận 12": "Quan 12",
        "Quận 8": "Quan 8",
        "Gò Vấp": "Go Vap",
        "Hải Phòng": "Hai Phong",
        "Hà Nội": "Ha Noi",
        "Thành Phố Hồ Chí Minh": "Ho Chi Minh",
        "Huế": "Hue",
        "Nha Trang": "Nha Trang",
        "Quy Nhơn": "Quy Nhon",
        "Vũng Tàu": "Vung Tau"
}

@app.route("/", methods=["POST"])
def home():
    return render_template('home.html')


class Weather(scrapy.Spider):
    name = "weather"
    start_urls = ["https://www.accuweather.com/vi/vn/vietnam-weather"]

    def parse(self, response):
        global all_weather
        all_weather = []
        for weather in response.css('div.nearby-locations-list a'):
            yield {
                'location': weather.css('span::text').get(),
                'temp': weather.css('span::text')[1].get().replace("°", "C")
            }
            all_weather.append([weather.css('span::text').get(), weather.css('span::text')[1].get().replace("°", "C")])

def get_weather():
    return get_temp('Da Nang') + " , mưa rào"

def get_temp(location):
    for l, t in all_weather:
        if location_dict[l].lower()==location.lower():
            global temp
            temp=int(t[:-1])
            return "Nhiệt độ ở "+ l + " là "+ t


with open('data.pkl', 'rb') as f:
    all_words, tags=pickle.load(f)
with open('intents.json', 'r') as f:
    data=json.load(f)

model=load_model('model.model')
translator=Translator()

def chat(sentence):
    if sentence in location_:
        pass
    sentence_=sentence
    X=tokenize(sentence_)
    X=bag_of_words(X, all_words)
    X=X.reshape(-1, len(all_words))
    prediction=model.predict(X)[0]
    predicted_tags=tags[np.argmax(prediction)]
    probability=prediction[np.argmax(prediction)]
    print(probability)
    if probability>0.7:
        for intents in data['intents']:
            if predicted_tags==intents['tag']:
                if predicted_tags=='location':
                    try:
                        return get_temp(str(sentence)) + ". Bạn đang trồng ở đâu? (Ví dụ: Ban công, vườn, tầng thượng, trong nhà)"
                    except:
                        return "Tôi không tìm được chỗ bạn"
                if predicted_tags=='plant_location':
                    if 7<=temp<=25 and sentence.lower()=='ban cong' or sentence.lower()=='trong nha':
                        return "Điều kiện của bạn thích hợp để trồng XÀ LÁCH"
                    elif 26<=temp<=35 and sentence.lower()=='vuon' or sentence.lower()=='tang thuong':
                        return "Điều kiện của bạn thích hợp để trồng RAU MUỐNG"
                    else:
                        return "Không có loại cây nào thích hợp. Hãy chọn lại chỗ trồng"
                if predicted_tags[:3]=="req":
                    for i in range(3):
                        response=intents['responses'][i]
                        response = translator.translate(response, src='en', dest='vi').text
                        return response

                if predicted_tags=='weather':
                    return get_weather()

                else:
                    response=random.choice(intents['responses'])
                    response=translator.translate(response, src='en', dest='vi').text
                    return response
    else:
        response=random.choice(data['error'])
        response = translator.translate(response, src='en', dest='vi').text
        return response

@app.route("/get", methods=["POST"])
def get_response():
    userText=str(dict(request.form)['response'])
    if os.path.exists('response.json') == True:
        pass
    else:
        with open('response.json', 'w') as f:
            _={"responses":[]}
            json.dump(_, f)
    with open('response.json', 'r') as f:
        data=json.load(f)
        temp=data['responses']
        temp.append(userText)
        print(temp)
    with open('response.json', 'w') as f:
        json.dump(data, f, indent=4)

    print(userText)
    return jsonify({"response": str(chat(userText))})

if __name__=='__main__':
    process = CrawlerProcess()
    process.crawl(Weather)
    process.start()
    app.run(host="192.168.0.89")

