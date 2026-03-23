"""
Instagram Following List Comparator
====================================
Compares two extracted following lists and finds overlapping users.

DESIGN DECISIONS:
- Uses set operations for O(n) comparison efficiency
- Outputs multiple formats (console, JSON, CSV) for flexibility
- Shows statistics and generates detailed report
- Handles edge cases: missing files, malformed JSON, empty lists

USAGE:
    python compare_lists.py account1_following.json account2_following.json

OUTPUT:
    - Console summary with statistics
    - mutual_follows.json with full results
    - mutual_follows.csv for spreadsheet import (optional)
"""

import json
import csv
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, Any


def load_following_list(filepath: str) -> Set[str]:
    """
    Load usernames from a JSON file created by the scraper.

    REASONING: We normalize to lowercase for case-insensitive comparison.
    Instagram usernames are case-insensitive.

    Args:
        filepath: Path to the JSON file

    Returns:
        Set of lowercase usernames

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both formats: list of strings or dict with "usernames" key
    if isinstance(data, list):
        usernames = data
    elif isinstance(data, dict) and "usernames" in data:
        usernames = data["usernames"]
    else:
        raise ValueError(f"Unexpected JSON format in {filepath}. Expected list or dict with 'usernames' key.")

    # Normalize to lowercase set
    return {username.lower().strip() for username in usernames if username}


def compare_lists(list1: Set[str], list2: Set[str]) -> Dict[str, Any]:
    """
    Compare two sets of usernames and compute statistics.

    REASONING: Set operations are O(n) and perfect for this use case.
    We compute multiple set operations to give a complete picture.

    Args:
        list1: First set of usernames
        list2: Second set of usernames

    Returns:
        Dictionary containing:
        - mutual: Users in both lists
        - only_in_first: Users only in first list
        - only_in_second: Users only in second list
        - statistics: Count and percentage info
    """
    mutual = list1 & list2  # Intersection
    only_first = list1 - list2  # Difference
    only_second = list2 - list1  # Difference

    # Calculate percentages
    pct_of_first = (len(mutual) / len(list1) * 100) if list1 else 0
    pct_of_second = (len(mutual) / len(list2) * 100) if list2 else 0
    jaccard = len(mutual) / len(list1 | list2) * 100 if (list1 | list2) else 0

    return {
        "mutual": sorted(mutual),
        "only_in_first": sorted(only_first),
        "only_in_second": sorted(only_second),
        "statistics": {
            "first_list_count": len(list1),
            "second_list_count": len(list2),
            "mutual_count": len(mutual),
            "only_in_first_count": len(only_first),
            "only_in_second_count": len(only_second),
            "mutual_pct_of_first": round(pct_of_first, 2),
            "mutual_pct_of_second": round(pct_of_second, 2),
            "jaccard_similarity": round(jaccard, 2)
        }
    }


def print_results(results: Dict[str, Any], file1: str, file2: str) -> None:
    """
    Print a formatted summary to the console.
    """
    stats = results["statistics"]

    print()
    print("=" * 60)
    print("COMPARISON RESULTS")
    print("=" * 60)
    print()
    print(f"List 1: {file1}")
    print(f"  Total users: {stats['first_list_count']:,}")
    print()
    print(f"List 2: {file2}")
    print(f"  Total users: {stats['second_list_count']:,}")
    print()
    print("-" * 60)
    print(f"MUTUAL FOLLOWS: {stats['mutual_count']:,}")
    print("-" * 60)
    print(f"  {stats['mutual_pct_of_first']}% of List 1 follows these accounts")
    print(f"  {stats['mutual_pct_of_second']}% of List 2 follows these accounts")
    print(f"  Jaccard Similarity: {stats['jaccard_similarity']}%")
    print()

    # Show sample of mutual follows
    mutual = results["mutual"]
    if mutual:
        print("Sample of mutual follows (first 20):")
        for i, username in enumerate(mutual[:20], 1):
            print(f"  {i:2}. @{username}")
        if len(mutual) > 20:
            print(f"  ... and {len(mutual) - 20} more")
    else:
        print("No mutual follows found.")

    print()
    print("-" * 60)
    print(f"Only in List 1: {stats['only_in_first_count']:,} users")
    print(f"Only in List 2: {stats['only_in_second_count']:,} users")
    print("-" * 60)


def save_json_results(results: Dict[str, Any], file1: str, file2: str, output_path: str) -> None:
    """
    Save full results to a JSON file.
    """
    output = {
        "metadata": {
            "compared_at": datetime.now().isoformat(),
            "source_files": {
                "list1": file1,
                "list2": file2
            }
        },
        "statistics": results["statistics"],
        "mutual_follows": results["mutual"],
        "only_in_first": results["only_in_first"],
        "only_in_second": results["only_in_second"]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[+] Full results saved to: {output_path}")


def save_csv_results(mutual: list, output_path: str) -> None:
    """
    Save mutual follows to a simple CSV file.
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["username", "profile_url"])
        for username in mutual:
            writer.writerow([username, f"https://instagram.com/{username}"])

    print(f"[+] CSV export saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Compare two Instagram following lists and find mutual follows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLE:
    python compare_lists.py account1_following.json account2_following.json

OUTPUT FILES:
    - mutual_follows.json: Full comparison results
    - mutual_follows.csv: Simple list for spreadsheet import (use --csv)
        """
    )

    parser.add_argument(
        "file1",
        help="First following list JSON file"
    )
    parser.add_argument(
        "file2",
        help="Second following list JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        default="mutual_follows.json",
        help="Output JSON filename (default: mutual_follows.json)"
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also generate CSV output"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Print all mutual follows (not just first 20)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Instagram Following List Comparator")
    print("=" * 60)

    # Load both lists
    try:
        print(f"\n[*] Loading {args.file1}...")
        list1 = load_following_list(args.file1)
        print(f"    Loaded {len(list1):,} usernames")

        print(f"[*] Loading {args.file2}...")
        list2 = load_following_list(args.file2)
        print(f"    Loaded {len(list2):,} usernames")

    except FileNotFoundError as e:
        print(f"\n[!] ERROR: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n[!] ERROR: Invalid JSON file: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n[!] ERROR: {e}")
        sys.exit(1)

    # Validate
    if not list1:
        print(f"\n[!] WARNING: {args.file1} is empty")
    if not list2:
        print(f"\n[!] WARNING: {args.file2} is empty")

    # Compare
    print("\n[*] Comparing lists...")
    results = compare_lists(list1, list2)

    # Print results
    print_results(results, args.file1, args.file2)

    # Show all if requested
    if args.show_all and len(results["mutual"]) > 20:
        print("\nFull list of mutual follows:")
        for i, username in enumerate(results["mutual"], 1):
            print(f"  {i:4}. @{username}")

    # Save results
    print()
    save_json_results(results, args.file1, args.file2, args.output)

    if args.csv:
        csv_path = args.output.replace('.json', '.csv')
        save_csv_results(results["mutual"], csv_path)

    print()
    print("[+] Done!")


if __name__ == "__main__":
    main()
