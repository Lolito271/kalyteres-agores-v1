import os
import yaml
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader

# Load configuration
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

def build_site():
    if not os.path.exists("public"):
        os.makedirs("public")
    
    # Copy Assets
    import shutil
    if os.path.exists("assets"):
        if os.path.exists("public/assets"):
            try:
                shutil.rmtree("public/assets")
            except Exception as e:
                print(f"Warning: Could not remove public/assets: {e}")
        try:
            shutil.copytree("assets", "public/assets", dirs_exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not copy assets: {e}")
    
    # Create CNAME file
    with open("public/CNAME", "w") as f:
        f.write("kalyteres-agores.gr")
    
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('article.html')

    # Process each markdown file in content/
    articles = []
    for filename in os.listdir("content"):
        if filename.endswith(".md"):
            post = frontmatter.load(os.path.join("content", filename))
            
            # Convert markdown to HTML
            html_content = markdown.markdown(post.content)
            
            # Replace [LINK_HERE] with actual affiliate ID link integration (simplified for now)
            aff_id = config['affiliate']['id']
            # We will evolve this to dynamically find products later
            
            final_html = template.render(
                title=post['title'],
                date=post['date'],
                image_url=post.get('image_url', ''),
                content=html_content,
                site_name=config['site']['name'],
                description=config['site']['description']
            )

            output_name = filename.replace(".md", ".html")
            with open(os.path.join("public", output_name), "w", encoding="utf-8") as f:
                f.write(final_html)
            
            articles.append({
                'title': post['title'],
                'url': output_name,
                'date': post['date'],
                'image_url': post.get('image_url', '')
            })

    # Sort articles by date descending
    articles.sort(key=lambda x: x['date'], reverse=True)

    # Generate Index
    index_template = env.get_template('index.html')
    index_html = index_template.render(
        articles=articles,
        site_name=config['site']['name'],
        description=config['site']['description']
    )
    
    with open(os.path.join("public", "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    
    print("Build complete! Files generated in public/")

if __name__ == "__main__":
    build_site()
