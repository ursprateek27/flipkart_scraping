import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
import datetime
import os
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

current_date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

input_csv_path  = "input_data.csv"
output_csv_path = f"output_{current_date_time}.csv"

_CategoryLink   = "https://www.flipkart.com/favourite-enid-blyton-stories/p/itmf3yxt3njbju4k?pid="
_SellerLink     = "https://www.flipkart.com/sellers?pid="

_header         = True

# ANSI color codes for terminal output
RED    = '\033[91m'
YELLOW = '\033[33m'
GREEN  = '\033[0;32m'
RESET  = '\033[0m'
BLUE   = "\033[0;34m"

def make_csv(datas):

    global _header

    data_dict = {
        'FSN':                  datas[0],  # FSN
        'Product Name':         datas[1],  # pr_names
        'Selling price':        datas[2],  # pr_price_selling
        'Original price':       datas[3],  # pr_price_original
        'Seller Name':          datas[4],  # pr_seller_name
        'Shipping Fees':        datas[5],  # pr_shipping_fees
        'Image Links':          datas[6],  # pr_image_links  
        'Image Count':          datas[7],  # pr_image_count
    }

    # Generate output CSV file to store the scraped data
    try:
        df = pd.DataFrame.from_dict([data_dict])
    except Exception as e:
        print(f"{RED}Error: ", e)
        return

    with open(output_csv_path, 'a+', encoding="utf-8", newline='') as outputfile:
        if _header:
            df.to_csv(outputfile, index=False, header=True)
            _header = False
        else:
            df.to_csv(outputfile, index=False, header=False)

def product_spider(product_url, fsn):
    
    try:
        # Make a GET request to the product page
        get_product_page = requests.get(product_url,  headers=HEADERS, verify=False)
        
        # Parse the HTML content of the product page
        product_page_soup = BeautifulSoup(get_product_page.text, 'html.parser')

        # Product name
        pr_names = product_page_soup.find('span', {'class': 'VU-ZEz'})
        pr_names = str(pr_names.text).replace(',', '') if pr_names is not None else 'Not available'
        #print(pr_names)

        # Selling price
        pr_price_selling = product_page_soup.find('div', {'class': 'Nx9bqj CxhGGd'})
        pr_price_selling = str(pr_price_selling.text).replace('₹', 'Rs ') if pr_price_selling is not None else 'Null'
        #print(pr_price_selling)

        # Original price
        pr_price_original = product_page_soup.find('div', {'class': 'yRaY8j A6+E6v'})
        pr_price_original = str(pr_price_original.text).replace('₹', 'Rs ') if pr_price_original is not None else 'Null'
        #print(pr_price_original)

        # Seller name
        pr_seller_name = product_page_soup.find('div', {'class': 'yeLeBC'})
        pr_seller_name = str(pr_seller_name.text) if pr_seller_name is not None else 'Not available'
        #print(pr_seller_name)

        # Shipping Fees
        pr_shipping_fees = product_page_soup.find('div', {'class': 'hVvnXm'})
        pr_shipping_fees = str(pr_shipping_fees.text).replace('₹', 'Rs ') if  pr_shipping_fees is not None else 'Null'
        #print(pr_shipping_fees)

        # Image Links
        pr_img_elements = product_page_soup.find_all('img', class_='_0DkuPH')
        pr_src_values = [img.get('src') for img in pr_img_elements if img.get('src') is not None]
        #print(pr_src_values)

        # Image Count
        pr_img_count = len(pr_src_values) if pr_src_values is not None else 0
        #print(pr_img_count)
        
        make_csv([
                    fsn,
                    pr_names,
                    pr_price_selling,
                    pr_price_original,
                    pr_seller_name,
                    pr_shipping_fees,
                    pr_src_values,
                    pr_img_count
                ])

    except requests.RequestException as e:
        print(f"{RED}Error fetching product page: {e}")

def page_spider():

    print(f"{GREEN}\n-------SCRAPING STARTS-------\n{RESET}")

    # Read the input CSV file
    csvfile = pd.read_csv(input_csv_path)

    # Total number of rows in the CSV
    total_rows = len(csvfile)
    #print(f"{BLUE}Total No. of FSN's: {RESET}{total_rows}")

    header = True
    scraped_count = 0

    # Create a progress bar
    progress_bar = tqdm(total=total_rows, desc="Scraping Progress", unit="rows", colour="blue")

    for i, j in csvfile.iterrows():
        fsn = str(j.values[0])
        Prod_url = _CategoryLink + fsn
        #Sell_url = _SellerLink + fsn

        #print(f"{GREEN}Processing URL: {RESET}{Prod_url}")

        try:
            # Make a GET request to the product URL
            get_flipkart_page = requests.get(Prod_url, verify=True)

            # Create a BeautifulSoup object from the response
            flipkart_soup = BeautifulSoup(get_flipkart_page.text, 'html.parser')

            # Sanity check
            if flipkart_soup:
                product_spider(Prod_url, fsn)
                scraped_count += 1
                progress_bar.update(1)
                # print(f"{BLUE}Scraped {scraped_count}/{total_rows} rows")

        except requests.RequestException as e:
            print(f"{RED}Error fetching category page: {e}")

    progress_bar.colour = "green"
    progress_bar.close()
    # print full path of output file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    output_file_path = os.path.join(dir_path, output_csv_path)
    print(f"{RESET}\nOutput file: {BLUE} {output_file_path}")
    print(f"{GREEN}\n-------SCRAPING ENDS-------\n")


if __name__ == '__main__':
    try:
        page_spider()
    except KeyboardInterrupt:
        print(f"{YELLOW}\n\nExiting...")
    except Exception as e:
        print(f"{RED}Error: ", e)