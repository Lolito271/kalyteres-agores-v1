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

    # Step 1: Brainstorm & Category Selection (Categorical Cycling)
    categories = config['content'].get('target_categories', ['Shopping'])
    niche = config['content'].get('niche', 'General')
    now = datetime.now()
    current_year = now.year
    date_str_short = now.strftime("%d/%m")
    
    # Simple Cycling: Look at existing content to pick the least recently used category
    content_dir = "content"
    category = categories[0]
    if os.path.exists(content_dir):
        files = [f for f in os.listdir(content_dir) if f.endswith(".md")]
        if files:
            last_categories = []
            for f in sorted(files, reverse=True)[:10]: # Check last 10 articles
                try:
                    with open(os.path.join(content_dir, f), "r", encoding="utf-8") as file:
                        c = yaml.safe_load(file.read().split('---')[1])['category']
                        last_categories.append(c)
                except: continue
            
            # Find categories not in the last few, or pick the one that appeared longest ago
            for cat in categories:
                if cat not in last_categories:
                    category = cat
                    break
            else:
                # If all categories were used, pick the one that was used the least recently
                category = min(categories, key=lambda x: last_categories.index(x) if x in last_categories else -1)

    # Seasonal Context injection
    season = "Άνοιξη" if 3 <= now.month <= 5 else "Καλοκαίρι" if 6 <= now.month <= 8 else "Φθινόπωρο" if 9 <= now.month <= 11 else "Χειμώνας"
    holidays = "Πάσχα, ανανέωση σπιτιού" if now.month == 3 or now.month == 4 else "Διακοπές, παραλία" if now.month == 6 or now.month == 7 else ""

    prompt_topic = f"""
    Λειτούργησε ως Senior SEO Specialist. 
    Σκέψου ένα θέμα για ένα SEO-optimized άρθρο στο niche: {niche}.
    ΚΑΤΗΓΟΡΙΑ: {category}.
    ΠΕΡΙΟΔΟΣ: {season} {current_year} (Ημερομηνία: {date_str_short}). {holidays}
    
    ΟΔΗΓΙΕΣ ΤΙΤΛΟΥ (Power Words):
    - Χρησιμοποίησε λέξεις όπως: 'Απίστευτο', 'Οικονομικό', 'Οδηγός', 'Λύση', 'Κορυφαίο', 'Που πρέπει να δείτε'.
    - Ο τίτλος πρέπει να είναι "κλικαρίσιμος" και να υπόσχεται λύση σε πρόβλημα.
    - Χρησιμοποίησε αποκλειστικά το έτος {current_year}.
    
    Δώσε την απάντησή σου ΜΟΝΟ σε μορφή JSON:
    {{
        "title": "Ο Τίτλος του Άρθρου",
        "category": "{category}",
        "short_summary": "Teaser 2 προτάσεων με emojis για Facebook",
        "tags": ["Tag1", "Tag2", "StoreNameIfRelevant"]
    }}
    """
    
    response_topic = model.generate_content(prompt_topic)
    try:
        topic_data = json.loads(response_topic.text.strip().replace('```json', '').replace('```', ''))
        title = topic_data['title']
        category = topic_data['category']
        summary = topic_data['short_summary']
        article_tags = topic_data.get('tags', [])
    except:
        title = f"Κορυφαίος Οδηγός Αγοράς για την {season} {current_year}: Λύσεις που Πρέπει να Δείτε"
        category = category
        summary = "Βρείτε τις καλύτερες επιλογές και προσφορές στα κορυφαία καταστήματα! 🚀✨"
        article_tags = [category, "Shopping"]
        
    print(f"Θέμα: {title} | Κατηγορία: {category}")

    # Step 2: Content Generation (SEO Optimized Structure)
    prompt_content = f"""
    Γράψε ένα επαγγελματικό SEO άρθρο (800-1000 λέξεις) για: '{title}'.
    Κατηγορία: {category}
    Εποχή: {season}
    
    ΔΟΜΗ ΑΡΘΡΟΥ (ΥΠΟΧΡΕΩΤΙΚΗ):
    1. # {title}
    2. Εισαγωγή: Εστίασε σε ένα πραγματικό πρόβλημα του αναγνώστη και πώς το θέμα αυτό δίνει τη λύση.
    3. Buyer's Guide Section (H2): Τι πρέπει να προσέξει ο αγοραστής (specs, ποιότητα, τιμή).
    4. Αναλυτική Παρουσίαση (H2): Χρησιμοποίησε H3 για επιμέρους σημεία, Bullet Points και Bold σε σημαντικούς όρους.
    5. Πλεονεκτήματα & Μειονεκτήματα (H2): Μια σύνοψη όσων αναφέρθηκαν.
    6. Συμπέρασμα & Τελική Πρόταση (H2): 1-2 παραγράφους με ξεκάθαρη γνώμη.
    7. Internal Linking: Στο τέλος, πρόσθεσε τη φράση: "Δείτε επίσης περισσότερες προτάσεις στην κατηγορία μας [{category}](https://kalyteres-agores-v1.gr/{slugify(category)}/)".
    
    ΠΡΟΣΟΧΗ:
    - ΜΗΝ αναφέρεις έτη εκτός του {current_year}.
    - Ο τόνος να είναι αυθεντικός, σαν έμπειρος αγοραστής (Authority Voice).
    - ΜΗΝ χρησιμοποιείς generic AI φράσεις όπως "Στον σημερινό κόσμο".
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

    # Step 4: Professional Image Generation (Unique per article)
    try:
        # Use a title-based query + unique signature + professional keywords
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', slugify(title).replace('-', ' '))
        # Adding a timestamp-based signature (sig) and studio keywords for Backup 1 quality
        sig = int(datetime.now().timestamp())
        query = f"{urllib.parse.quote(clean_title)},minimalist,studio,product,high-end,8k"
        image_url = f"https://images.unsplash.com/featured/1600x900/?{query}&sig={sig}"
    except Exception as e:
        print(f"Image generation error: {e}")
        # Fallback to category featured image
        image_url = f"https://images.unsplash.com/featured/1600x900/?{urllib.parse.quote(category.encode('utf-8'))},product"

    summary_escaped = summary.replace('"', '\\"')
    article_tags_json = json.dumps(article_tags, ensure_ascii=False)
    
    full_markdown = f"""---
title: "{title}"
date: "{date_str}"
image_url: "{image_url}"
category: "{category}"
short_summary: "{summary_escaped}"
tags: {article_tags_json}
---

{main_content}
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_markdown)
    
    print(f"Successfully saved to {filename}")

if __name__ == "__main__":
    if not os.path.exists("content"): os.makedirs("content")
    generate_blog_post()
