# app.py
import pandas as pd
import numpy as np
#from fake_useragent import UserAgent
import requests
import cfscrape
import random
import time
from bs4 import BeautifulSoup
import re
import urllib.parse
from flask import Flask, render_template, request, send_from_directory
from wtforms import Form, TextField, validators
import configparser
import ast

# App config.
DEBUG = True
application = Flask(__name__, static_url_path='/static')
application.config.from_object(__name__)
application.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

# Our index
#url = 'https://www.alibaba.com/'
#category = 'waffle maker'
config = configparser.ConfigParser()
config.sections()
config.read('features.ini')
 
# set the "static" directory as the static folder.
# this will ensure that all the static files are under one folder
 
# serving some static html files
@application.route('/html/path:path')
def send_html(path):
    return send_from_directory('static', path)

def scraping_function(url):
    sleep_min = 2 
    sleep_max = 4
#    category_arr = category.split()
#    category2 = '+'.join(category_arr)
#        proxies_list = ['62.162.195.217:41418', '46.201.252.32:53281', '82.117.247.134:49561', 
#                        '5.9.233.14:8080', '178.132.200.244:3128']
#        proxies = {'https': random.choice(proxies_list)}

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    headers = {'User-Agent': user_agent}

    sess = requests.session()
    sess = cfscrape.create_scraper(sess)
    page = sess.get(url, headers=headers, timeout=50) # proxies=proxies,

    soup = BeautifulSoup(page.content, 'lxml')

    if sleep_max > 0:
        time.sleep(random.randint(sleep_min, sleep_max))    
    return soup

def get_images(soup, url):
#    img_links = soup.findAll('img')
    imgs = soup.select('img')
    img = imgs[1]
    img_url = urllib.parse.urljoin(url, img['src'])
#    file_name = mypath+'\\wtpfiles\\'+img['src'].split('/')[-1]
#    urlretrieve(img_url, file_name)
#    print(img_url)
    return img_url

def get_links(url, category):
#    https://www.alibaba.com/products/BBQ.html?IndexArea=product_en&page=2
    category_arr = category.split()
    category2 = '_'.join(category_arr)
    prods_all = []
    for page in range(1, 2):
        url = url+'products/'+category2+'.html?IndexArea=product_en&page='+str(page)
        soup = scraping_function(url) 
        prod_links = soup.findAll('a', attrs = {'href': re.compile(".*(product-detail).*")})
        prods = [item.get('href') for item in prod_links]
        prods_all = np.append(prods_all, prods)
    return prods_all
    
def get_features(url, category, config):
    features_material_arr = []
    values_material_arr = []
    prod_all = []
    title_arr = []
    nr_all = []
    img_url_all =[]
    feature_list = ast.literal_eval(config['Features']['All'])
    pd.set_option('display.max_colwidth', -1)
    prods_all = get_links(url, category)
    df = pd.DataFrame()
#    os.makedirs(mypath+'\\wtpfiles')
    for item in prods_all:
        url2 = 'https:'+item
        soup2 = scraping_function(url2) 
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
        nr2 = [i.replace(')', '').replace('(', '') for i in nr]
        if len(nr2) == 0:
            nr2 = ['No article number']
        if len(title) == 0:
            title = ['No title']
        nr_list = len(features_material) * nr2
        prod = len(features_material) * [url2]
        desc = len(features_material) * [title[0]]
        img_url = len(features_material) * [img_url]
        prod_all = np.append(prod_all, prod)
        title_arr = np.append(title_arr, desc)
        nr_all = np.append(nr_all, nr_list)
        img_url_all = np.append(img_url_all, img_url)
#    shutil.make_archive('wtpfiles', 'zip', mypath)
    df['Description'] = title_arr
    df['Product Links'] = prod_all
    df['Features'] = features_material_arr
    df['Values'] = values_material_arr
    df['Article Nr.'] = nr_all
    return df, img_url_all


class ReusableForm(Form):
    url = TextField('URL:', validators=[validators.required()])
    category = TextField('Category:', validators=[validators.required()])
    feature_type = TextField('Features:', validators=[validators.required()])
#    file_path = TextField('Download photos to:', validators=[validators.required()])
    @application.route("/", methods=['GET', 'POST'])
    @application.route('/index', methods=['GET', 'POST'])
    def hello():
        form = ReusableForm(request.form)
        options = config.options('Features')
