from collections import defaultdict
import random
import json
from pathlib import Path

INPUT_PATH = Path("emoji_data.jsonl")
OUTPUT_PATH = Path("data/test.jsonl")

def load_raw(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]
    
def save_data(data, path):
    with path.open("w", encoding="utf-8") as f:
        for x in data:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")

def category_to_names_dict(path):
    data = load_raw(path)

    dict = defaultdict(list)
    for row in data:
        dict[row['category']].append(row['name'])

    return dict

def color_to_names_dict(path):
    data = load_raw(path)

    dict = defaultdict(list)

    for row in data:
        dict[tuple(row['colors'])].append(row['name'])

    return dict

def get_choices(emoji_name, category):

    choices = category_dict[category].copy()
    choices.remove(emoji_name)
    # Pick three random incorrect choices
    return random.sample(choices, 3)

if __name__=="__main__":

    category_dict = category_to_names_dict(INPUT_PATH)
    data = load_raw(INPUT_PATH)

    for row in data:

        name, cat = row['name'], row['category']
        choices = [name] + get_choices(name, cat)
        choices_and_labels = list(zip(choices, [1, 0, 0, 0]))
        random.shuffle(choices_and_labels)
        choices, labels = zip(*choices_and_labels)
        row['choices'] = choices
        row['labels'] = labels

    save_data(data, OUTPUT_PATH)