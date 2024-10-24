
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
        'pageSize': 5
    }

    response = requests.get(NEWS_BASE_URL, params=params)
    print("*********" + country + "  " + category)
    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
        
        if articles:
            soundOutput = f"Top {category.capitalize()} News Headlines in {country.upper()}:\n"
            print(f"Top {category.capitalize()} News Headlines in {country.upper()}:\n")
            news = soundOutput
            for idx, article in enumerate(articles):
                if(article['title'] != '[Removed]'):
                    news = news + article['title']
                
                    print(f"{idx + 1}. {article['title']}")
                    print(f"   Source: {article['source']['name']}")
                    print(f"   URL: {article['url']}\n")
                
        else:
            print("No news articles found.")
    else:
        print(f"Failed to fetch news. Status code: {response.status_code}")
    return news
def display_menu():
    """
    Menu choices to the user.
    """
    print("=== Light Menu ===")
    print("1. Get a Quote")
    print("2. Get weather")
    print("3. Get news")
    print("4. Exit")
    print("===================")

def main():
    while True:
        display_menu()
        
        choice = input("Please choose an option (1-4): ")

        if choice == '1':
            quote = get_random_quote()
            tts = gTTS(quote)
            tts.save("output.mp3")
        elif choice == '2':
            weather = get_weather('Latvia')
            if(weather!=''):
                tts = gTTS(weather)
                tts.save("output.mp3")
        elif choice == '3':
            news =  get_top_headlines(country='us', category='general')
            tts = gTTS(news)
            tts.save("output.mp3")
        elif choice == '4':
            print("Exiting the program. Goodbye!")
            break  # Exit the loop and end the program
        else:
            print("Invalid choice. Please choose a number between 1 and 4.")
        
        print()  # Print a new line for better readability


if __name__ == "__main__":
    main()


