import json
from typing import Dict, List

class BlocklistManager:
    def __init__(self, path: str):
        self.path = path
        self.data: Dict = {}  # Full JSON structure
        self.load_blocklist()

    def load_blocklist(self):
        with open(self.path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        # Ensure "websites" key exists
        if "websites" not in self.data:
            self.data["websites"] = {}

    def save_blocklist(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get_all_sites(self) -> List[str]:
        # Get all website/app names from the blocklist
        return list(self.data.get("websites", {}).keys())

    def is_blocked(self, site_name: str) -> bool:
        # Check if a specific site/app is blocked
        if site_name not in self.data.get("websites", {}):
            return False
        return self.data["websites"][site_name].get("blocked", False)

    def set_blocked(self, site_name: str, blocked: bool):
        # Set the blocked status for a specific site/app
        if site_name not in self.data.get("websites", {}):
            return
        self.data["websites"][site_name]["blocked"] = blocked
        self.save_blocklist()

    def add_entry(self, name: str, urls: List[str] = None, apps: str = ""):
        # Add a new entry to the blocklist
        if "websites" not in self.data:
            self.data["websites"] = {}
        
        self.data["websites"][name] = {
            "blocked": False,
            "apps": apps,
            "urls": urls if urls else []
        }
        self.save_blocklist()

    def add_website(self, name: str, url: str):
        # Add a new website entry
        self.add_entry(name, urls=[url], apps="")

    def add_app(self, name: str, exe_pattern: str):
        # Add a new app entry
        self.add_entry(name, urls=[], apps=exe_pattern)

    def get_blocked_urls(self) -> List[str]:
        # Return all URLs from blocked entries
        urls = []
        for site_name, site_data in self.data.get("websites", {}).items():
            if site_data.get("blocked", False):
                urls.extend(site_data.get("urls", []))
        return urls

    def get_blocked_apps(self) -> List[str]:
        # Return all app patterns from blocked entries
        apps = []
        for site_name, site_data in self.data.get("websites", {}).items():
            if site_data.get("blocked", False):
                app_pattern = site_data.get("apps", "")
                if app_pattern:
                    apps.append(app_pattern)
        return apps
        
    def set_all_blocked(self, blocked: bool):
        # Set all websites/apps to the same blocked status
        for site_name in self.data.get("websites", {}).keys():
            self.data["websites"][site_name]["blocked"] = blocked
        self.save_blocklist()

    def are_all_blocked(self) -> bool:
        # Check if all websites/apps are blocked
        websites = self.data.get("websites", {})
        if not websites:
            return False
        return all(site_data.get("blocked", False) for site_data in websites.values())