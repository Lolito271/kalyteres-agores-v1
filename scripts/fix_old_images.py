import os
import frontmatter
import urllib.parse

def fix_images():
    content_dir = "content"
    if not os.path.exists(content_dir):
        print("Content directory not found.")
        return

    for filename in os.listdir(content_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(content_dir, filename)
            try:
                post = frontmatter.load(filepath)
                
                # Get keywords for image
                tags = post.get('tags', [])
                category = post.get('category', 'shopping')
                
                # Use tags if available, else category
                image_keywords = ",".join(tags[:3]) if tags else category
                
                # Direct Unsplash Source URL as requested
                new_image_url = f"https://source.unsplash.com/featured/?{urllib.parse.quote(image_keywords.encode('utf-8'))}"
                
                print(f"Updating {filename} with keywords: {image_keywords}")
                
                post['image_url'] = new_image_url
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(frontmatter.dumps(post))
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    fix_images()
