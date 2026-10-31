import asyncio
import os
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import re
from database import init_db, save_listing

def parse_price(price_text):
    digits = re.sub(r'\D', '', price_text)
    return int(digits) if digits else None
   

async def parse_single_product(page, product_url, title_selector):
    try:
        await page.goto(
            product_url,
            wait_until="domcontentloaded",
            timeout=30000
        )
        await page.wait_for_selector(title_selector, timeout=10000)

        html_content = await page.content()
        product_soup = BeautifulSoup(html_content, 'lxml')

        title_element = product_soup.select_one(title_selector)
        if not title_element:
            title_element = product_soup.find(
                "h4", attrs={"data-nx-name": "H4"}
            )

        if not title_element or "Повідомлення" in title_element.text:
            return None

        item_data = {
            "title": title_element.text.strip(),
            "url": product_url,
        }

        image_element = product_soup.select_one(
            'div[data-testid="image-gallery-container"] img'
        )
        item_data["image"] = (
            image_element.get("src") if image_element else "не знайдено"
        )
        
        price_element = product_soup.select_one(
            'div[data-testid="ad-price-container"] h3'
        )
        if not price_element:
            price_element = product_soup.find(
                "h3", attrs={"data-nx-name": "H3"}
            )

        raw_price = price_element.get_text(strip=True) if price_element else ""
        item_data["price"] = parse_price(raw_price)

        #Опис
        description_element = product_soup.select_one(
            'div[data-testid="ad-description"] '
        )
        if not description_element:
            description_element = product_soup.find(
                "div", attrs={"data-cy": "ad description"}
            )
        item_data["description"] = (
            description_element.get_text(strip=True)
            if description_element else "не знайдено"
        )
        return item_data

    except Exception as e:
        print(f"Помилка при парсингу товару {product_url}: {e}")
        return None                

           
  



async def collect_all_pages():
    init_db()
    os.makedirs('data', exist_ok=True)
    title_selector = 'div[data-testid="offer_title"] h4[data-nx-name="H4"]'

    async with async_playwright() as p:
        print("\n[СТАРТ] Запуск браузера для парсингу 25 сторінок...")
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--start-maximized']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='uk-UA',
            timezone_id='Europe/Kyiv'
        )
        page = await context.new_page()

        
        for page_num in range(1, 26):
            list_url = f"https://www.olx.ua/uk/elektronika/kompyutery-i-komplektuyuschie/?page={page_num}"
            print(f"\n--- ОБРОБКА СТОРІНКИ №{page_num} ---")
            print(f"Перехід на: {list_url}")
            
            try:
                await page.goto(list_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000) 
                
                
                list_html = await page.content()
                list_soup = BeautifulSoup(list_html, 'lxml')
                articles = list_soup.find_all('div', attrs={'data-cy': 'l-card'})
                
                page_urls = []
                for article in articles:
                    link_element = article.find('a')
                    if link_element:
                        url_path = link_element.get('href')
                        if url_path and url_path.startswith('/'):
                            page_urls.append('https://olx.ua' + url_path)

                print(f"Знайдено {len(page_urls)} оголошень на сторінці №{page_num}")
                
                
                page_products = []
                
                
                for prod_url in page_urls:
                    print(f" Парсимо товар: {prod_url.split('/')[-1][:30]}...")

                    product_data = await parse_single_product(
                        page, prod_url, title_selector
                    )

                    if not product_data:
                        print("[ПРОПУСК] Не вдалося отримати товар")
                        continue

                    result = save_listing(
                        title=product_data["title"],
                        price=product_data["price"],
                        url=product_data["url"]
                    )

                    print(
                        f"[DB] {result['status']} | "
                        f"{product_data['title'][:30]}... | "
                        f"{result['new_price']}"
                    )

                    page_products.append(product_data)
                    print(
                        f"[УСПІХ] Збережено: "
                        f"{product_data['title'][:30]}... | "
                        f"{product_data['price']}"
                    )
                
                # Зберігаємо окремий JSON для поточної сторінки
                output_file = f'data/page_{page_num}.json'
                with open(output_file, 'w', encoding='utf-8') as json_file:
                    json.dump(page_products, json_file, ensure_ascii=False, indent=4)
                print(f"[ЗБЕРЕЖЕНО] Створено файл: {output_file} (Всього товарів: {len(page_products)})")
                
            except Exception as page_error:
                print(f"Помилка обробки сторінки списку №{page_num}: {page_error}")

        await browser.close()
    print("\n[ФІНІШ] Усі 25 сторінок успішно оброблені!")

if __name__ == "__main__":
    asyncio.run(collect_all_pages())
