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
    # Generate link (assuming slug-based naming)
    # The build script uses the base name of the md file
    slug = os.path.basename(article_path).replace('.md', '.html')
    link = f"{site_url}/{slug}"

    # Get credentials from environment
    page_id = os.environ.get('FB_PAGE_ID')
    access_token = os.environ.get('FB_PAGE_ACCESS_TOKEN')

    if not page_id or not access_token:
        print("Facebook credentials not found in environment variables.")
        return

    message = f"🚀 {title}\n\nΔιαβάστε το νέο μας άρθρο εδώ: {link}"
    
    url = f"https://graph.facebook.com/v22.0/{page_id}/feed"
    payload = {
        'message': message,
        'link': link,
        'access_token': access_token
    }

    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(f"Successfully posted to Facebook: {response.json()}")
    else:
        print(f"Failed to post to Facebook: {response.text}")

if __name__ == "__main__":
    post_to_facebook()
