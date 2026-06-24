import os
import re
import json
import git  # Make sure to import git here now!
import diff_analyzer

def extract_search_terms(impacted_items):
    """
    Strips full function signatures down to just their base names, 
    and also grabs the base filename as a fallback search term.
    """
    search_terms = set()
    
    for item in impacted_items:
        file_path = item.get("file", "")
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        if base_name:
            search_terms.add(base_name)
            
        funcs = item.get("impacted_functions", [])
        for sig in funcs:
            if sig == "global_scope_or_unknown":
                continue
                
            match = re.search(r'([a-zA-Z0-9_]+)\s*\(', sig)
            if match:
                search_terms.add(match.group(1))

    return search_terms

def get_tests_to_run(diff_json_data, repo_path, target_commit, tests_dir_prefix="tests"):
    """
    Scans the Git tree of a specific commit for .py tests and returns 
    a list of files that reference any of the changed functions.
    """
    impacted_items = diff_json_data.get("added_or_modified", [])
    if not impacted_items:
        return []

    search_terms = extract_search_terms(impacted_items)
    print(f"🔍 Searching tests in commit '{target_commit}' for keywords: {', '.join(search_terms)}\n")
    
    tests_to_run = set()
    
    try:
        repo = git.Repo(repo_path)
        commit = repo.commit(target_commit)
    except Exception as e:
        print(f"❌ Error accessing Git repo: {e}")
        return []

    # Traverse the Git tree for this EXACT commit
    for item in commit.tree.traverse():
        
        # We only care about Python files inside the designated tests folder
        if item.type == 'blob' and item.path.startswith(tests_dir_prefix) and item.path.endswith('.py'):
            try:
                # Read the file directly from Git memory (errors='ignore' handles weird encodings)
                content = item.data_stream.read().decode('utf-8', errors='ignore')
                
                # Check if any of our search terms exist in this test file
                for term in search_terms:
                    # \b ensures whole words only. This perfectly catches words inside comments too!
                    pattern = r'\b' + re.escape(term) + r'\b'
                    
                    if re.search(pattern, content):
                        print(f"✅ Selected: {item.path} (Matched keyword: '{term}')")
                        tests_to_run.add(item.path)
                        break # Found a match, move to the next file
            
            except Exception as e:
                print(f"⚠️ Could not read {item.path} from Git: {e}")

    return list(tests_to_run)


# --- Local Testing Block ---
if __name__ == "__main__":
    DUMMY_REPO_PATH = "../dummy-codebase-techathon" 
    
    BASE = "18550d2583e0cfc5dd2f3ae17ede5322c43feaf3" 
    TARGET = "9997e84e61f5f59b2b84948d4bfccb5289c3dacd" 
    
    # Path relative to the Git root
    TESTS_DIR_PREFIX = "tests" 
    
    print("--- Phase 1: Analyzing Git Diff ---\n")
    live_json_output = diff_analyzer.get_impacted_files(
        repo_path=DUMMY_REPO_PATH,
        base_commit=BASE,
        target_commit=TARGET,
        target_dir="src/"
    )
    
    for item in live_json_output.get("added_or_modified", []):
        filename = item["file"]
        
        clean_funcs = set()
        for sig in item.get("impacted_functions", []):
            if sig == "global_scope_or_unknown":
                continue
            match = re.search(r'([a-zA-Z0-9_]+)\s*\(', sig)
            if match:
                clean_funcs.add(match.group(1))
                
        formatted_funcs = str(clean_funcs) if clean_funcs else "{No functions detected}"
        change_tag = "[ADDED]" if item["change_type"] == 'A' else "[MODIFIED]"
        print(f"{filename} {change_tag}: {formatted_funcs}")
    
    
    print("\n--- Phase 2: Mapping Impacted Tests ---")
    
    # Notice we now pass repo_path and target_commit directly
    final_test_list = get_tests_to_run(live_json_output, DUMMY_REPO_PATH, TARGET, TESTS_DIR_PREFIX)
    
    print("\n--- Final Execution Payload ---")
    print(json.dumps(final_test_list, indent=4))