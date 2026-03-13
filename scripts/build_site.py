import os
import yaml
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader
import re
import shutil

# Load configuration
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

def slugify(text):
    text = text.lower()
    greek_map = {
        'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'i', 'θ': 'th',
        'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p',
        'ρ': 'r', 'σ': 's', 'τ': 't', 'υ': 'y', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
        'ς': 's', 'ά': 'a', 'έ': 'e', 'ή': 'i', 'ί': 'i', 'ό': 'o', 'ύ': 'y', 'ώ': 'o',
        'ϊ': 'i', 'ϋ': 'y', 'ΐ': 'i', 'ΰ': 'y'
    }
    for g, l in greek_map.items():
        text = text.replace(g, l)
    
    # Replace non-alphanumeric with hyphens
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text

def build_site():
    if os.path.exists("public"):
        try:
            # We don't rmtree the whole public to keep .git if it's there
            for item in os.listdir("public"):
                if item == ".git": continue
                path = os.path.join("public", item)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        except Exception as e:
            print(f"Warning during cleanup: {e}")
    else:
        os.makedirs("public")
    
    # Copy Assets
    if os.path.exists("assets"):
        shutil.copytree("assets", "public/assets", dirs_exist_ok=True)
    
    # Create CNAME file
    with open("public/CNAME", "w") as f:
        f.write("kalyteres-agores.gr")
    
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('article.html')
    
    # Prepare categories for navigation
    target_categories_names = config['content'].get('target_categories', [])
    categories_list = [{'name': c, 'url': f"/{slugify(c)}/"} for c in target_categories_names]

    # Process each markdown file in content/
    articles = []
    content_dir = "content"
    
    if not os.path.exists(content_dir):
        os.makedirs(content_dir)
        print("Content directory created. Add .md files there.")
        return

    for filename in os.listdir(content_dir):
        if filename.endswith(".md"):
            try:
                post = frontmatter.load(os.path.join(content_dir, filename))
                
                # Convert markdown to HTML
                html_content = markdown.markdown(post.content)
                
                category = post.get('category', 'Γενικά')
                cat_slug = slugify(category)
                
                # Create category directory
                cat_dir = os.path.join("public", cat_slug)
                if not os.path.exists(cat_dir):
                    os.makedirs(cat_dir)
                
                # Article URL
                article_slug = filename.replace(".md", "")
                output_name = f"{article_slug}.html"
                relative_url = f"{cat_slug}/{output_name}"
                
                final_html = template.render(
                    title=post['title'],
                    date=post['date'],
                    category=category,
                    image_url=post.get('image_url', ''),
                    content=html_content,
                    site_name=config['site']['name'],
                    description=config['site']['description'],
                    site_url=config['site']['url'],
                    asset_path="../assets", # Articles are in subfolders
                    categories=categories_list
                )

                with open(os.path.join(cat_dir, output_name), "w", encoding="utf-8") as f:
                    f.write(final_html)
                
                articles.append({
                    'title': post['title'],
                    'url': relative_url,
                    'date': post['date'],
                    'category': category,
                    'image_url': post.get('image_url', '')
                })
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Sort articles by date descending
    articles.sort(key=lambda x: str(x['date']), reverse=True)

    # Generate Category Indexes
    index_template = env.get_template('index.html')
    for cat in categories_list:
        cat_slug = slugify(cat['name'])
        cat_articles = [a for a in articles if a['category'] == cat['name']]
        
        cat_index_html = index_template.render(
            articles=cat_articles,
            site_name=f"{cat['name']} - {config['site']['name']}",
            description=f"Διαβάστε τα καλύτερα άρθρα για {cat['name']}",
            site_url=config['site']['url'],
            article_url_prefix="", 
            asset_path="../assets",
            categories=categories_list
        )
        cat_dir = os.path.join("public", cat_slug)
        if not os.path.exists(cat_dir):
            os.makedirs(cat_dir)
        with open(os.path.join(cat_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(cat_index_html)

    # Generate Main Index
    index_html = index_template.render(
        articles=articles,
        site_name=config['site']['name'],
        description=config['site']['description'],
        site_url=config['site']['url'],
        article_url_prefix="", # Relative from root
        asset_path="assets", # Index is at root
        categories=categories_list
    )
    
    with open(os.path.join("public", "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    
    print(f"Build complete! {len(articles)} articles generated.")

if __name__ == "__main__":
    build_site()
