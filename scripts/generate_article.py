import os
import yaml
import google.generativeai as genai
from datetime import datetime
import json
import urllib.parse
import re
import sys

# Ensure UTF-8 output
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Load configuration
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# API Key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

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

def generate_blog_post():
    if not GOOGLE_API_KEY:
        print("Error: Missing GOOGLE_API_KEY")
        return

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(config['ai']['model'])

    # Step 1: Brainstorm
    categories = config['content'].get('target_categories', ['Shopping'])
    niche = config['content'].get('niche', 'General')
    current_year = datetime.now().year
    
    prompt_topic = f"""
    Λειτούργησε ως έμπειρος αρχισυντάκτης.
    Σκέψου ένα θέμα για ένα SEO-optimized άρθρο (blog post) στο niche: {niche}.
    Κατηγορία από τη λίστα: {', '.join(categories)}.
    Όπου χρειάζεται (π.χ. στον τίτλο) χρησιμοποίησε αποκλειστικά την τρέχουσα χρονιά ({current_year}). ΠΟΤΕ παλαιότερα έτη.
    
    Δώσε την απάντησή σου ΜΟΝΟ σε μορφή JSON:
    {{
        "title": "Ο Τίτλος του Άρθρου",
        "category": "Η Κατηγορία",
        "short_summary": "Μια σύντομη περιγραφή (1 γραμμή)"
    }}
    """
    
    response_topic = model.generate_content(prompt_topic)
    try:
        topic_data = json.loads(response_topic.text.strip().replace('```json', '').replace('```', ''))
        title = topic_data['title']
        category = topic_data['category']
        summary = topic_data['short_summary']
    except:
        title = "Οδηγός Έξυπνων Αγορών: Ποιοτικά Gadgets για το 2026"
        category = categories[0]
        summary = "Βρείτε τις καλύτερες επιλογές και προσφορές στα κορυφαία καταστήματα."
        
    print(f"Θέμα: {title} | Κατηγορία: {category}")

    # Step 2: Content Generation (Concise 500-700 words)
    prompt_content = f"""
    Γράψε ένα ΣΥΝΤΟΜΟ, ΠΕΡΙΕΚΤΙΚΟ και ΕΓΚΥΡΟ άρθρο (500-700 λέξεις) για: '{title}'.
    Κατηγορία: {category}
    
    ΠΡΟΣΟΧΗ - ΚΡΙΣΙΜΟ:
    Η τρέχουσα χρονιά είναι το {current_year}. Απαγορεύεται αυστηρά να αναφέρεις παλαιότερα έτη όπως 2023, 2024, κλπ. σαν να είναι το παρόν. 
    Όλες οι αναφορές σε "φέτος", "νέα μοντέλα", ή "τάσεις" πρέπει να αφορούν το {current_year}.
    
    Άλλες Οδηγίες: 
    - ΜΗΝ βάλεις συγκεκριμένα links προϊόντων μέσα στο κείμενο.
    - Εστίασε σε συμβουλές αγοράς, χαρακτηριστικά και τι να προσέξει ένας αγοραστής.
    - Χρησιμοποίησε έντονα γράμματα και punchy headings.
    - Στο τέλος του άρθρου, βάλε ΤΟΝ ΕΞΗΣ ΚΩΔΙΚΟ (μην τον αλλάξεις): {{LINKS_HERE}}
    
    Δομή:
    - Εισαγωγή 100 λέξεις.
    - 3-4 βασικά σημεία προσοχής (Short paragraphs).
    - Συμπέρασμα 100 λέξεις.
    - Εικόνα: ![Image](https://images.unsplash.com/featured/?{urllib.parse.quote(category.encode('utf-8'))})
    """
    
    response_content = model.generate_content(prompt_content)
    main_content = response_content.text.strip()

    # Step 3: Smart Affiliate Link Injection (keyword-based matching)
    all_stores = config['affiliate'].get('stores', [])
    
    # Build a searchable text from title + category (lowercase)
    article_text = (title + " " + category).lower()
    
    # Score each store based on how many of its tags appear in the article text
    scored_stores = []
    for store in all_stores:
        score = sum(1 for tag in store.get('tags', []) if tag.lower() in article_text)
        if score > 0:
            scored_stores.append((score, store))
    
    # Sort by score descending, pick top 3
    scored_stores.sort(key=lambda x: x[0], reverse=True)
    top_stores = [s for _, s in scored_stores[:3]]
    
    # If no keyword match found, fallback: pick the first store in the list that matches the category
    if not top_stores:
        cat_lower = category.lower()
        for store in all_stores:
            for tag in store.get('tags', []):
                if tag.lower() in cat_lower or cat_lower in tag.lower():
                    top_stores.append(store)
                    break
            if len(top_stores) >= 2:
                break
    
    # Build markdown links for selected stores
    markdown_links = f"\n\n### 📦 Βρείτε τις καλύτερες επιλογές για {category}:\n\n"
    for store in top_stores:
        aff_url = store['url']
        display_name = store['name']
        markdown_links += f"▶ **[Δείτε τις κορυφαίες επιλογές στο {display_name}]({aff_url})**\n\n"
    
    main_content = main_content.replace("{LINKS_HERE}", markdown_links)

    # Save
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug_val = slugify(title)
    filename = f"content/{date_str}-{slug_val}.md"

    image_url = f"https://images.unsplash.com/photo-1550009158-9ebf69173e03?auto=format&fit=crop&q=80&w=1200"

    full_markdown = f"""---
title: "{title}"
date: "{date_str}"
image_url: "{image_url}"
category: "{category}"
---

{main_content}
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_markdown)
    
    print(f"Successfully saved to {filename}")

if __name__ == "__main__":
    if not os.path.exists("content"): os.makedirs("content")
    generate_blog_post()
