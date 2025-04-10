#!/usr/bin/env python3
"""
BibTeX File Merger

This script processes multiple BibTeX files, checking for inconsistencies and merging them:
1. Articles with the same title should have the same key (warns if not)
2. Articles with the same key should have the same title (warns if not)
3. Merges the unique entries from all files into a new BibTeX file (ask user to choose which to keep interactively)

Usage: python bib_merger.py [--no-interactive] input1.bib input2.bib [input3.bib ...] output.bib
"""

import sys
import re
import os
import argparse
from collections import defaultdict

# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Valid BibTeX entry types
VALID_ENTRY_TYPES = [
    'article', 'book', 'booklet', 'conference', 'inbook', 'incollection',
    'inproceedings', 'manual', 'mastersthesis', 'misc', 'phdthesis',
    'proceedings', 'techreport', 'unpublished'
]

def parse_bib_file(filename):
    """Parse a BibTeX file and return a dictionary of entries."""
    if not os.path.exists(filename):
        print(f"Error: File {filename} does not exist.")
        sys.exit(1)
        
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extract individual entries
    entries = {}
    # Updated pattern to only match valid entry types
    entry_pattern = r'@(' + '|'.join(VALID_ENTRY_TYPES) + r')\{([^,]+),([\s\S]*?)\n\}'
    for match in re.finditer(entry_pattern, content, re.IGNORECASE):
        entry_type = match.group(1).lower()
        entry_key = match.group(2).strip()
        entry_content = match.group(3).strip()
        
        # Normalize indentation in entry_content
        lines = entry_content.split('\n')
        normalized_lines = []
        for line in lines:
            line = line.strip()
            if line:  # Only add non-empty lines
                normalized_lines.append('    ' + line)  # Add 4 spaces indentation
        entry_content = '\n'.join(normalized_lines)
        
        # Extract title
        title = extract_title(entry_content)

        # Reconstruct the raw entry with proper indentation
        raw_entry = f"@{entry_type}{{{entry_key},\n{entry_content}\n}}"
        
        entries[entry_key] = {
            'type': entry_type,
            'key': entry_key,
            'title': title,
            'content': entry_content,
            'raw': raw_entry,
            'source': filename  # Track which file this entry came from
        }
    
    return entries    

def extract_title(entry_content):
    # look for { } and ends with ','
    title_match = re.search(r'title\s*=\s*["{]?(.*?)["}]?(?:,|\s*$)', entry_content)
    if title_match:
        title = title_match.group(1).strip().strip(',')
        return title
    return None

def check_same_title_different_keys(all_entries, titles_to_keys_by_file):
    has_issues = False
    print("\nChecking for entries with the same title but different keys:")
    
    # Check within each file
    for file_idx, titles_to_keys in titles_to_keys_by_file.items():
        # Group by type first
        titles_to_keys_by_type = defaultdict(lambda: defaultdict(list))
        for title, keys in titles_to_keys.items():
            for key in keys:
                entry = next(e for e in all_entries.values() if e['key'] == key and e['source'].endswith('.bib'))
                titles_to_keys_by_type[entry['type']][title].append(key)
        
        # Check each type group separately
        for entry_type, type_titles_to_keys in titles_to_keys_by_type.items():
            for title, keys in type_titles_to_keys.items():
                if len(keys) > 1:
                    has_issues = True
                    file_name = next(entry['source'] for entry in all_entries.values() 
                                   if entry['source'].endswith('.bib') and entry['key'] in keys)
                    print(f"{YELLOW}WARNING{RESET}: Same title and type ({entry_type}) has multiple keys in file {YELLOW}{file_name}{RESET}:")
                    print(f"  Title: {RED}{title}{RESET}")
                    print(f"  Keys: {RED}{', '.join(keys)}{RESET}")
                    for key in keys:
                        matching_entries = [e for e in all_entries.values() 
                                         if e['key'] == key and e['source'] == file_name]
                        if matching_entries:
                            print(f"  Entry: {matching_entries[0]['raw'][:100]}...")
    
    # Check across files - collect all keys for each title and type
    all_titles_to_keys = defaultdict(lambda: defaultdict(list))
    for file_idx, titles_to_keys in titles_to_keys_by_file.items():
        for title, keys in titles_to_keys.items():
            for key in keys:
                entry = next(e for e in all_entries.values() if e['key'] == key and e['source'].endswith('.bib'))
                if key not in all_titles_to_keys[entry['type']][title]:
                    all_titles_to_keys[entry['type']][title].append((key, file_idx))
    
    # Find titles with multiple different keys for each type
    for entry_type, type_titles_to_keys in all_titles_to_keys.items():
        for title, key_file_pairs in type_titles_to_keys.items():
            if len(set(key for key, _ in key_file_pairs)) > 1:
                has_issues = True
                print(f"{YELLOW}WARNING{RESET}: Same title and type ({entry_type}) has different keys across files:")
                print(f"  Title: {RED}{title}{RESET}")
                for key, file_idx in key_file_pairs:
                    file_name = next(entry['source'] for entry in all_entries.values() 
                                   if entry['source'].endswith('.bib') and entry['key'] == key)
                    print(f"  Key in {YELLOW}{file_name}{RESET}: {RED}{key}{RESET}")
                    matching_entries = [e for e in all_entries.values() 
                                     if e['key'] == key and e['source'] == file_name]
                    if matching_entries:
                        print(f"  Entry: {matching_entries[0]['raw'][:100]}...")
    
    return has_issues

