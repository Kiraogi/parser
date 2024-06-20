import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext, messagebox
from concurrent.futures import ThreadPoolExecutor
import pandas as pd


def get_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        messagebox.showerror("Ошибка запроса", f"Не удалось получить данные с {url}: {str(e)}")
        return None


def parse_product_page_petrovich(html):
    soup = BeautifulSoup(html, 'html.parser')
    try:
        name = soup.find('span', class_='title-lg', attrs={'data-test': 'product-title'}).text.strip()
        product_code = soup.find('span', class_='pt-c-secondary', attrs={'data-test': 'product-code'}).text.strip()
        price_card = soup.find('div',
                               class_='pt-price___c9u6v pt-price-cp___tzloY gold-price pt-typography____JqPt pt-t-label-lg-m-mid___mv6lT pt-ta-left pt-c-secondary pt-wrap',
                               attrs={'data-test': 'product-gold-price'}).text.strip()
        price_regular = soup.find('div',
                                  class_='pt-price___c9u6v pt-price-cp___tzloY retail-price pt-typography____JqPt pt-t-h3___Sr1ag pt-ta-left pt-c-secondary-lowest pt-wrap',
                                  attrs={'data-test': 'product-retail-price'}).text.strip()
        brand = soup.find('span', class_='title').text.strip()
        link = soup.find('link', {'rel': 'canonical'})['href']

        return {
            'link': link,
            'name': name,
            'product_code': product_code,
            'price_card': price_card,
            'price_regular': price_regular,
            'brand': brand
        }
    except AttributeError as e:
        print(f"Ошибка парсинга: {str(e)}")
        return None


def parse_catalog_petrovich(url):
    html = get_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    for a_tag in soup.find_all('a', class_='catalog-product__name'):
        product_url = 'https://petrovich.ru' + a_tag['href']
        product_html = get_html(product_url)
        if product_html:
            product_data = parse_product_page_petrovich(product_html)
            if product_data:
                products.append(product_data)
    return products


def parse_product_page_leroymerlin(html):
    soup = BeautifulSoup(html, 'html.parser')
    try:
        name = soup.find('h1', class_='header-2').text.strip()
        product_code = soup.find('span', class_='product-code').text.strip()
        price = soup.find('span', class_='price__main-value').text.strip()
        brand = soup.find('div', class_='brand__name').text.strip()
        link = soup.find('link', {'rel': 'canonical'})['href']

        return {
            'link': link,
            'name': name,
            'product_code': product_code,
            'price': price,
            'brand': brand
        }
    except AttributeError as e:
        print(f"Ошибка парсинга: {str(e)}")
        return None


def parse_catalog_leroymerlin(url):
    html = get_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    for a_tag in soup.find_all('a', class_='plp-item__info__title'):
        product_url = 'https://leroymerlin.ru' + a_tag['href']
        product_html = get_html(product_url)
        if product_html:
            product_data = parse_product_page_leroymerlin(product_html)
            if product_data:
                products.append(product_data)
    return products


def save_to_excel(products, filename='products.xlsx'):
    df = pd.DataFrame(products)
    df.to_excel(filename, index=False)
    messagebox.showinfo("Сохранение данных", f"Данные успешно сохранены в файл {filename}")


def start_parsing():
    petrovich_url = petrovich_entry.get().strip()
    leroymerlin_url = leroymerlin_entry.get().strip()

    if not petrovich_url and not leroymerlin_url:
        messagebox.showerror("Ошибка ввода", "Пожалуйста, введите хотя бы один URL-адрес.")
        return

    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "Парсинг данных, пожалуйста подождите...\n")

    products = []
    with ThreadPoolExecutor() as executor:
        futures = []
        if petrovich_url:
            futures.append(executor.submit(parse_catalog_petrovich, petrovich_url))
        if leroymerlin_url:
            futures.append(executor.submit(parse_catalog_leroymerlin, leroymerlin_url))

        for future in futures:
            result = future.result()
            if result:
                products.extend(result)
                if future == futures[0] and petrovich_url:
                    output_text.insert(tk.END, "Петро́вич:\n")
                elif leroymerlin_url:
                    output_text.insert(tk.END, "\nЛеруа Мерлен:\n")
                for product in result:
                    output_text.insert(tk.END, f"{product}\n")
            else:
                if future == futures[0] and petrovich_url:
                    output_text.insert(tk.END, "Ошибка при парсинге данных с сайта Петро́вич.\n")
                elif leroymerlin_url:
                    output_text.insert(tk.END, "Ошибка при парсинге данных с сайта Леруа Мерлен.\n")

    if products:
        save_to_excel(products)


app = tk.Tk()
app.title("Парсер товаров")

tk.Label(app, text="URL Петро́вич:").pack(pady=5)
petrovich_entry = tk.Entry(app, width=50)
petrovich_entry.pack(pady=5)

tk.Label(app, text="URL Леруа Мерлен:").pack(pady=5)
leroymerlin_entry = tk.Entry(app, width=50)
leroymerlin_entry.pack(pady=5)

parse_button = tk.Button(app, text="Запустить парсинг", command=start_parsing)
parse_button.pack(pady=10)

output_text = scrolledtext.ScrolledText(app, width=80, height=20)
output_text.pack(pady=10)

app.mainloop()
