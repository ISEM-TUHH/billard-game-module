import smtplib
from email.message import EmailMessage
import os
from io import BytesIO

def send_message(text, subject, df=None):
    mto = os.getenv("MAIL_TO")
    mfrom = os.getenv("MAIL_FROM")
    server = os.getenv("MAIL_SERVER")
    port = os.getenv("MAIL_PORT")
    user = os.getenv("MAIL_USER")
    auth = os.getenv("MAIL_PW")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mfrom
    msg["To"] = [mto]

    if not df is None:
        #att = BytesIO()
        att = df.to_csv(index=False, sep="\t")

        text += "\n\nAttached table:\n" + att
        msg.set_content(text)

        msg.add_attachment(att, subtype="csv", filename="scores")
    else:
        msg.set_content(text)

    with smtplib.SMTP(server, port) as smtp:
        print(server)
        smtp.connect(host=server, port=port)
        smtp.starttls()  # Secure the connection
        smtp.login(user, auth)
        smtp.send_message(msg)
        #smtp.sendmail(mfrom, [mto], msg.as_string())

if __name__=="__main__":
    import pandas as pd

    attachment = pd.DataFrame({"a": [1,2], "b": [3,4]})

    send_message("Hello there", "Hello from python!", df=attachment)