def get_user_choice(title, keys, entries):
    """Get user's choice for which key to use when there are multiple keys for the same title."""
    print(f"\n{YELLOW}Multiple keys found for title:{RESET} {RED}{title}{RESET}")
    print("Available keys:")
    for i, key in enumerate(keys, 1):
        entry = next(e for e in entries.values() if e['key'] == key)
        print(f"{i}. {RED}{key}{RESET} (from {YELLOW}{entry['source']}{RESET})")
        print(f"   Entry: {entry['raw'][:300]}...")
    
    while True:
        choice = input("\nEnter the number of the key to use (or 'q' to quit): ")
        if choice.lower() == 'q':
            sys.exit(1)
        try:
            choice = int(choice)
            if 1 <= choice <= len(keys):
                return keys[choice - 1]
            print(f"Please enter a number between 1 and {len(keys)}")
        except ValueError:
            print("Please enter a valid number or 'q' to quit")

def get_user_choice_for_same_key(key, entries):
    """Get user's choice for which entry to keep when there are multiple entries with the same key."""
    print(f"\n{YELLOW}Multiple entries found for key:{RESET} {RED}{key}{RESET}")
    print("Available entries:")
    for i, entry in enumerate(entries, 1):
        print(f"{i}. From {YELLOW}{entry['source']}{RESET}:")
        print(f"   Type: {entry['type']}")
        print(f"   Title: {RED}{entry['title']}{RESET}")
        print(f"   Entry: {entry['raw'][:300]}...")
    
    while True:
        choice = input("\nEnter the number of the entry to keep (or press Enter to keep all): ")
        if choice.strip() == "":
            return None  # Keep all entries
        try:
            choice = int(choice)
            if 1 <= choice <= len(entries):
                return entries[choice - 1]
            print(f"Please enter a number between 1 and {len(entries)}")
        except ValueError:
            print("Please enter a valid number or press Enter to keep all")

def choose_entry_from_smallest_index(entries):
    """Choose the entry from the file with the smallest index."""
    # Extract file index from the source path
    def get_file_index(entry):
        # The source path format is "key_filecount_filepath"
        # We need to extract filecount from the entry's key
        key_parts = entry['key'].split('_')
        if len(key_parts) >= 2:
            return int(key_parts[-2])  # filecount is the second-to-last part
        return float('inf')  # Return infinity if we can't parse the index
    
    # Sort entries by file index and return the first one
    return min(entries, key=get_file_index)

def check_same_key_different_titles(all_entries, interactive=True):
    """Check if articles with the same key have different titles."""
    has_issues = False
    print("\nChecking for entries with the same key but different titles:")
    
    # Group entries by key
    entries_by_key = defaultdict(list)
    for entry in all_entries.values():
        entries_by_key[entry['key']].append(entry)
    
    # Check for keys with different titles
    key_to_chosen_entry = {}  # Store user's choices for keys with multiple entries
    for key, entries in entries_by_key.items():
        # Group entries by type
        entries_by_type = defaultdict(list)
        for entry in entries:
            entries_by_type[entry['type']].append(entry)
        
        # Check each type group separately
        for entry_type, type_entries in entries_by_type.items():
            titles = {entry['title'].lower() if entry['title'] else None for entry in type_entries}
            if len(titles) > 1:
                has_issues = True
                print(f"{YELLOW}WARNING{RESET}: Same key and type ({entry_type}) has different titles:")
                print(f"  Key: {RED}{key}{RESET}")
                
                if interactive:
                    if key not in key_to_chosen_entry:
                        chosen_entry = get_user_choice_for_same_key(key, type_entries)
                        if chosen_entry:
                            key_to_chosen_entry[key] = chosen_entry
                            # Remove other entries with this key
                            for entry in type_entries:
                                if entry != chosen_entry:
                                    entry['skip'] = True
                else:
                    # In non-interactive mode, choose entry from file with smallest index
                    chosen_entry = choose_entry_from_smallest_index(type_entries)
                    key_to_chosen_entry[key] = chosen_entry
                    # Remove other entries with this key
                    for entry in type_entries:
                        if entry != chosen_entry:
                            entry['skip'] = True
                
                for entry in type_entries:
                    if not entry.get('skip', False):
                        title_display = entry['title'] if entry['title'] else "None"
                        print(f"  Title in {YELLOW}{entry['source']}{RESET}: {RED}{title_display}{RESET}")
                        print(f"  Entry: {entry['raw'][:100]}...")
    
    return has_issues, key_to_chosen_entry

