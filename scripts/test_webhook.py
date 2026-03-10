import requests
import os
import frontmatter
import yaml

def get_latest_article():
    content_dir = 'content'
    if not os.path.exists(content_dir):
        return None
    articles = [f for f in os.listdir(content_dir) if f.endswith('.md')]
    if not articles:
        return None
    articles.sort(reverse=True)
    return os.path.join(content_dir, articles[0])

def trigger_test_webhook():
    article_path = get_latest_article()
    if not article_path:
        print("No articles found to post.")
        return

    post = frontmatter.load(article_path)
    title = post.get('title', 'Δοκιμαστικό Άρθρο')
    
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    site_url = config.get('site_url', 'https://kalyteres-agores.gr')
    slug = os.path.basename(article_path).replace('.md', '.html')
    link = f"{site_url}/{slug}"

    webhook_url = "https://hook.eu2.make.com/r8z6mi5i3tjp8yn4aydnanijodddo699"

    payload = {
        'title': title,
        'link': link
    }

    print(f"Sending test data to Make.com: {payload}")
    response = requests.post(webhook_url, json=payload)
    if response.status_code == 200:
        print(f"Successfully sent to Make.com: {response.text}")
    else:
        print(f"Failed to send to Make.com: {response.status_code} - {response.text}")

if __name__ == "__main__":
    trigger_test_webhook()
