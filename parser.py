from bs4 import BeautifulSoup
from pyopenmensa.feed import LazyBuilder
from datetime import date, timedelta
import requests
import re

from flask import Flask

app = Flask(__name__)

@app.route("/")
def test():
    return "<p>Hello, World!</p>"

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)

def get_plan_for_mensa(mensa):
    html = requests.get("https://www.stw-bremen.de/de/" + mensa)
    soup = BeautifulSoup(html.text, 'html.parser')

    canteen = LazyBuilder()
    current = date.today()
    if current.weekday() > 4:
        current = next_weekday(current, 0)

    meal_category = ""
    meal_description = []
    meal_price_student = ""
    meal_price_employe = ""
    meal_type = []
    i = 0
    # Food plan in the website
    for div in soup.find_all('div', {'class': 'food-plan'}):
        # Food plan for every day
        for table in div.find_all('table', {'class': 'food-category'}):
            # Entry for every Meal in this mensa
            for meal in table.find_all('tr'):
                #print(meal.prettify())
                if len( meal.find_all('th', {'class': 'category-name'})) > 1:
                    print("WARNING: More than one food category in Header")
                # Find category name for this meal
                for h in meal.find_all('th', {'class': 'category-name'}):
                    # Should only be one entry, regular expression is to trim multiple spaces
                    meal_category = re.sub(' +', ' ', h.text).replace('&', 'und')

                # Get food type, e.g. plant-based/vegan, vegetarian, chicken, etc.
                if 'class' in meal.attrs:
                    types = list(map(lambda x: x.replace('food-type-','').replace('plant-based--', '').capitalize(), \
                        filter(lambda x: 'food-type' in x, meal['class'])))
                    types = list(map(lambda x: re.sub('-+', ' ', x), types))
                    #meal_type.append(list(filter(lambda x: 'food-type' in x, meal['class'])))
                    meal_type.append(types)

                # Get meal description and prices
                for h in meal.find_all('td'):
                    if 'description' in h['class'][1]:
                        # Ugly hack because there are some unnecessary tags in the description
                        if h.sup: h.sup.decompose()
                        if h.sup: h.sup.decompose()
                        # Remove bytes for new line
                        t = h.text.replace('\n', ' ').replace('\r', '')
                        # Correct '&' because encoding
                        t = t.replace('&', ' und')
                        # Remove multiple spaces which can result from cleaning the string above
                        t = re.sub(' +', ' ', t)
                        meal_description.append(t)
                    if 'price-student' in h['class'][1]:
                        meal_price_student = h.text
                    if 'price-employees' in h['class'][1]:
                        meal_price_employe = h.text
            # If there are more than one description for a category
            for i in range(len(meal_description)):
                canteen.addMeal(current, meal_category, meal_description[i], notes=meal_type[i], \
                    prices={'student': meal_price_student, 'employee' : meal_price_employe})
            meal_description = []
            meal_type = []
        # Set date to the next day
        current += timedelta(days=1)
        # If the next day is Saturday or sunday set date to Monday
        if current.weekday() > 4:
            current = next_weekday(current, 0)
            #break
        #break
    return canteen.toXMLFeed()
    #print(canteen.toXMLFeed())



@app.route("/mensa/<mensa>")
def parse_mensa(mensa):
    return get_plan_for_mensa("mensa/" + mensa)

@app.route("/cafeteria/<cafeteria>")
def parse_cafeteria(cafeteria):
    return get_plan_for_mensa("cafeteria/" + cafeteria)

#if __name__ == '__main__':
#    get_plan_for_mensa("uni-mensa")