def check_output_file(output_file, interactive=True, overwrite=False):
    """Check if the output file exists and handle it based on interactive mode."""
    if os.path.exists(output_file):
        if overwrite:
            return True
        if interactive:
            while True:
                choice = input(f"\n{YELLOW}Warning:{RESET} Output file {RED}{output_file}{RESET} already exists. Overwrite? (y/n): ")
                if choice.lower() == 'y':
                    return True
                elif choice.lower() == 'n':
                    print("Operation cancelled.")
                    sys.exit(0)
                else:
                    print("Please enter 'y' or 'n'")
        else:
            print(f"\n{RED}Error:{RESET} Output file {output_file} already exists. Use interactive mode to overwrite.")
            sys.exit(1)
    return True

def merge_bib_files(input_files, output_file, interactive=True, overwrite=False):
    """Merge multiple BibTeX files with consistency checks."""
    # Check if output file exists
    check_output_file(output_file, interactive, overwrite)
    
    all_entries = {}
    titles_to_keys_by_file = {}
    title_to_chosen_key = {}  # Store user's choices for titles with multiple keys
    
    # Parse all input files
    file_count = 0
    for input_file in input_files:
        entries = parse_bib_file(input_file)
        print(f"Found {len(entries)} entries in {input_file}")
        
        # Create mappings from title to keys for this file
        titles_to_keys = defaultdict(list)
        for key, entry in entries.items():
            if entry['title']:
                titles_to_keys[entry['title'].lower()].append(key)
            
            # Add unique identifier to avoid key collisions
            unique_key = f"{key}_{file_count}_{input_file}"
            all_entries[unique_key] = entry
            
        titles_to_keys_by_file[file_count] = titles_to_keys
        file_count += 1
    
    # Check for consistency issues
    has_issues = False
    
    # 1. Check if articles with the same title have different keys
    has_issues |= check_same_title_different_keys(all_entries, titles_to_keys_by_file)
    
    # 2. Check if articles with the same key have different titles
    has_issues, key_to_chosen_entry = check_same_key_different_titles(all_entries, interactive)
    
    # 3. Merge entries
    merged_entries = {}
    for entry in all_entries.values():
        key = entry['key']
        title = entry['title'].lower() if entry['title'] else None
        entry_type = entry['type']
        
        # Skip entries that were chosen to be removed in interactive mode
        if entry.get('skip', False):
            continue
        
        if title and (entry_type, title) in title_to_chosen_key:
            # Use the previously chosen key for this title and type
            key = title_to_chosen_key[(entry_type, title)]
        elif title:
            # Check if this title has multiple keys of the same type
            all_keys = set()
            for titles_to_keys in titles_to_keys_by_file.values():
                if title in titles_to_keys:
                    for k in titles_to_keys[title]:
                        entry = next(e for e in all_entries.values() if e['key'] == k)
                        if entry['type'] == entry_type:
                            all_keys.add(k)
            
            if len(all_keys) > 1:
                if interactive:
                    if (entry_type, title) not in title_to_chosen_key:
                        chosen_key = get_user_choice(entry['title'], list(all_keys), all_entries)
                        title_to_chosen_key[(entry_type, title)] = chosen_key
                    key = title_to_chosen_key[(entry_type, title)]
                else:
                    # In non-interactive mode, choose key from file with smallest index
                    entries_with_keys = [next(e for e in all_entries.values() if e['key'] == k) for k in all_keys]
                    chosen_entry = choose_entry_from_smallest_index(entries_with_keys)
                    key = chosen_entry['key']
        
        if key not in merged_entries:
            merged_entries[key] = entry
    
    # Sort entries by title
    sorted_entries = sorted(merged_entries.values(), 
                           key=lambda e: (e['title'].lower() if e['title'] else '', e['type'], e['key']))
    
    # Write merged file
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in sorted_entries:
            f.write(entry['raw'] + "\n\n")
    
    print(f"\nMerged {len(merged_entries)} unique entries into {output_file}")
    
    if has_issues:
        print(f"\n{YELLOW}{BOLD}Warning:{RESET} Inconsistencies were found. Please review the warnings above.")
    else:
        print(f"\n{GREEN}{BOLD}No inconsistencies found!{RESET}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Merge multiple BibTeX files with consistency checks.')
    parser.add_argument('--no-interactive', action='store_true', help='Disable interactive mode (defaults to interactive)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite output file without asking')
    parser.add_argument('files', nargs='+', help='Input BibTeX files followed by output file')
    
    args = parser.parse_args()
    
    if len(args.files) < 3:
        print("Error: At least two input BibTeX files and one output file are required.")
        sys.exit(1)
    
    output_file = args.files[-1]
    input_files = args.files[:-1]
    
    merge_bib_files(input_files, output_file, not args.no_interactive)
