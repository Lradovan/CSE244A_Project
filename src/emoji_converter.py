import json
from PIL import Image 

import numpy as np
import os
from skimage import color
import emojis

emoji_dir = "./emojis/"
curated_names_file = "./curated_names.txt"
emoji_list_file = "./emojis/LIST_OF_EMOJI.txt"
output_file = "emoji_data.jsonl"
THRESHOLD = 30

emoji_ascii_map = {
    "🟥": '@',
    "🟧": '%',
    "🟨": '*',
    "🟩": '+',
    "🟦": '=',
    "🟪": '-',
    "⬛": ':',
    "🟫": '#',
    "⬜": '.' 
}

palette = {
    "🟥": np.array([222, 37, 43, 255]), 
    "🟧": np.array([255, 125, 41, 255]),
    "🟨": np.array([253, 203, 50, 255]),
    "🟩": np.array([59, 183, 95, 255]),
    "🟦": np.array([47, 112, 205, 255]),
    "🟪": np.array([151, 75, 181, 255]),
    "⬛": np.array([44, 44, 46, 255]),
    "🟫": np.array([121, 70, 45, 255]),
    "⬜": np.array([242, 242, 243, 255])
}

FULL_SPACE = "　"

def resize_with_padding(img, size=10):
    """Resize the image to fit inside size×size while preserving aspect ratio.
       Pads with transparency so the final image is exactly size×size."""

    img = img.convert("RGBA")
    w, h = img.size
    scale = size / max(w, h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    # Resize while preserving aspect ratio
    img_resized = img.resize((new_w, new_h), Image.Resampling.NEAREST)

    # Create a padded canvas
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))  

    # Center the resized image inside it
    offset_x = (size - new_w) // 2
    offset_y = (size - new_h) // 2
    canvas.paste(img_resized, (offset_x, offset_y))

    return canvas

def closest_emoji(color, palette):
    diffs = [delta_e_distance(color, v) for v in palette.values()]
    emojis = list(palette.keys())
    return min(diffs), emojis[np.argmin(diffs)]

def rgb_to_lab(rgb_color):
    rgb = np.array(rgb_color[:3]).reshape(1, 1, 3) / 255.0
    return color.rgb2lab(rgb)

def delta_e_distance(color1, color2):

    lab1 = rgb_to_lab(color1)
    lab2 = rgb_to_lab(color2)
    return color.deltaE_ciede2000(lab1, lab2)[0][0]

def create_art(img, palette):

    img = resize_with_padding(img, size=10)

    colors = set()
    arr = np.array(img)
    emoji_grid = []
    ascii_grid = []
    diffs = []
    for row in arr:
        emoji_line = ""
        ascii_line = ""
        for pixel in row:
            if pixel[3] < 128:
                emoji_line += FULL_SPACE
                ascii_line += FULL_SPACE
            else:
                diff, e = closest_emoji(pixel, palette)
                diffs.append(diff)
                emoji_line += e
                ascii_line += emoji_ascii_map[e] * 2
                colors.add(e)
        emoji_grid.append(emoji_line)
        ascii_grid.append(ascii_line)
    avg_diff = np.mean(diffs)
    return avg_diff, "\n".join(emoji_grid), "\n".join(ascii_grid), colors

def get_emoji_safe(ch):
    e = emojis.db.get_emoji_by_code(ch)
    if e is None and not ch.endswith("\ufe0f"):
        e = emojis.db.get_emoji_by_code(ch + "\ufe0f")
    return e

# set of names that avoid gender specific or duplicate emojis
def get_curated_names():
    with open(curated_names_file, "r") as f:
        names = set(line.strip() for line in f)

    return names

def load_emoji_names(list_file):
    """Load emoji names from the LIST_OF_EMOJI.txt file"""
    emoji_map = {}
    cat_map = {}
    with open(list_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or ' - ' not in line:
                continue
            
            parts = line.split(' - ')
            if len(parts) >= 3:
                emoji_char = parts[0].strip()
                emoji_name = parts[1].strip()
                filename = parts[2].strip()
                emoji_obj = get_emoji_safe(emoji_char)

                if emoji_obj:
                    emoji_cat = emoji_obj.category
                    unicode_code = filename.replace('.png', '')
                    emoji_map[unicode_code] = (emoji_name, emoji_char, emoji_cat)
                    if emoji_cat not in cat_map:
                        cat_map[emoji_cat] = [emoji_name]
                    else:
                        cat_map[emoji_cat].append(emoji_name)

    return emoji_map, cat_map

# Load the emoji name mapping
print("Loading emoji names...")
emoji_name_map, cat_map = load_emoji_names(emoji_list_file)
print(f"Loaded {len(emoji_name_map)} emoji names")

# load curated names
curated_names = get_curated_names()

# Process all emojis and write to JSONL
successful = 0
failed = 0
missing_names = 0

with open(output_file, 'w', encoding='utf-8') as f:
    for fname in sorted(os.listdir(emoji_dir)):
        if not fname.endswith(".png"):
            continue
        
        try:
            path = os.path.join(emoji_dir, fname)
            img = Image.open(path).convert("RGBA")
            
            unicode_code = fname[:-4]  # Remove .png
            emoji_name, emoji_char, emoji_cat = emoji_name_map.get(unicode_code)

            if emoji_name not in curated_names:
                continue
            
            if not emoji_name:
                missing_names += 1
                print(f"⚠ Missing name for: {unicode_code}")
                emoji_name = f"emoji {unicode_code}"
            
            avg_diff, emoji_art, ascii_art, colors = create_art(img, palette)
            if avg_diff > THRESHOLD:
                raise Exception("Color difference exceeded threshold")
            
            # Create training example in chat format
            training_example = {
                "name": emoji_name,
                "unicode": unicode_code,
                "category": emoji_cat,
                "emoji_art": emoji_art,
                "colors": list(colors),
                "ascii_art": ascii_art
            }

            f.write(json.dumps(training_example, ensure_ascii=False) + '\n')
            
            successful += 1
            print(f"✓ Processed: {unicode_code} - {emoji_name}")
            
        except Exception as e:
            failed += 1
            print(f"✗ Failed: {fname} - {str(e)}")

print(f"\nProcessing complete!")
print(f"Successful: {successful}")
print(f"Failed: {failed}")
print(f"Missing names: {missing_names}")
print(f"Training data saved to: {output_file}")