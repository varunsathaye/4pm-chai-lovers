import git
import os
import re
from typing import List, Dict, Any

# 1. Global ignore list (solves scope issues and cleans up noise)
IGNORE_KEYWORDS = {
    'if', 'for', 'while', 'switch', 'catch', 'else', 'return',
    'public:', 'private:', 'protected:', 'class', 'struct', 'namespace',
    'ESP_LOG', 'Serial', 'printf', 'cout', 'cin', 'print'
}

def get_enclosing_function(file_lines: List[str], changed_line_index: int) -> str:
    """
    Scans upwards from the EXACT changed line to find the nearest C++ function signature.
    """
    # Ensure we don't scan out of bounds
    start_idx = min(changed_line_index, len(file_lines) - 1)

    for i in range(start_idx, -1, -1):
        line = file_lines[i].strip()

        # Skip empty lines, comments, and preprocessor directives
        if not line or line.startswith('//') or line.startswith('#'):
            continue

        # Skip standard statements (they end in semicolons)
        if line.endswith(';'):
            continue

        # Grab the very first word of the line to check against our ignore list
        # e.g., "if (x > 5)" -> grabs "if"
        first_word_match = re.match(r'^([a-zA-Z_]\w*)', line)
        if first_word_match:
            first_word = first_word_match.group(1)
            if first_word in IGNORE_KEYWORDS:
                continue

        # Regex: Looks for [Word] + [Spaces] + [(] + [Anything] + [)] + [Optional Space/{]
        match = re.search(r'\b([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{?$', line)
        if match:
            # Final safety check: ensure the matched word isn't a blocked keyword
            func_name = match.group(1)
            if func_name not in IGNORE_KEYWORDS:
                return line

    return "global_scope_or_unknown"


def get_impacted_files(repo_path: str, base_commit: str, target_commit: str = 'HEAD', target_dir: str = '') -> Dict[str, Any]:
    try:
        repo = git.Repo(repo_path)
        commit_a = repo.commit(base_commit)
        commit_b = repo.commit(target_commit)
    except Exception as e:
        print(f"Error accessing repo or commits: {e}")
        return {}

    diff_index = commit_a.diff(commit_b, create_patch=True)
    impacted_files = {"added_or_modified": [], "deleted": [], "renamed": []}

    for diff_item in diff_index:
        a_path = diff_item.a_path if diff_item.a_path else ""
        b_path = diff_item.b_path if diff_item.b_path else ""

        change_type = diff_item.change_type
        if change_type is None:
            if diff_item.new_file: change_type = 'A'
            elif diff_item.deleted_file: change_type = 'D'
            elif diff_item.renamed_file: change_type = 'R'
            else: change_type = 'M'

        if target_dir in ['.', './', ''] or a_path.startswith(target_dir) or b_path.startswith(target_dir):
            
            if change_type in ['A', 'M']:
                raw_diff = diff_item.diff.decode('utf-8', errors='ignore') if diff_item.diff else ""
                
                try:
                    file_blob = commit_b.tree[b_path]
                    file_lines = file_blob.data_stream.read().decode('utf-8', errors='ignore').split('\n')
                except KeyError:
                    file_lines = []

                impacted_functions = set()
                
                if change_type == 'A':
                    # For entirely new files, scan every line for functions
                    for line in file_lines:
                        clean_line = line.strip()
                        if not clean_line or clean_line.endswith(';'):
                            continue
                            
                        first_word_match = re.match(r'^([a-zA-Z_]\w*)', clean_line)
                        if first_word_match and first_word_match.group(1) in IGNORE_KEYWORDS:
                            continue
                            
                        if re.search(r'\b([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{?$', clean_line):
                            impacted_functions.add(clean_line)
                else:
                    # For modified files, track the EXACT line number of the change
                    current_line_num = -1
                    hunk_fallback_func = "global_scope_or_unknown"
                    
                    for line in raw_diff.split('\n'):
                        if line.startswith('@@'):
                            # Parse the hunk header to get the starting line number
                            match = re.search(r'\+(\d+)', line)
                            if match:
                                # Subtract 1 to convert to Python's 0-based array index
                                current_line_num = int(match.group(1)) - 1
                                
                            # Grab Git's built-in fallback guess
                            parts = line.split('@@', 2)
                            if len(parts) >= 3 and parts[2].strip():
                                hunk_fallback_func = parts[2].strip()
                                
                        # Trigger the scanner ONLY when we hit the specifically modified line
                        elif line.startswith('+') and not line.startswith('+++'):
                            if current_line_num != -1 and file_lines:
                                # Scan upwards from the specific changed line
                                current_function = get_enclosing_function(file_lines, current_line_num)
                                
                                # Use Git's fallback if Python fails
                                if current_function == "global_scope_or_unknown":
                                    current_function = hunk_fallback_func
                                    
                                impacted_functions.add(current_function)
                                
                            current_line_num += 1 # Advance pointer
                            
                        # Handle deleted lines (scan from the line right above the deletion)
                        elif line.startswith('-') and not line.startswith('---'):
                            if current_line_num != -1 and file_lines:
                                current_function = get_enclosing_function(file_lines, max(0, current_line_num - 1))
                                if current_function == "global_scope_or_unknown":
                                    current_function = hunk_fallback_func
                                impacted_functions.add(current_function)
                                
                        # Advance pointer for unmodified context lines
                        elif not line.startswith('\\'): 
                            if current_line_num != -1:
                                current_line_num += 1
                
                impacted_files["added_or_modified"].append({
                    "file": b_path,
                    "change_type": change_type,
                    "impacted_functions": list(impacted_functions) 
                })
            
            elif change_type == 'D':
                impacted_files["deleted"].append(a_path)
            
            elif change_type == 'R':
                impacted_files["renamed"].append({"old_path": a_path, "new_path": b_path})

    return impacted_files