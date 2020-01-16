import pandas as pd
from fake_useragent import UserAgent
import requests
import cfscrape
import random
import time
from bs4 import BeautifulSoup
import sys
import re
import numpy as np
import urllib.parse
from urllib.request import urlretrieve

feature_list = ['Grill Type', 'Metal Type', 'Finishing', 'Material', 'NET WEIGHT', 'Gross Weight', 
                 'Packing Size', 'Power Source', 'Volts', 'DIMENSIONS', 'Product size', 
                'Capacity','size', 'Tool Type', 'Single gross weight', 'dimension']

def scraping_function(url, category):
    sleep_min = 2 
    sleep_max = 4
#    try:
#        proxies_list = ['62.162.195.217:41418', '46.201.252.32:53281', '82.117.247.134:49561', 
#                        '5.9.233.14:8080', '178.132.200.244:3128']
#        proxies = {'https': random.choice(proxies_list)}

    ua = UserAgent()
    header = {'User-Agent':str(ua.chrome)}

    sess = requests.session()
    sess = cfscrape.create_scraper(sess)
    page = sess.get(url+category, headers=header, timeout=50) # proxies=proxies,

    soup = BeautifulSoup(page.content, 'lxml')
# =============================================================================
# 
#     except:
#         print(sys.exc_info()[0])
#         print("Error: An error or timeout occured for url:" , url+category) #, "with proxy", proxies)
    if sleep_max > 0:
         time.sleep(random.randint(sleep_min, sleep_max))    
    return soup
# =============================================================================

def get_images(soup, url):
#    img_links = soup.findAll('img')
    imgs = soup.select('img')
    img = imgs[0]
    img_url = urllib.parse.urljoin(url, img['src'])
    file_name = img['src'].split('/')[-1]
    urlretrieve(img_url, file_name)
#    print(img_url)
    return img_url

def scrape(url, category):
    soup = scraping_function(url, category) 
    prod_links = soup.findAll('a', attrs = {'href': re.compile(".*(product-detail).*")})
    prods = [item.get('href') for item in prod_links]
    features_material_arr = []
    values_material_arr = []
    prod_all = []
    img_url_all = []
    title_arr = []
    nr_all = []
    data = []
    for item in prods:
        df = {}
        url2 = 'https:'+item
        category2 = ''
        soup2 = scraping_function(url2, category2) 
        img_url = get_images(soup2, url2)
        features = [i.get_text('span') for i in soup2.findAll('dt')]
        values = [i.get_text('span') for i in soup2.findAll('dd')]
        nr = [i.get_text('span') for i in soup2.findAll('span', class_='bread-count')]
        features = [i.replace('\n', '') for i in features]
        features = [i.replace('span', '') for i in features]
        features = [i.replace(':', '') for i in features]
        features = [s.replace('                    ', '') for s in features[1:]]
        values = [item.replace('\n', '') for item in values]
        values = [item.replace('span', '') for item in values]
        values = [s.replace('                    ', '') for s in values[1:]]
        title = [i.get_text('h1') for i in soup2.findAll('h1')]
        inter = np.intersect1d(features, feature_list)
        indices_arr = []
        for item2 in inter:
            indices = [i for i, s in enumerate(features) if item2 in s]
            indices_arr = np.append(indices_arr, indices)
            indices_arr = indices_arr.astype(int)
        features_material = [features[i] for i in indices_arr]
        values_material = [values[i] for i in indices_arr]
        features_material_arr = np.append(features_material_arr, features_material)
        values_material_arr = np.append(values_material_arr, values_material)
        if len(nr) == 0:
            nr = ['No article number']
        if len(title) == 0:
            title = ['No title']
        nr2 = len(features_material) * [nr]
        prod = len(features_material) * [item]
        desc = len(features_material) * [title[0]]
        img_url = len(features_material) * [img_url]
        prod_all = np.append(prod_all, prod)
        title_arr = np.append(title_arr, desc)
        nr_all = np.append(nr2, nr_all)
        img_url_all = np.append(img_url_all, img_url)
        df['Article Nr.'] = nr2
        df['Description'] = desc
        df['Product Links'] = prod
        df['Image Links'] = img_url
        df['Features'] = features_material
        df['Values'] = values_material
        data.append(df)
    return render_template("index.html", data=data)

if __name__ == "__main__":
    url = 'https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText='
    category = 'waffle+maker'
    scrape(url, category)
# 
