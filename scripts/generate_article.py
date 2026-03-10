import os
import yaml
import google.generativeai as genai
from datetime import datetime

# Load configuration
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Hardcoded for now, will use environment variables later for GitHub Actions
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

def generate_blog_post():
    if not GOOGLE_API_KEY:
        print("Error: Missing GOOGLE_API_KEY")
        return

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(config['ai']['model'])

    # Step 1: Brainstorm a topic based on niche and categories
    categories = ", ".join(config['content'].get('target_categories', []))
    prompt_topic = f"""
    Είσαι ένας έμπειρος Έλληνας affiliate marketer. 
    Το niche του site μας είναι: {config['content']['niche']}.
    Οι βασικές κατηγορίες που μας ενδιαφέρουν είναι: {categories}.
    
    Σκέψου ένα επίκαιρο, πιασάρικο θέμα για ένα νέο άρθρο στην Ελλάδα που θα βοηθήσει τον κόσμο να εξοικονομήσει χρήματα ή να κάνει μια έξυπνη αγορά. 
    Προσπάθησε να επιλέγεις κάθε φορά διαφορετική κατηγορία για να υπάρχει ποικιλία.
    Επίπεσε μόνο τον τίτλο του άρθρου στα Ελληνικά.
    """
    
    response_topic = model.generate_content(prompt_topic)
    title = response_topic.text.strip().replace('"', '')
    print(f"Θέμα που επιλέχθηκε: {title}")

    # Step 2: Write the full SEO optimized article
    prompt_content = f"""
    Γράψε ένα πλήρες άρθρο ιστολογίου σε Markdown για τον τίτλο: '{title}'.
    
    Προδιαγραφές:
    1. Γλώσσα: Ελληνικά.
    2. Στυλ: Επαγγελματικό αλλά φιλικό, σαν "έμπειρος οδηγός".
    3. Δομή:
       - Εισαγωγή που εξηγεί το πρόβλημα.
       - H2 επικεφαλίδες για ανάλυση.
       - Λίστα με πλεονεκτήματα/μειονεκτήματα.
       - Μία ενότητα με "Προτεινόμενα Προϊόντα".
       - Συμπέρασμα.
    4. SEO: Χρησιμοποίησε σχετικές λέξεις-κλειδιά.
    5. Affiliate Links: Εκεί που προτείνεις προϊόντα, βάλε placeholders όπως [LINK_HERE].
    6. ΑΠΑΓΟΡΕΥΣΕΙΣ:
       - ΜΗΝ αναφέρεις ενότητα σχολίων ή "γράψτε στα σχόλια" (δεν υπάρχει τέτοια λειτουργία).
       - ΜΗΝ χρησιμοποιείς placeholders όπως [ΕΔΩ ΜΠΑΙΝΕΙ Η ΦΩΤΟΓΡΑΦΙΑ].
       - ΜΗΝ βάζεις "Σημειώσεις για τον συντάκτη".
    
    Μην βάλεις Frontmatter (---), μόνο το κυρίως κείμενο σε Markdown.
    """
    
    response_content = model.generate_content(prompt_content)
    main_content = response_content.text.strip()

    # Step 2.5: Generate image keyword based on title
    prompt_image = f"Δώσε μου μία μόνο λέξη στα Αγγλικά (keyword) που να περιγράφει το θέμα του άρθρου '{title}' για να βρω μια σχετική εικόνα στο Unsplash. Μόνο τη λέξη."
    response_image = model.generate_content(prompt_image)
    image_keyword = response_image.text.strip().lower()
    image_url = f"https://images.unsplash.com/photo-1558403194-611308249627?auto=format&fit=crop&w=1200&q=80" # Default
    if image_keyword:
        image_url = f"https://source.unsplash.com/featured/1200x800?{image_keyword}"

    # Step 3: Save to file
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Better sanitization for Greek characters and Windows filenames
    def slugify(text):
        # Keep letters and numbers, replace space with -
        import re
        text = text.lower()
        # Remove invalid characters for Windows filenames
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Handle Greek/Other chars by just keeping alphanumeric and basic symbols
        # But for Windows we mostly care about the characters above. 
        # Let's replace spaces with hyphens
        text = text.replace(" ", "-")
        # Remove markdown bold/italics
        text = text.replace("*", "").replace("_", "")
        return text[:50]

    slug = slugify(title)
    filename = f"content/{date_str}-{slug}.md"

    # Add Frontmatter manually
    full_markdown = f"""---
title: "{title}"
date: "{date_str}"
image_url: "{image_url}"
---

{main_content}
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_markdown)
    
    print(f"Το άρθρο αποθηκεύτηκε: {filename}")

if __name__ == "__main__":
    # Ensure content directory exists
    if not os.path.exists("content"):
        os.makedirs("content")
    generate_blog_post()
