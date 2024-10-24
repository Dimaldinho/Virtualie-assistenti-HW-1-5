
import requests
from gtts import gTTS
from IPython.display import Audio
import json
import os

config_path = os.path.join(os.path.dirname(__file__), '..\config.json')
with open(config_path) as config_file:
    config = json.load(config_file)

NEWS_API_KEY = config['NEWS_API_KEY']
NEWS_BASE_URL = config['NEWS_BASE_URL']

WEATHER_API_KEY = config['WEATHER_API_KEY']
WEATHER_BASE_URL = config['WEATHER_BASE_URL']

QUOTE_BASE_URL = config['QUOTE_BASE_URL']

allText = ''
def get_random_quote():
    
    response = requests.get(QUOTE_BASE_URL)

    if response.status_code == 200:
        data = response.json()
        
        quoteData = data[0]['q']  
        authorData = data[0]['a'] 
        quote = quoteData + ' - ' + authorData + '\n'
        print(quote)
        return quote
        
    else:
        print("Error fetching quote data:", response.status_code)

def get_weather(city, aqi='no'):
    params = {
        'key': WEATHER_API_KEY,
        'q': city,
        'aqi': aqi
    }
    response = requests.get(WEATHER_BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        location = data['location']
        current = data['current']
        
        weather = f"Weather: Temperature: {current['temp_c']}°C, Condition: {current['condition']['text']}, Humidity: {current['humidity']}%\n"
        print(weather)
        return weather 
    else:
        print("Error fetching weather data:", response.status_code)
        return ''

def get_top_headlines(country='lv', category='general'):
    #Params for news
    params = {
        'apiKey': NEWS_API_KEY,   
        'country': country,  
        'category': category,  
        'pageSize': 1
    }

    response = requests.get(NEWS_BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
        
        if articles:
            soundOutput = f"Top {category.capitalize()} News Headlines in {country.upper()}:\n"
            print(f"Top {category.capitalize()} News Headlines in {country.upper()}:\n")
            for idx, article in enumerate(articles):
                news = soundOutput + article['title']
                
                print(f"{idx + 1}. {article['title']}")
                print(f"   Source: {article['source']['name']}")
                print(f"   URL: {article['url']}\n")
                return news
        else:
            print("No news articles found.")
    else:
        print(f"Failed to fetch news. Status code: {response.status_code}")


quote = get_random_quote()
weather =  get_weather('Liepaja')
news =  get_top_headlines(country='us', category='general')
tts = gTTS(quote + weather + news)
tts.save("output.mp3")


