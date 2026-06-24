import git
import os
import re
from typing import List, Dict, Any

def get_enclosing_function(file_lines: List[str], line_num: int) -> str:
    """
    Scans upwards from a specific line number to find the nearest real function signature,
    ignoring access specifiers and control flow statements.
    """
    # Convert 1-based line number from Git to 0-based Python array index
    start_idx = min(line_num - 1, len(file_lines) - 1)
    
    # Keywords that Git might mistake for a function, but aren't
    ignore_keywords = ('if', 'for', 'while', 'switch', 'catch', 'public:', 'private:', 'protected:', 'class')

    for i in range(start_idx, -1, -1):
        line = file_lines[i].strip()
        
        # Skip empty lines or ignored keywords
        if not line or any(line.startswith(kw) for kw in ignore_keywords):
            continue
            
        # Regex to catch C++ and JS function signatures (looks for word + parenthesis)
        if re.search(r'\w+\s*\([^)]*\)', line):
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
    
    ignore_keywords = ('if', 'for', 'while', 'switch', 'catch', 'public:', 'private:', 'protected:', 'class')

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
                raw_diff = diff_item.diff.decode('utf-8') if diff_item.diff else ""
                
                try:
                    file_blob = commit_b.tree[b_path]
                    file_lines = file_blob.data_stream.read().decode('utf-8').split('\n')
                except KeyError:
                    file_lines = []

                impacted_functions = set()
                
                # --- NEW LOGIC FOR ADDED FILES ---
                if change_type == 'A':
                    # Grab every function in the newly added file
                    for line in file_lines:
                        clean_line = line.strip()
                        if not clean_line or any(clean_line.startswith(kw) for kw in ignore_keywords):
                            continue
                        if re.search(r'\w+\s*\([^)]*\)', clean_line):
                            impacted_functions.add(clean_line)
                else:
                    # Original logic for modified files (using Git hunks)
                    for line in raw_diff.split('\n'):
                        if line.startswith('@@'):
                            match = re.search(r'\+(\d+)', line)
                            
                            if match and file_lines:
                                line_num = int(match.group(1))
                                current_function = get_enclosing_function(file_lines, line_num)
                                impacted_functions.add(current_function)
                            else:
                                parts = line.split('@@', 2)
                                if len(parts) >= 3 and parts[2].strip():
                                    impacted_functions.add(parts[2].strip())
                                else:
                                    impacted_functions.add("global_scope_or_unknown")
                
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

# --- Local Testing Block ---
if __name__ == "__main__":
    DUMMY_REPO_PATH = "../dummy-codebase-techathon" 
    BASE = "18550d2583e0cfc5dd2f3ae17ede5322c43feaf3" 
    TARGET = "63e16005c3119f79590cfff6f251040f37753841" 
    
    print(f"Analyzing changes in {DUMMY_REPO_PATH} from {BASE} to {TARGET}...\n")
    
    results = get_impacted_files(
        repo_path=DUMMY_REPO_PATH,
        base_commit=BASE,
        target_commit=TARGET,
        target_dir="src/"
    )
    
    import json
    print(json.dumps(results, indent=4))