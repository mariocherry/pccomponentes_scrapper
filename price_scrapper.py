import smtplib
import cloudscraper
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from scrapper_secrets import SENDER_EMAIL, RECEIVER_EMAIL, EMAIL_PASSWORD

TIME_BETWEEN_REQUESTS = 20
TIME_BETWEEN_TRIES = 20

def check_prices():
    products = []

    rtx_4080_price = check_custom_price(
        item_name='RTX 4080',
        url='https://www.pccomponentes.com/tarjetas-graficas/geforce-rtx-4080-super',
        name_pattern = r'<h3[^>]*data-e2e="title-card"[^>]*>(.*?)</h3>',
        price_pattern = r'<span[^>]*data-e2e="price-card"[^>]*>([\d.,]+)€</span>'
    )

    if rtx_4080_price:
        products.append(rtx_4080_price)

    print(f"Esperando {TIME_BETWEEN_REQUESTS} segundos antes de la siguiente petición...")
    time.sleep(TIME_BETWEEN_REQUESTS)

    ram_ddr5_price = check_custom_price(
        item_name='RAM DDR5',
        url='https://www.pccomponentes.com/memorias-ram/6400-mhz/ddr5/kit-2x32gb',
        name_pattern=r'<h3[^>]*data-e2e="title-card"[^>]*>(.*?)</h3>',
        price_pattern=r'<span[^>]*data-e2e="price-card"[^>]*>([\d.,]+)€</span>'
    )

    if ram_ddr5_price:
        products.append(ram_ddr5_price)

    print(f"Productos encontrados: {products}")
    
    if products:
        send_email(products)
    else:
        print("No se encontraron productos para enviar por email.")
    
def check_custom_price(item_name: str, url: str, name_pattern: str, price_pattern: str):
    retries = 2
    retry = True
    for _ in range(retries):
        if retry:
            try:
                scraper = cloudscraper.create_scraper()
                response = scraper.get(url)

                names = re.findall(name_pattern, response.text)
                prices = re.findall(price_pattern, response.text)

                if names and prices:
                    numeric_prices = [float(price.replace('.', '').replace(',', '.')) for price in prices]

                    products = list(zip(names, numeric_prices))
                    print(f"Productos encontrados para {item_name}: {products}")
                    retry = False

                    best_product = min(products, key=lambda x: x[1])
                    print(f"El mejor precio para {item_name} es: {best_product[1]}€ para el producto: {best_product[0]}")
                    return best_product
                else:
                    print(f"No se encontraron productos o precios para {item_name}.")
                    if retry:
                        print(f"Reintentando... Esperando {TIME_BETWEEN_TRIES} segundos antes de la siguiente petición...")
                    return None
            except Exception as e:
                print(f"Error obteniendo los precios de {item_name}: {e}")
                return None
        
    
def send_email(products):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        
        message = MIMEMultipart()
        message['From'] = SENDER_EMAIL
        message['To'] = RECEIVER_EMAIL
        message['Subject'] = "Actualización de precios de productos"

        body = "Aquí tienes los mejores precios encontrados:\n\n"
        
        for name, price in products:
            body += f"Producto: {name}\n"
            body += f"Precio: {price}€\n"
            body += "-" * 50 + "\n"

        message.attach(MIMEText(body, 'plain', 'utf-8'))

        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        server.quit()
        
        print("Correo enviado correctamente.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


if __name__ == "__main__":
    check_prices()
