import yaml
import os

def test_encoding():
    print("Testing config.yaml encoding...")
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            cats = config['content']['target_categories']
            print(f"UTF-8: {cats}")
            for c in cats:
                print(f"  {c} -> {c.encode('utf-8').hex()}")
    except Exception as e:
        print(f"UTF-8 failed: {e}")

    try:
        with open("config.yaml", "r", encoding="utf-8-sig") as f:
            config = yaml.safe_load(f)
            cats = config['content']['target_categories']
            print(f"UTF-8-SIG: {cats}")
    except Exception as e:
        print(f"UTF-8-SIG failed: {e}")

if __name__ == "__main__":
    test_encoding()
