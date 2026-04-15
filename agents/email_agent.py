# agents/email_agent.py
import smtplib
from email.mime.text import MIMEText
from src.config import EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD, EMAIL_PREFIX

def send_email(lenders):
    if not lenders: 
        return

    body = ""
    for lender in lenders:
        body += f"{lender['name']}\n"
        body += f"15yr: {lender['15yr']}% | 20yr: {lender['20yr']}% | 30yr: {lender['30yr']}% | Points: {lender['points']}\n\n"

    msg = MIMEText(body)
    msg["Subject"] = EMAIL_PREFIX
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_FROM, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()