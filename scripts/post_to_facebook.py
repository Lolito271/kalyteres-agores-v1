import requests
import os
import frontmatter
import yaml

def get_latest_article():
    content_dir = 'content'
    articles = [f for f in os.listdir(content_dir) if f.endswith('.md')]
    if not articles:
        return None
    # Sort by filename (assumes YYYY-MM-DD-...)
    articles.sort(reverse=True)
    return os.path.join(content_dir, articles[0])

def post_to_facebook():
    article_path = get_latest_article()
    if not article_path:
        print("No articles found to post.")
        return

    # Load article data
    post = frontmatter.load(article_path)
    title = post.get('title', 'Νέο άρθρο!')
    
    # Load config for site URL
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    site_url = config.get('site_url', 'https://kalyteres-agores.gr')
    slug = os.path.basename(article_path).replace('.md', '.html')
    link = f"{site_url}/{slug}"

    # Get webhook URL from environment
    webhook_url = os.environ.get('MAKE_WEBHOOK_URL')

    if not webhook_url:
        print("Make.com Webhook URL not found in environment variables.")
        return

    payload = {
        'title': title,
        'link': link
    }

    response = requests.post(webhook_url, json=payload)
    if response.status_code == 200:
        print(f"Successfully sent to Make.com: {response.text}")
    else:
        print(f"Failed to send to Make.com: {response.text}")

if __name__ == "__main__":
    post_to_facebook()
