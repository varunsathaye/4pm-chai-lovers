import os
import re
import json
import git  
import diff_analyzer

def extract_search_terms(impacted_items):
    """
    Strips full function signatures down to just their base names.
    (Removed the fallback base filename logic as requested).
    """
    search_terms = set()
    
    for item in impacted_items:
        funcs = item.get("impacted_functions", [])
        for sig in funcs:
            if sig == "global_scope_or_unknown":
                continue
                
            # Extracts the pure function name
            match = re.search(r'([a-zA-Z0-9_]+)\s*\(', sig)
            if match:
                search_terms.add(match.group(1))

    return search_terms

def get_recursive_dependencies(initial_terms, repo_path, target_commit, src_dir_prefix="src"):
    """
    Iteratively scans the source code to find parent functions that call 
    our impacted functions, expanding the blast radius until no new dependencies are found.
    """
    if not initial_terms:
        return set()

    try:
        repo = git.Repo(repo_path)
        commit = repo.commit(target_commit)
    except Exception as e:
        print(f"❌ Error accessing Git repo during recursive scan: {e}")
        return initial_terms

    try:
        # 1. Pre-load all C++ source files into memory to make the looping extremely fast
        src_files = {}
        for item in commit.tree.traverse():
            if item.type == 'blob' and item.path.startswith(src_dir_prefix) and item.path.endswith(('.cpp', '.c', '.h', '.hpp')):
                try:
                    content = item.data_stream.read().decode('utf-8', errors='ignore')
                    src_files[item.path] = content.split('\n')
                except:
                    pass

        current_keywords = set(initial_terms)
        
        # 2. Loop continuously until the size of our keyword set stops growing
        while True:
            new_additions = set()
            
            escaped_terms = [re.escape(term) for term in current_keywords]
            pattern = r'\b(' + '|'.join(escaped_terms) + r')\b'
            regex = re.compile(pattern)

            for path, lines in src_files.items():
                for idx, line in enumerate(lines):
                    if regex.search(line):
                        enclosing_sig = diff_analyzer.get_enclosing_function(lines, idx + 1)
                        if enclosing_sig != "global_scope_or_unknown":
                            match = re.search(r'([a-zA-Z0-9_]+)\s*\(', enclosing_sig)
                            if match:
                                parent_func = match.group(1)
                                if parent_func not in current_keywords:
                                    new_additions.add(parent_func)

            if not new_additions:
                break
                
            print(f"🔄 Blast Radius Expanded! Found parent dependencies: {', '.join(new_additions)}")
            current_keywords.update(new_additions)
            
    finally:
        # CRITICAL FIX: Guarantee the file locks are released
        repo.close()

    return current_keywords


def get_tests_to_run(search_terms, repo_path, target_commit, tests_dir_prefix="tests"):
    """
    Scans the Git tree of a specific commit for .py tests and returns 
    a list of files that reference any of the final keyword functions.
    """
    if not search_terms:
        return []

    print(f"\n🔍 Searching tests in commit '{target_commit}' for keywords:\n   {', '.join(search_terms)}\n")
    
    tests_to_run = set()
    
    try:
        repo = git.Repo(repo_path)
        commit = repo.commit(target_commit)
    except Exception as e:
        print(f"❌ Error accessing Git repo: {e}")
        return []

    try:
        # Traverse the Git tree for this EXACT commit
        for item in commit.tree.traverse():
            # Flexible path check (case-insensitive) to ensure we don't miss the folder
            if item.type == 'blob' and tests_dir_prefix.lower() in item.path.lower():
                try:
                    # Read the file directly from Git memory
                    content = item.data_stream.read().decode('utf-8', errors='ignore')
                    
                    # Check if any of our search terms exist in this test file
                    for term in search_terms:
                        # \b ensures whole words only. Catches words inside comments too!
                        pattern = r'\b' + re.escape(term) + r'\b'
                        
                        if re.search(pattern, content):
                            print(f"✅ Selected: {item.path} (Matched keyword: '{term}')")
                            tests_to_run.add(item.path)
                            break # Found a match, move to the next file
                
                except Exception as e:
                    print(f"⚠️ Could not read {item.path} from Git: {e}")
                    
    finally:
        # CRITICAL FIX: Guarantee the file locks are released for Windows
        repo.close()

    return list(tests_to_run)


# --- Local Testing Block ---
if __name__ == "__main__":
    import tempfile 
    REMOTE_URL = "https://github.com/varunsathaye/dummy-codebase-techathon.git"    
    BASE = "ab07b1d875126ba62532f244d9391effc13a461b" 
    TARGET = "5d02dd2e11648327179377f424879feee418814e" 
    TESTS_DIR_PREFIX = "tests" 
    SRC_DIR_PREFIX = "src"
    print(f"Cloning {REMOTE_URL} to a temporary directory...")
    # FIX 1: Tell Windows to ignore non-critical cleanup lock errors
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        try:
            # FIX 2: Assign the clone to a variable so we can close it later
            cloned_repo = git.Repo.clone_from(REMOTE_URL, temp_dir)
            print("Clone successful.\n")
        except git.exc.GitCommandError as e:
            print(f"❌ Error cloning repository: {e}")
            exit(1)
        print("--- Phase 1: Analyzing Git Diff ---\n")    
        live_json_output = diff_analyzer.get_impacted_files(
            repo_path=temp_dir,
            base_commit=BASE,
            target_commit=TARGET,
            target_dir="src/"
        )
        for item in live_json_output.get("added_or_modified", []):
            filename = item["file"]
            clean_funcs = set()
            for sig in item.get("impacted_functions", []):
                if sig == "global_scope_or_unknown": continue
                match = re.search(r'([a-zA-Z0-9_]+)\s*\(', sig)
                if match: clean_funcs.add(match.group(1))
                    
            formatted_funcs = str(clean_funcs) if clean_funcs else "{No functions detected}"
            change_tag = "[ADDED]" if item["change_type"] == 'A' else "[MODIFIED]"
            print(f"{filename} {change_tag}: {formatted_funcs}")
        print("\n--- Phase 2: Expanding Blast Radius (Call Graph) ---")
        impacted_items = live_json_output.get("added_or_modified", [])
        initial_keywords = extract_search_terms(impacted_items)
        final_keywords = get_recursive_dependencies(initial_keywords, temp_dir, TARGET, SRC_DIR_PREFIX)
        print("\n--- Phase 3: Mapping Impacted Tests ---")
        final_test_list = get_tests_to_run(final_keywords, temp_dir, TARGET, TESTS_DIR_PREFIX)
        print("\n--- Final Execution Payload ---")
        print(json.dumps(final_test_list, indent=4))
        # FIX 3: Explicitly force Git to release the file locks before the block ends
        cloned_repo.close()
    print("\n🧹 Temporary directory cleaned up.")