# =============================================================================
#         material_features = ast.literal_eval(config['Features']['Material'])
#         weight_features = ast.literal_eval(config['Features']['Weight'])
#         size_features = ast.literal_eval(config['Features']['Size'])
#         finishing_features = ast.literal_eval(config['Features']['Finishing'])
#         grill_type_features = ast.literal_eval(config['Features']['Grill Type'])
#         type_features = ast.literal_eval(config['Features']['Type'])
#         thickness_features = ast.literal_eval(config['Features']['Thickness'])
#         color_features = ast.literal_eval(config['Features']['Color'])
#         usage_features = ast.literal_eval(config['Features']['Usage'])
#         product_type_features = ast.literal_eval(config['Features']['Product Type'])
#         product_name_features = ast.literal_eval(config['Features']['Product Name'])
#         brand_name_features = ast.literal_eval(config['Features']['Brand Name'])
#         feat_features = ast.literal_eval(config['Features']['Features'])
#         model_number_features = ast.literal_eval(config['Features']['Model Number'])
#         place_origin_features = ast.literal_eval(config['Features']['Place of Origin'])
# 
# =============================================================================
        if request.method == 'POST':
            url = request.form['url']
            category = request.form['category']
            feature_type = request.form['feature_type']
#            file_path = request.form['file_path']
        if form.validate():
        # Save the comment here.
            df, img_url_all = get_features(url, category, config)
            item = feature_type.split(', ')
            df1 = pd.DataFrame()
            for j in options[1:]:
                features = ast.literal_eval(config['Features'][j])
                for i in item:
                    if any(i in s for s in features):
                        df1 = df1.append(df[df['Features'].isin(features)])
# =============================================================================
#                 if any(i in s for s in material_features):
#                     df1 = df1.append(df[df['Features'].isin(material_features)])
#                 if any(i in s for s in weight_features):
#                     df1 = df1.append(df[df['Features'].isin(weight_features)])
#                 if any(i in s for s in size_features):
#                     df1 = df1.append(df[df['Features'].isin(size_features)])
#                 if any(i in s for s in finishing_features):
#                     df1 = df1.append(df[df['Features'].isin(finishing_features)])
#                 if any(i in s for s in grill_type_features):
#                     df1 = df1.append(df[df['Features'].isin(grill_type_features)])
#                 if any(i in s for s in type_features):
#                     df1 = df1.append(df[df['Features'].isin(type_features)])
#                 if any(i in s for s in thickness_features):
#                     df1 = df1.append(df[df['Features'].isin(thickness_features)])
#                 if any(i in s for s in color_features):
#                     df1 = df1.append(df[df['Features'].isin(color_features)])
#                 if any(i in s for s in usage_features):
#                     df1 = df1.append(df[df['Features'].isin(usage_features)])
#                 if any(i in s for s in product_type_features):
#                     df1 = df1.append(df[df['Features'].isin(product_type_features)])
#                 if any(i in s for s in brand_name_features):
#                     df1 = df1.append(df[df['Features'].isin(brand_name_features)])
#                 if any(i in s for s in feat_features):
#                     df1 = df1.append(df[df['Features'].isin(feat_features)])
#                 if any(i in s for s in model_number_features):
#                     df1 = df1.append(df[df['Features'].isin(model_number_features)])
#                 if any(i in s for s in place_origin_features):
#                     df1 = df1.append(df[df['Features'].isin(place_origin_features)])
#                 if any(i in s for s in product_name_features):
#                     df1 = df1.append(df[df['Features'].isin(product_name_features)])
#                     
# =============================================================================
            df1 = df1.drop_duplicates()
            dfhtml = df1.to_html(classes="scraped", table_id='response', 
                                index=False)
            return render_template('index.html', tables = [dfhtml], phlist = img_url_all.tolist(),  
                                   titles = df1.columns)
        return render_template('hello.html', form=form)
        
# =============================================================================
#     @app.route("/download/", methods=['POST'])
#     def download():
#         form = ReusableForm(request.form)
#         #Moving forward code
#         forward_message = "Download"
#         if request.method == 'POST':
#             download = request.form['download']
#         if form.validate():
#             output = BytesIO()
#             writer = pd.ExcelWriter(output, engine='xlsxwriter')
#         
#             #taken from the original question
#             df.to_excel(writer, startrow = 0, merge_cells = False, sheet_name = "Sheet_1")
#             workbook = writer.book
#             worksheet = writer.sheets["Sheet_1"]
#             format = workbook.add_format()
#             format.set_bg_color('#eeeeee')
#             worksheet.set_column(0,9,28)
#         
#             #the writer has done its job
#             writer.close()
#         
#             #go back to the beginning of the stream
#             output.seek(0)
#             return send_file(output, attachment_filename="testing.xlsx", as_attachment=True)
# 
# =============================================================================
#        return render_template('index.html', message=forward_message);
#    def index(url, category, feature_list):
#        df = scrape(url, category, feature_list)
#        dfhtml = df.to_html(header="true", classes="scraped")
#        return render_template('index.html', tables = [dfhtml], titles = df.columns)

if __name__ == "__main__":
    application.run(debug=True, host='0.0.0.0', port=5000)