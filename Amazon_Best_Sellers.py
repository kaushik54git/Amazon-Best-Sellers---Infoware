from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import logging
import pandas as pd
from datetime import datetime

class AmazonScraper:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            filename=f'amazon_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)

    def login(self):
        try:
            self.driver.get('https://www.amazon.in/ap/signin')
            
            # Enter email
            email_field = self.driver.find_element(By.ID, 'ap_email')
            email_field.send_keys(self.email)
            self.driver.find_element(By.ID, 'continue').click()
            
            # Enter password
            password_field = self.driver.find_element(By.ID, 'ap_password')
            password_field.send_keys(self.password)
            self.driver.find_element(By.ID, 'signInSubmit').click()
            
            logging.info("Successfully logged in")
            return True
            
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            return False

    def get_category_urls(self):
        category_urls = [
            'https://www.amazon.in/gp/bestsellers/kitchen',
            'https://www.amazon.in/gp/bestsellers/shoes',
            'https://www.amazon.in/gp/bestsellers/computers',
            'https://www.amazon.in/gp/bestsellers/electronics',
        ]
        return category_urls[:10]

    def extract_product_details(self, product_element):
        try:
            product_data = {
                'name': self.safe_extract(product_element, './/span[@class="a-size-medium a-color-base a-text-normal"]'),
                'price': self.safe_extract(product_element, './/span[@class="a-price-whole"]'),
                'original_price': self.safe_extract(product_element, './/span[@class="a-price a-text-price"]'),
                'rating': self.safe_extract(product_element, './/span[@class="a-icon-alt"]'),
                'num_reviews': self.safe_extract(product_element, './/span[@class="a-size-small"]'),
            }

            if product_data['original_price'] and product_data['price']:
                try:
                    original = float(product_data['original_price'].replace('₹', '').replace(',', ''))
                    current = float(product_data['price'].replace(',', ''))
                    discount = ((original - current) / original) * 100
                    product_data['discount_percentage'] = round(discount, 2)
                except:
                    product_data['discount_percentage'] = 0

            return product_data

        except Exception as e:
            logging.error(f"Error extracting product details: {str(e)}")
            return None

    def safe_extract(self, element, xpath):
        try:
            return element.find_element(By.XPATH, xpath).text
        except:
            return None

    def get_product_additional_details(self, product_url):
        try:
            self.driver.get(product_url)
            time.sleep(2)
            
            additional_details = {
                'description': self.safe_extract(self.driver, '//div[@id="productDescription"]'),
                'ship_from': self.safe_extract(self.driver, '//div[@id="tabular-buybox"]//span[contains(text(), "Ships from")]/../following-sibling::span'),
                'sold_by': self.safe_extract(self.driver, '//div[@id="tabular-buybox"]//span[contains(text(), "Sold by")]/../following-sibling::span'),
                'images': [img.get_attribute('src') for img in self.driver.find_elements(By.XPATH, '//div[@id="altImages"]//img')]
            }
            
            return additional_details

        except Exception as e:
            logging.error(f"Error getting additional details: {str(e)}")
            return None

    def scrape_category(self, category_url):
        products = []
        try:
            self.driver.get(category_url)
            category_name = self.driver.find_element(By.ID, 'zg_banner_text').text
            
            for page in range(1, 16):
                product_elements = self.driver.find_elements(By.XPATH, '//div[@class="a-section a-spacing-none aok-relative"]')
                
                for product in product_elements:
                    product_data = self.extract_product_details(product)
                    
                    if product_data and product_data.get('discount_percentage', 0) > 50:
                        
                        product_url = product.find_element(By.XPATH, './/a[@class="a-link-normal"]').get_attribute('href')
                        additional_details = self.get_product_additional_details(product_url)
                        
                        if additional_details:
                            product_data.update(additional_details)
                        
                        product_data['category'] = category_name
                        products.append(product_data)
                
                try:
                    next_button = self.driver.find_element(By.XPATH, '//li[@class="a-last"]/a')
                    next_button.click()
                    time.sleep(2)
                except:
                    break
                    
        except Exception as e:
            logging.error(f"Error scraping category {category_url}: {str(e)}")
            
        return products

    def save_to_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def save_to_csv(self, data, filename):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')

    def run(self):
        try:
            self.setup_driver()
            if not self.login():
                raise Exception("Login failed")

            all_products = []
            category_urls = self.get_category_urls()

            for category_url in category_urls:
                products = self.scrape_category(category_url)
                all_products.extend(products)
                logging.info(f"Scraped {len(products)} products from {category_url}")

            self.save_to_json(all_products, 'amazon_products.json')
            self.save_to_csv(all_products, 'amazon_products.csv')
            
            logging.info(f"Successfully scraped {len(all_products)} products total")

        except Exception as e:
            logging.error(f"Scraping failed: {str(e)}")
        
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    scraper = AmazonScraper(email="kaushikkumbhat54@gmail.com", password="notmypassword")
    scraper.run()
