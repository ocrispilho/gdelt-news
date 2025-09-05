import requests
import datetime
import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIGURAÇÕES DO EMAIL (via Secrets do GitHub) ===
EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_TO = f"{os.environ['EMAIL_TO']},{os.environ['EMAIL_TO_2']}"
EMAIL_PASS = os.environ["EMAIL_PASS"]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# === CONFIGURAÇÕES DA BUSCA ===
MAXRECORDS = 50  # quantidade máxima de notícias
SEARCH_TERMS = '(SEARCH_TERMS = '("shoppertainment" OR "social commerce" OR "tiktok shop" OR "live streaming" OR "live commerce" OR "shopee live")')'

QUERY_BRASIL = f'{SEARCH_TERMS} sourcecountry:BR'
QUERY_MUNDO = f'{SEARCH_TERMS} -sourcecountry:BR'


# === FUNÇÃO PARA PEGAR NOTÍCIAS DO GDELT ===
def get_gdelt_news(query, startdate, enddate, maxrecords=MAXRECORDS):
    url = (
        f"https://api.gdeltproject.org/api/v2/doc/doc?"
        f"query={query}&mode=artlist&startdatetime={startdate}&enddatetime={enddate}&"
        f"maxrecords={maxrecords}&format=json"
    )
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data.get("articles", [])

# === FUNÇÃO PARA SALVAR EM JSON (opcional, para backup) ===
def save_news(news, tag):
    today = datetime.date.today().isoformat()
    filename = f"gdelt_{tag}_{today}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    return filename

# === FUNÇÃO PARA ENVIAR EMAIL ===
def send_email(news_brasil, news_mundo):
    def format_news_section(news, title):
        if not news:
            return f"<h3>{title}</h3><p>Nenhuma notícia encontrada.</p>"
        body = f"<h3>{title} (total: {len(news)})</h3><ul>"
        for n in news:
            body += f'<li><a href="{n["url"]}">{n["title"]}</a></li>'
        body += "</ul>"
        return body

    body = "<h2>Notícias sobre Shoppertainment</h2>"
    body += format_news_section(news_brasil, "Brasil")
    body += format_news_section(news_mundo, "Mundo (exceto Brasil)")

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = f"Notícias Shoppertainment - {datetime.date.today()}"

    msg.attach(MIMEText(body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.send_message(msg)

# === FLUXO PRINCIPAL ===
if __name__ == "__main__":
    # calcular o dia anterior
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    start = yesterday.strftime("%Y%m%d000000")
    end = yesterday.strftime("%Y%m%d235959")

    # busca Brasil
    news_brasil = get_gdelt_news(QUERY_BRASIL, start, end)
    save_news(news_brasil, "brasil")

    # busca Mundo (exceto Brasil)
    news_mundo = get_gdelt_news(QUERY_MUNDO, start, end)
    save_news(news_mundo, "mundo")

    # envia e-mail único
    send_email(news_brasil, news_mundo)

    print("E-mail enviado com notícias de ontem (Brasil + Mundo).")




