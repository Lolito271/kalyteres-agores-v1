import requests
import os
import frontmatter
import yaml
import re

def slugify(text):
    text = text.lower()
    greek_map = {
        'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'i', 'θ': 'th',
        'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p',
        'ρ': 'r', 'σ': 's', 'τ': 't', 'υ': 'y', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
        'ς': 's', 'ά': 'a', 'έ': 'e', 'ή': 'i', 'ί': 'i', 'ό': 'o', 'ύ': 'y', 'ώ': 'o',
        'ϊ': 'i', 'ϋ': 'y', 'ΐ': 'i', 'ΰ': 'y'
    }
    for g, l in greek_map.items(): text = text.replace(g, l)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text

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
    
    site_url = config['site']['url']
    
    # Extract category to match the new dynamic routing
    category = post.get('category', 'Γενικά')
    cat_slug = slugify(category)
    slug = os.path.basename(article_path).replace('.md', '.html')
    
    print(f"DEBUG: Processing article: {title}")
    
    # Secure link construction (no double slashes)
    link = f"{site_url.rstrip('/')}/{cat_slug}/{slug}"
    print(f"DEBUG: Constructed Facebook Link: {link}")
    
    # Get webhook URL from environment
    webhook_url = os.environ.get('MAKE_WEBHOOK_URL')

    if not webhook_url:
        print("ERROR: MAKE_WEBHOOK_URL not found.")
        return

    payload = {
        'title': title,
        'link': link,
        'teaser': post.get('short_summary', ''),
        'image_url': post.get('image_url', ''),
        'date': str(post.get('date', '')),
        'author': post.get('author', ''),
        'tags': ', '.join(post.get('tags', [])) if isinstance(post.get('tags'), list) else str(post.get('tags', ''))
    }

    try:
        print("DEBUG: Sending payload to Make.com...")
        response = requests.post(webhook_url, json=payload, timeout=15)
        print(f"DEBUG: Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"SUCCESS: Sent to Facebook via Make.com. Response: {response.text}")
        else:
            print(f"FAILED: status {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")

if __name__ == "__main__":
    post_to_facebook()
