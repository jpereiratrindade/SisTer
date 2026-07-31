#!/usr/bin/env python3
import sys, json

def main():
    if len(sys.argv) < 2:
        print("Usage: json-to-tabular.py <results.json>")
        sys.exit(1)
        
    json_path = sys.argv[1]
    with open(json_path, "r") as f:
        data = json.load(f)
        
    if "stages" in data:
        for stage_obj in data["stages"]:
            stage_name = stage_obj.get("id")
            for check in stage_obj.get("checks", []):
                status = check.get("status")
                cid = check.get("id")
                mandatory = "yes" if check.get("mandatory") else "no"
                desc = check.get("description", "")
                detail = check.get("detail", "")
                
                desc = desc.replace("\t", " ").replace("\n", " ").replace("\r", " ")
                detail = detail.replace("\t", " ").replace("\n", " ").replace("\r", " ")
                print(f"{status}\t{stage_name}\t{cid}\t{mandatory}\t{desc}\t{detail}")
    else:
        for check in data.get("checks", []):
            status = check.get("status")
            stage_name = check.get("stage")
            cid = check.get("id")
            mandatory = "yes" if check.get("mandatory") else "no"
            desc = check.get("description", "")
            detail = check.get("detail", "")
            
            desc = desc.replace("\t", " ").replace("\n", " ").replace("\r", " ")
            detail = detail.replace("\t", " ").replace("\n", " ").replace("\r", " ")
            print(f"{status}\t{stage_name}\t{cid}\t{mandatory}\t{desc}\t{detail}")

if __name__ == "__main__":
    main()
