import os
import json
import yaml
from datetime import datetime, timezone

def read_yaml(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def read_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_index():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    runtime_root = os.path.join(repo_root, '.run', 'maturity')
    ecosystem_path = os.path.join(repo_root, 'engineering', 'maturity', 'ecosystem.yaml')
    
    ecosystem = read_yaml(ecosystem_path) or {"components": []}
    
    aggregated = {
        "schema": "sister.maturity-components/1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec='seconds'),
        "components": []
    }
    
    for comp in ecosystem.get('components', []):
        cid = comp['id']
        label = comp.get('label', cid)
        
        # Load profile
        profile_path = os.path.join(repo_root, 'engineering', 'maturity', 'profiles', f"{cid}.yaml")
        profile = read_yaml(profile_path)
        
        if not profile:
            profile_state = "missing"
            governance_mode = "none"
        else:
            profile_state = "configured"
            governance_mode = profile.get('evaluation_mode', 'governed')
            
        # Load latest execution
        latest_rel_path = f"components/{cid}/latest.json"
        latest_abs_path = os.path.join(runtime_root, latest_rel_path)
        latest_data = read_json(latest_abs_path)
        
        if latest_data:
            technical_result = latest_data.get('result')
            stage = latest_data.get('target_stage')
            latest_ref = latest_rel_path
        else:
            technical_result = None
            stage = None
            latest_ref = None
            
        comp_entry = {
            "component_id": cid,
            "label": label,
            "governance_mode": governance_mode,
            "profile_state": profile_state,
            "technical_result": technical_result,
            "stage": stage
        }
        if latest_ref:
            comp_entry["latest_ref"] = latest_ref
            
        aggregated["components"].append(comp_entry)
        
    # Write atomically
    out_path = os.path.join(runtime_root, "components.json")
    tmp_path = out_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated, f, indent=2)
    os.rename(tmp_path, out_path)

if __name__ == '__main__':
    build_index()
