import smtplib
import cloudscraper
import re
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from scrapper_secrets import SENDER_EMAIL, RECEIVER_EMAIL, EMAIL_PASSWORD

TIME_BETWEEN_TRIES = 20

logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

def check_prices():
    products = []

    product_list = [
        {
            'item_name': 'RTX 4080',
            'url': 'https://www.pccomponentes.com/tarjetas-graficas/geforce-rtx-4080-super',
            'name_pattern': r'<h3[^>]*data-e2e="title-card"[^>]*>(.*?)</h3>',
            'price_pattern': r'<span[^>]*data-e2e="price-card"[^>]*>([\d.,]+)€</span>'
        },
        {
            'item_name': 'RAM DDR5',
            'url': 'https://www.pccomponentes.com/memorias-ram/6400-mhz/ddr5/kit-2x32gb',
            'name_pattern': r'<h3[^>]*data-e2e="title-card"[^>]*>(.*?)</h3>',
            'price_pattern': r'<span[^>]*data-e2e="price-card"[^>]*>([\d.,]+)€</span>'
        },
        {
            'item_name': 'Fuente de alimentación 1000W Platinum',  
            'url': 'https://www.pccomponentes.com/fuentes-alimentacion/1000w/80-plus-platinum',
            'name_pattern': r'<h3[^>]*data-e2e="title-card"[^>]*>(.*?)</h3>',
            'price_pattern': r'<span[^>]*data-e2e="price-card"[^>]*>([\d.,]+)€</span>'
        },
    ]

    for product in product_list:
        product_price = check_custom_price(**product)

        if product_price:
            products.append(product_price)

    logger.info(f"Productos encontrados: {products}")
    
    if products:
        send_email(products)
    else:
        logger.info("No se encontraron productos para enviar por email.")
    
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
                    logger.info(f"Productos encontrados para {item_name}: {products}")
                    retry = False

                    best_product = min(products, key=lambda x: x[1])
                    logger.info(f"El mejor precio para {item_name} es: {best_product[1]}€ para el producto: {best_product[0]}")
                    return best_product
                else:
                    logger.info(f"No se encontraron productos o precios para {item_name}.")
                    if retry:
                        logger.info(f"Reintentando... Esperando {TIME_BETWEEN_TRIES} segundos antes de la siguiente petición...")
                        
                    return None
            except Exception as e:
                logger.error(f"Error obteniendo los precios de {item_name}: {e}")
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
        
        logger.info("Correo enviado correctamente.")
    except Exception as e:
        logger.error(f"Error al enviar el correo: {e}")


if __name__ == "__main__":
    check_prices()

