import os
import yaml
import google.generativeai as genai
from datetime import datetime
import json
import urllib.parse
import re
import sys
import frontmatter

# Ensure UTF-8 output
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Load configuration
with open("config.yaml", "r", encoding="utf-8-sig") as f:
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

    # Step 1: Brainstorm Topic
    categories = config['content'].get('target_categories', ['Έξυπνο Σπίτι'])
    category = categories[int(datetime.now().timestamp()) % len(categories)]
    
    prompt_topic = f"""
    Λειτούργησε ως Senior SEO Specialist. 
    Σκέψου ένα θέμα για έναν πλήρη οδηγό αγοράς (discovery guide) στην κατηγορία: {category}.
    Εστίασε σε προϊόντα που αναζητούν οι Έλληνες καταναλωτές το 2026.
    
    Δώσε την απάντησή σου ΜΟΝΟ σε μορφή JSON:
    {{
        "title": "Ο Τίτλος του Άρθρου (π.χ. Τα 5 Καλύτερα Air Fryers το 2026)",
        "short_summary": "Teaser 2 προτάσεων για την αρχική σελίδα",
        "category": "{category}"
    }}
    """
    
    response_topic = model.generate_content(prompt_topic)
    try:
        topic_data = json.loads(response_topic.text.strip().replace('```json', '').replace('```', ''))
        title = topic_data['title']
        summary = topic_data['short_summary']
    except:
        title = f"Κορυφαίος Οδηγός Αγοράς για {category} (2026)"
        summary = "Βρείτε τις καλύτερες επιλογές της αγοράς σήμερα!"

    print(f"Generating: {title}")

    # Step 2: Content Generation (Full-Body Discovery Guide)
    prompt_content = f"""
    Γράψε έναν πλήρη, επαγγελματικό οδηγό αγοράς (1000+ λέξεις) για: '{title}'.
    Κατηγορία: {category}
    
    Η απάντηση πρέπει να είναι ΑΠΟΚΛΕΙΣΤΙΚΑ σε μορφή JSON με την εξής δομή:
    {{
        "intro": "3-4 αναλυτικές παράγραφοι εισαγωγής",
        "buyer_guide_intro": "2 παράγραφοι για το τι πρέπει να προσέξει ο αγοραστής",
        "products": [
            {{
                "name": "Όνομα Προϊόντος 1",
                "score": 9.5,
                "description": "2 αναλυτικές παράγραφοι παρουσίασης",
                "best_for": "Για τι είναι ιδανικό",
                "price_range": "Τιμή (π.χ. 150€ - 200€)",
                "retailer": "Kotsovolos ή E-SHOP ή Amazon",
                "link_type": "product",
                "image_query": "English keywords for Unsplash"
            }},
            {{
                "name": "Όνομα Προϊόντος 2",
                "score": 8.8,
                "description": "2 αναλυτικές παράγραφοι παρουσίασης",
                "best_for": "Οικονομική επιλογή",
                "price_range": "80€ - 120€",
                "retailer": "E-SHOP",
                "link_type": "product",
                "image_query": "English keywords for Unsplash"
            }},
            {{
                "name": "Όνομα Προϊόντος 3",
                "score": 9.2,
                "description": "2 αναλυτικές παράγραφοι παρουσίασης",
                "best_for": "Premium επιλογή",
                "price_range": "300€+",
                "retailer": "Kotsovolos",
                "link_type": "product",
                "image_query": "English keywords for Unsplash"
            }}
        ],
        "comparison_intro": "Ανάλυση σύγκρισης των επιλογών",
        "faq": [
            {{"question": "Ερώτηση 1", "answer": "Απάντηση 1"}},
            {{"question": "Ερώτηση 2", "answer": "Απάντηση 2"}},
            {{"question": "Ερώτηση 3", "answer": "Απάντηση 3"}}
        ],
        "final_recommendation": "Τελικό συμπέρασμα και πρόταση αγοράς"
    }}
    """
    
    response_content = model.generate_content(prompt_content)
    try:
        content_data = json.loads(response_content.text.strip().replace('```json', '').replace('```', ''))
    except:
        print("AI JSON failure.")
        return

    # Step 3: Affiliate & Images
    all_stores = config['affiliate'].get('stores', [])
    for product in content_data.get('products', []):
        retailer_name = product.get('retailer', '').lower()
        matched_store = next((s for s in all_stores if s['name'].lower() in retailer_name or retailer_name in s['name'].lower()), all_stores[0])
        product['affiliate_url'] = matched_store['url']
        product['retailer'] = matched_store['name']
        iq = product.get('image_query', 'gadget')
        product['image_url'] = f"https://images.unsplash.com/featured/800x600/?{urllib.parse.quote(iq)}&sig={int(datetime.now().timestamp())}"

    # Step 4: Save
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug_val = slugify(title)
    filename = f"content/{date_str}-{slug_val}.md"

    article_img = f"https://images.unsplash.com/featured/1600x900/?{urllib.parse.quote(category)}&sig={int(datetime.now().timestamp())}"

    metadata = {
        "title": title,
        "date": date_str,
        "image_url": article_img,
        "category": category,
        "short_summary": summary,
        "type": "discovery",
        "top_pick": content_data['products'][0] if content_data['products'] else None,
        "value_pick": content_data['products'][1] if len(content_data['products']) > 1 else None,
        "budget_pick": content_data['products'][2] if len(content_data['products']) > 2 else None,
        "products": content_data['products'],
        "faq": content_data['faq'],
        "related_pages": []
    }

    body = f"""
{content_data['intro']}

## Οδηγός Αγοράς
{content_data['buyer_guide_intro']}

## Αναλυτική Παρουσίαση
"""
    for p in content_data['products']:
        body += f"### {p['name']}\n{p['description']}\n\n"

    body += f"""
## Σύγκριση & Συμπέρασμα
{content_data['comparison_intro']}

{content_data['final_recommendation']}
"""

    post = frontmatter.Post(body, **metadata)
    with open(filename, "wb") as f:
        frontmatter.dump(post, f)
    
    print(f"Saved: {filename}")

if __name__ == "__main__":
    if not os.path.exists("content"): os.makedirs("content")
    generate_blog_post()
