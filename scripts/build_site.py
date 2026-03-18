import os
import yaml
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader
import re
import shutil

# Load configuration
with open("config.yaml", "r", encoding="utf-8-sig") as f:
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
        for item in os.listdir("public"):
            if item == ".git": continue
            path = os.path.join("public", item)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
            except Exception as e:
                print(f"Skipping {item} due to lock/error: {e}")
    else:
        os.makedirs("public")
    
    # Image Fallbacks
    IMAGE_FALLBACKS = {
        'Έξυπνο Σπίτι': 'https://images.unsplash.com/photo-1558002038-103792e17734?q=80&w=1600',
        'Gadgets & Τεχνολογία': 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=1600',
        'Υγεία & Ευεξία': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=1600',
        'Σπίτι & Κήπος': 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?q=80&w=1600',
        'default': 'https://images.unsplash.com/photo-1510033331526-dca71429074b?q=80&w=1600'
    }

    # Approved Categories
    target_categories_names = config['content'].get('target_categories', [])
    approved_cats = set(target_categories_names)
    
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
    categories_list = []
    approved_cats_slugs = set()
    for c in target_categories_names:
        c_name = str(c).strip()
        c_slug = slugify(c_name)
        categories_list.append({'name': c_name, 'url': f"/{c_slug}/", 'slug': c_slug})
        approved_cats_slugs.add(c_slug)

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
                with open(os.path.join(content_dir, filename), "r", encoding="utf-8-sig") as f:
                    post = frontmatter.load(f)
                
                # Clean up metadata
                title = str(post.get('title', '')).strip()
                category = str(post.get('category', 'Γενικά')).strip()
                cat_slug = slugify(category)
                
                # Convert markdown to HTML
                html_content = markdown.markdown(post.content)
                
                if cat_slug not in approved_cats_slugs:
                    print(f"Skipping {filename}: Category '{category}' (slug: {cat_slug}) not in approved list.")
                    continue

                cat_slug = slugify(category)
                
                # Create category directory
                cat_dir = os.path.join("public", cat_slug)
                if not os.path.exists(cat_dir):
                    os.makedirs(cat_dir)
                
                # Image Logic
                image_url = post.get('image_url')
                if not image_url or image_url.strip() == "":
                    image_url = IMAGE_FALLBACKS.get(category, IMAGE_FALLBACKS['default'])

                # Article URL
                article_slug = filename.replace(".md", "")
                output_name = f"{article_slug}.html"
                relative_url = f"{cat_slug}/{output_name}"
                
                # Select template based on page type
                page_type = post.get('type', 'article')
                if page_type == 'discovery':
                    active_template = env.get_template('discovery.html')
                else:
                    active_template = env.get_template('article.html')
                
                final_html = active_template.render(
                    title=title,
                    date=post['date'],
                    category=category,
                    image_url=image_url,
                    content=html_content,
                    # Discovery specific data
                    type=page_type,
                    short_summary=post.get('short_summary', ''),
                    intro=post.get('intro', ''),
                    buyer_guide_intro=post.get('buyer_guide_intro', ''),
                    comparison_intro=post.get('comparison_intro', ''),
                    final_recommendation=post.get('final_recommendation', ''),
                    top_pick=post.get('top_pick'),
                    value_pick=post.get('value_pick'),
                    budget_pick=post.get('budget_pick'),
                    products=post.get('products', []),
                    faq=post.get('faq', []),
                    related_pages=post.get('related_pages', []),
                    # Global data
                    site_name=config['site']['name'],
                    description=config['site']['description'],
                    site_url=config['site']['url'],
                    asset_path="../assets", # Articles are in subfolders
                    categories=categories_list
                )

                with open(os.path.join(cat_dir, output_name), "w", encoding="utf-8") as f:
                    f.write(final_html)
                
                articles.append({
                    'title': title,
                    'url': relative_url,
                    'date': post['date'],
                    'category': category,
                    'image_url': image_url,
                    'type': page_type,
                    'short_summary': post.get('short_summary', '')
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
            posts=cat_articles,
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
        posts=articles,
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
