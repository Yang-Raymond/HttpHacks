import json
from typing import Dict, List

class BlocklistManager:
    def __init__(self, path: str):
        self.path = path
        self.all_sites: Dict[str, List[str]] = {}  # { "Youtube": [...], "Reddit": [...] }
        self.blocked: Dict[str, List[str]] = {}
        self.unblocked: Dict[str, List[str]] = {}
        self.load_blocklist()

    def load_blocklist(self):
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Each top-level key is a website group
        for site, urls in data.items():
            self.all_sites[site] = urls
            self.unblocked[site] = urls.copy()
            self.blocked[site] = []

    def set_blocked(self, site_name: str, blocked: bool):
        if site_name not in self.all_sites: return
        if blocked:
            self.blocked[site_name] = self.all_sites[site_name]
            self.unblocked[site_name] = []
        else:
            self.blocked[site_name] = []
            self.unblocked[site_name] = self.all_sites[site_name]

    def get_blocked_urls(self) -> List[str]:
        urls = []
        for b in self.blocked.values():
            urls.extend(b)
        return urls
