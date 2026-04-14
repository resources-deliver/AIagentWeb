import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

def send_email(smtp_server: str, smtp_port: int, username: str, password: str, to_addr: str, subject: str, content: str) -> dict:
    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = username
        msg['To'] = to_addr
        msg['Subject'] = Header(subject, 'utf-8')
        send_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(username, password)
            server.sendmail(username, [to_addr], msg.as_string())
        return {
            'status': 'ok',
            'to': to_addr,
            'subject': subject,
            'send_time': send_time,
            'message': f'邮件已成功发送给{to_addr}，主题：{subject}，时间：{send_time}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'to': to_addr,
            'subject': subject,
            'send_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': f'邮件发送失败：{str(e)}'
        }
