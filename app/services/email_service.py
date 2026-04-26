import os
import smtplib
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import markdown

load_dotenv()

MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")


def send_email(subject: str, body_text: str, body_html: str = None, recipients: list = None):
    if recipients is None:
        if not MY_EMAIL:
            raise ValueError("MY_EMAIL environment variable is not set")
        recipients = [MY_EMAIL]
    
    recipients = [r for r in recipients if r is not None]
    if not recipients:
        raise ValueError("No valid recipients provided")
    
    if not MY_EMAIL:
        raise ValueError("MY_EMAIL environment variable is not set")
    if not APP_PASSWORD:
        raise ValueError("APP_PASSWORD environment variable is not set")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = MY_EMAIL
    msg["To"] = ", ".join(recipients)
    
    part1 = MIMEText(body_text, "plain")
    msg.attach(part1)
    
    if body_html:
        part2 = MIMEText(body_html, "html")
        msg.attach(part2)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(MY_EMAIL, APP_PASSWORD)
        smtp.sendmail(MY_EMAIL, recipients, msg.as_string())


def markdown_to_html(markdown_text: str) -> str:
    html = markdown.markdown(markdown_text, extensions=['extra', 'nl2br'])
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
        }}
        h2 {{
            font-size: 18px;
            font-weight: 600;
            color: #1a1a1a;
            margin-top: 24px;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        h3 {{
            font-size: 16px;
            font-weight: 600;
            color: #1a1a1a;
            margin-top: 20px;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        p {{
            margin: 8px 0;
            color: #4a4a4a;
        }}
        strong {{
            font-weight: 600;
            color: #1a1a1a;
        }}
        em {{
            font-style: italic;
            color: #666;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
            font-weight: 500;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e5e5e5;
            margin: 20px 0;
        }}
        .greeting {{
            font-size: 16px;
            font-weight: 500;
            color: #1a1a1a;
            margin-bottom: 12px;
        }}
        .introduction {{
            color: #4a4a4a;
            margin-bottom: 20px;
        }}
        .article-link {{
            display: inline-block;
            margin-top: 8px;
            color: #0066cc;
            font-size: 14px;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>"""


def digest_to_html(digest_response) -> str:
    from app.agent.email_agent import EmailDigestResponse
    
    if not isinstance(digest_response, EmailDigestResponse):
        return markdown_to_html(digest_response.to_markdown() if hasattr(digest_response, 'to_markdown') else str(digest_response))
    
    html_parts = []
    
    # Render Header
    html_parts.append('''
        <div class="header">
            <h1 style="color: #ffffff; margin: 0; font-size: 24px;">🧠 AI News Digest</h1>
        </div>
        <div class="content">
    ''')
    
    # Render Introduction
    greeting_html = markdown.markdown(digest_response.introduction.greeting, extensions=['extra', 'nl2br'])
    introduction_html = markdown.markdown(digest_response.introduction.introduction, extensions=['extra', 'nl2br'])
    html_parts.append(f'<div class="greeting">{greeting_html}</div>')
    html_parts.append(f'<div class="introduction">{introduction_html}</div>')
    
    # Render Articles
    for article in digest_response.articles:
        html_parts.append('<div class="article-card">')
        html_parts.append(f'<h3><a href="{html.escape(article.url)}" style="color: #0f172a;">{html.escape(article.title)}</a></h3>')
        
        # Add a "Relevance" badge
        html_parts.append(f'<span class="badge">🎯 Match Score: {article.relevance_score:.1f}/10</span>')
        
        summary_html = markdown.markdown(article.summary, extensions=['extra', 'nl2br'])
        html_parts.append(f'<div class="summary">{summary_html}</div>')
        
        # Reasoning block
        if article.reasoning:
            reasoning_html = markdown.markdown(article.reasoning, extensions=['extra', 'nl2br'])
            html_parts.append(f'''
                <div class="reasoning-block">
                    <strong>💡 Why this matters for you:</strong>
                    <div>{reasoning_html}</div>
                </div>
            ''')
            
        html_parts.append(f'<p><a href="{html.escape(article.url)}" class="article-link">Read full research &rarr;</a></p>')
        html_parts.append('</div>')
    
    html_parts.append('</div>') # Close content
    html_parts.append('<div class="footer">Generated specifically for your expertise by your AI Agent 🤖</div>')
    
    html_content = '\n'.join(html_parts)
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f7f6; }}
        .container {{ max-width: 650px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        .header {{ background: linear-gradient(135deg, #0f172a 0%, #334155 100%); padding: 30px 20px; text-align: center; }}
        .content {{ padding: 30px; }}
        h3 {{ font-size: 20px; font-weight: 600; color: #0f172a; margin-top: 0; margin-bottom: 12px; line-height: 1.4; }}
        p {{ margin: 8px 0; color: #475569; }}
        a {{ color: #2563eb; text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        .greeting {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 15px; }}
        .greeting p {{ margin: 0; color: #0f172a; font-size: inherit; font-weight: inherit; }}
        .introduction {{ font-size: 15px; color: #334155; margin-bottom: 30px; padding: 20px; background-color: #f8fafc; border-radius: 8px; border-left: 4px solid #3b82f6; }}
        .article-card {{ margin-bottom: 35px; padding-bottom: 30px; border-bottom: 1px solid #e2e8f0; }}
        .article-card:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
        .badge {{ display: inline-block; background-color: #e0f2fe; color: #0369a1; padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600; margin-bottom: 15px; }}
        .summary {{ font-size: 15px; color: #475569; margin-bottom: 15px; }}
        .reasoning-block {{ background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 15px; margin: 15px 0; }}
        .reasoning-block strong {{ font-size: 13px; color: #b45309; display: block; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .reasoning-block div {{ font-size: 14px; color: #92400e; }}
        .article-link {{ display: inline-block; font-size: 14px; font-weight: 600; color: #2563eb; margin-top: 10px; background-color: #eff6ff; padding: 8px 16px; border-radius: 6px; }}
        .article-link:hover {{ background-color: #dbeafe; text-decoration: none; }}
        .footer {{ text-align: center; font-size: 13px; color: #64748b; padding: 25px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; }}
    </style>
</head>
<body>
    <div class="container">
{html_content}
    </div>
</body>
</html>"""


def send_email_to_self(subject: str, body: str):
    if not MY_EMAIL:
        raise ValueError("MY_EMAIL environment variable is not set. Please set it in your .env file.")
    send_email(subject, body, recipients=[MY_EMAIL])


if __name__ == "__main__":
    send_email_to_self("Test from Python", "Hello from my script.")