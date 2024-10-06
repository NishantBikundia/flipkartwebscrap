from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from selenium import webdriver
from bs4 import BeautifulSoup
import os
import time

app = Flask(__name__)

# MongoDB setup
client = MongoClient('mongodb+srv://Manya:Manya%40072007@cluster0.grkkany.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['flipkart_reviews']
collection = db['products']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        query = request.form['query']
        url = f"https://www.flipkart.com/search?q={query}"

        # Set up Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        time.sleep(2)  # Wait for the page to load
        soup = BeautifulSoup(driver.page_source, "lxml")
        driver.quit()

        names = soup.find_all("div", class_="KzDlHZ")
        prices = soup.find_all("div", class_="Nx9bqj _4b5DiR")
        desc_list = soup.find_all("ul", class_="G4BRas")
        reviews_blocks = soup.find_all("div", class_="_5OesEi")
        
        product_info = []

        def clean_text(text):
            return text.strip()

        for i in range(len(names)):
            product = {}
            product['name'] = clean_text(names[i].text)
            product['price'] = clean_text(prices[i].text).replace("â‚¹", "₹").replace(",", "")
            
            if i < len(desc_list):
                items = desc_list[i].find_all("li")
                product['description'] = " | ".join([clean_text(item.text) for item in items])
            else:
                product['description'] = "No description available"
            
            review_text = "No reviews available"
            if i < len(reviews_blocks):
                rating = reviews_blocks[i].find("div", class_="XQDdHH")
                ratings_count = reviews_blocks[i].find("span", class_="Wphh3N")
                if rating and ratings_count:
                    review_text = clean_text(rating.text) + " | " + clean_text(ratings_count.text)
            
            product['reviews'] = review_text
            product_info.append(product)

        # Insert data into MongoDB
        collection.insert_many(product_info)

        return render_template('results.html', products=product_info)

    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('error.html', error=str(e))  # Render error template

if __name__ == "__main__":
    app.run(debug=True)
