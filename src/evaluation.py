import argparse
from utils.prompts import TEXT_ONLY_PROMPT, IMAGE_ONLY_PROMPT
from utils.load_dataset import EmojiDataset
from torch.utils.data import DataLoader
from tqdm import tqdm
from utils.llm_helper import call_llm
from collections import defaultdict
from utils.post_processing import postprocess_answer
import json

def main(args):
    test_data = EmojiDataset(data_path=args.test_file_path)

    # Handle slicing for partial runs
    start = args.start_idx
    end = args.end_idx if args.end_idx is not None else len(test_data)

    # Guard against invalid ranges
    if start < 0 or start >= len(test_data):
        raise ValueError(f"Invalid start_idx {start}")
    if end > len(test_data):
        raise ValueError(f"Invalid end_idx {end}")

    # Slice the dataset
    test_data = test_data[start:end]

    test_dataloader = DataLoader(test_data, shuffle=False, batch_size=1)
    
    # Track overall statistics
    total_correct = 0
    total_questions = 0
    
    # Track per-category statistics
    category_correct = defaultdict(int)
    category_total = defaultdict(int)
    
    # Store results for output file
    results = []
    
    for data in tqdm(test_dataloader):
        emoji_art = data["emoji_art"][0]
        choices = data["choices"][0]
        category = data["category"][0]
        target_label = data["labels"][0]
        
        # Prepare prompt based on mode
        if args.mode == "text":
            prompt = TEXT_ONLY_PROMPT.format(emoji_art=emoji_art, choices=choices)
            image_path = None
        elif args.mode == "image":
            prompt = IMAGE_ONLY_PROMPT.format(choices=choices)
            image_path = f"emojis/{data['unicode'][0]}.png"
        else:
            raise ValueError(f"Invalid mode: {args.mode}")
        
        try:
            response, _ = call_llm(args.model_name, args.api_key, prompt, image_path)
            # Check if answer is correct
            is_correct = postprocess_answer(
                response, 
                target_label, 
                data["ori_choices"][0]
            )

            print(response)

            # Update counts
            total_questions += 1
            category_total[category] += 1
            
            if is_correct:
                total_correct += 1
                category_correct[category] += 1
            
            # Store result
            results.append({
                "unicode": data["unicode"][0],
                "name": data.get("name", [""])[0],
                "category": category,
                "response": response,
                "correct": bool(is_correct),
                "target": target_label
            })
            
        except Exception as e:
            print(f"Error processing {data.get('unicode', ['unknown'])[0]}: {e}")
            total_questions += 1
            category_total[category] += 1
            results.append({
                "unicode": data["unicode"][0],
                "name": data.get("name", [""])[0],
                "category": category,
                "error": str(e),
                "correct": False
            })
    
    # Calculate overall accuracy
    overall_accuracy = total_correct / total_questions if total_questions > 0 else 0
    
    # Calculate per-category accuracy
    category_accuracy = {}
    for category in category_total:
        category_accuracy[category] = (
            category_correct[category] / category_total[category] 
            if category_total[category] > 0 else 0
        )
    
    # Macro accuracy
    if len(category_accuracy) > 0:
        macro_acc = sum(category_accuracy.values()) / len(category_accuracy)
    else:
        macro_acc = 0

    # Print results
    print("\n" + "="*60)
    print("OVERALL RESULTS")
    print("="*60)
    print(f"Total Questions: {total_questions}")
    print(f"Correct: {total_correct}")
    print(f"Overall Micro Accuracy: {overall_accuracy:.2%}")
    print(f"Overall Macro Accuracy: {macro_acc:.2%}")
    
    print("\n" + "="*60)
    print("PER-CATEGORY RESULTS")
    print("="*60)
    for category in sorted(category_accuracy.keys()):
        correct = category_correct[category]
        total = category_total[category]
        accuracy = category_accuracy[category]
        print(f"{category:30s}: {correct:3d}/{total:3d} = {accuracy:.2%}")
    
    # Save detailed results to file
    if args.output_file_path:
        output_data = {
            "model": args.model_name,
            "mode": args.mode,
            "overall": {
                "total": total_questions,
                "correct": total_correct,
                "accuracy": overall_accuracy
            },
            "per_category": {
                category: {
                    "total": category_total[category],
                    "correct": category_correct[category],
                    "accuracy": category_accuracy[category]
                }
                for category in category_accuracy
            },
            "detailed_results": results
        }
        
        with open(args.output_file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nDetailed results saved to: {args.output_file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emoji Art MCQ Evaluation")
    parser.add_argument("--model_name", type=str, required=True, help="Model name")
    parser.add_argument("--api_key", type=str, default="", help="API_KEY")
    parser.add_argument("--test_file_path", type=str, default="./data/test.jsonl")
    parser.add_argument("--output_file_path", type=str, help="Path to save results JSON")
    parser.add_argument("--category", type=str, help="Filter to specific category (optional)")
    parser.add_argument("--mode", type=str, default="text", choices=["text", "image"], 
                        help="Evaluation mode: text or image")
    parser.add_argument("--start_idx", type=int, default=0, help="Start index (inclusive)")
    parser.add_argument("--end_idx", type=int, default=None, help="End index (exclusive)")
    
    args = parser.parse_args()
    main(args)