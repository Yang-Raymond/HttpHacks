import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import subprocess
import sys

class FocusAppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus App - Website Blocker")
        self.root.geometry("900x600")
        self.root.configure(bg="#2b2b2b")
        
        # Load blocklist
        self.blocklist_file = "blocklist.json"
        self.websites = self.load_websites()
        self.website_states = {site: True for site in self.websites}  # True = blocked, False = allowed
        
        # Timer variables
        self.timer_minutes = tk.IntVar(value=25)
        self.timer_seconds = 0
        self.timer_running = False
        self.blocking_process = None
        
        # Create main container
        main_container = tk.Frame(root, bg="#2b2b2b")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left Panel - Website List
        self.create_left_panel(main_container)
        
        # Right Panel - Timer
        self.create_right_panel(main_container)
        
    def load_websites(self):
        """Load websites from blocklist.json"""
        if os.path.exists(self.blocklist_file):
            with open(self.blocklist_file, 'r') as f:
                data = json.load(f)
                # Get unique base domains (remove wildcards and duplicates)
                blocked = data.get('blocked', [])
                unique_sites = []
                seen = set()
                for site in blocked:
                    # Remove wildcards and clean up
                    clean_site = site.replace('*.', '').replace('*', '')
                    if clean_site and clean_site not in seen:
                        seen.add(clean_site)
                        unique_sites.append(clean_site)
                return sorted(unique_sites)
        return []
    
    def save_blocklist(self):
        """Save the current blocklist to JSON"""
        blocked_sites = []
        for site, is_blocked in self.website_states.items():
            if is_blocked:
                blocked_sites.append(site)
                blocked_sites.append(f"*.{site}")
        
        with open(self.blocklist_file, 'w') as f:
            json.dump({"blocked": blocked_sites}, f, indent=2)
    
    def create_left_panel(self, parent):
        """Create the left panel with website toggles"""
        left_frame = tk.Frame(parent, bg="#1e1e1e", relief=tk.RAISED, borderwidth=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Header
        header = tk.Label(left_frame, text="📱 Websites to Block", 
                         font=("Segoe UI", 16, "bold"), 
                         bg="#1e1e1e", fg="#ffffff")
        header.pack(pady=(10, 5))
        
        # Description
        desc = tk.Label(left_frame, text="Toggle websites you want to block during focus sessions", 
                       font=("Segoe UI", 9), 
                       bg="#1e1e1e", fg="#aaaaaa")
        desc.pack(pady=(0, 10))
        
        # Search bar
        search_frame = tk.Frame(left_frame, bg="#1e1e1e")
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_websites)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                               font=("Segoe UI", 10),
                               bg="#2b2b2b", fg="#ffffff", 
                               insertbackground="#ffffff",
                               relief=tk.FLAT)
        search_entry.pack(fill=tk.X, ipady=5)
        search_entry.insert(0, "🔍 Search websites...")
        search_entry.bind('<FocusIn>', lambda e: search_entry.delete(0, tk.END) if search_entry.get().startswith("🔍") else None)
        
        # Scrollable website list
        list_container = tk.Frame(left_frame, bg="#1e1e1e")
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Canvas and scrollbar
        canvas = tk.Canvas(list_container, bg="#1e1e1e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add websites
        self.website_widgets = {}
        self.populate_websites()
        
        # Buttons at bottom
        button_frame = tk.Frame(left_frame, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        select_all_btn = tk.Button(button_frame, text="Select All", 
                                   command=self.select_all_websites,
                                   bg="#4a4a4a", fg="#ffffff", 
                                   font=("Segoe UI", 9),
                                   relief=tk.FLAT, cursor="hand2")
        select_all_btn.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill=tk.X)
        
        deselect_all_btn = tk.Button(button_frame, text="Deselect All", 
                                     command=self.deselect_all_websites,
                                     bg="#4a4a4a", fg="#ffffff", 
                                     font=("Segoe UI", 9),
                                     relief=tk.FLAT, cursor="hand2")
        deselect_all_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
    
    def populate_websites(self):
        """Populate the website list"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.website_widgets.clear()
        
        # Add each website
        for site in self.websites:
            self.create_website_toggle(site)
    
    def create_website_toggle(self, site):
        """Create a toggle button for a website"""
        frame = tk.Frame(self.scrollable_frame, bg="#2b2b2b", relief=tk.FLAT)
        frame.pack(fill=tk.X, padx=5, pady=3)
        
        # Website label
        label = tk.Label(frame, text=site, 
                        font=("Segoe UI", 10),
                        bg="#2b2b2b", fg="#ffffff", 
                        anchor="w")
        label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=8)
        
        # Toggle button
        is_blocked = self.website_states.get(site, True)
        btn_text = "🔒 ON" if is_blocked else "🔓 OFF"
        btn_color = "#e74c3c" if is_blocked else "#27ae60"
        
        toggle_btn = tk.Button(frame, text=btn_text, 
                              command=lambda s=site: self.toggle_website(s),
                              bg=btn_color, fg="#ffffff", 
                              font=("Segoe UI", 9, "bold"),
                              width=8,
                              relief=tk.FLAT, cursor="hand2")
        toggle_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
        self.website_widgets[site] = (frame, label, toggle_btn)
    
    def toggle_website(self, site):
        """Toggle website blocking state"""
        current_state = self.website_states[site]
        self.website_states[site] = not current_state
        
        # Update button
        frame, label, btn = self.website_widgets[site]
        new_state = self.website_states[site]
        btn.config(
            text="🔒 ON" if new_state else "🔓 OFF",
            bg="#e74c3c" if new_state else "#27ae60"
        )
        
        # Save to file
        self.save_blocklist()
    
    def filter_websites(self, *args):
        """Filter websites based on search"""
        search_term = self.search_var.get().lower()
        if search_term.startswith("🔍"):
            search_term = ""
        
        for site in self.websites:
            frame, _, _ = self.website_widgets[site]
            if search_term in site.lower():
                frame.pack(fill=tk.X, padx=5, pady=3)
            else:
                frame.pack_forget()
    
    def select_all_websites(self):
        """Select all websites for blocking"""
        for site in self.websites:
            self.website_states[site] = True
            frame, label, btn = self.website_widgets[site]
            btn.config(text="🔒 ON", bg="#e74c3c")
        self.save_blocklist()
    
    def deselect_all_websites(self):
        """Deselect all websites"""
        for site in self.websites:
            self.website_states[site] = False
            frame, label, btn = self.website_widgets[site]
            btn.config(text="🔓 OFF", bg="#27ae60")
        self.save_blocklist()
    
    def create_right_panel(self, parent):
        """Create the right panel with timer"""
        right_frame = tk.Frame(parent, bg="#1e1e1e", relief=tk.RAISED, borderwidth=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Header
        header = tk.Label(right_frame, text="⏰ Focus Timer", 
                         font=("Segoe UI", 16, "bold"), 
                         bg="#1e1e1e", fg="#ffffff")
        header.pack(pady=(20, 10))
        
        # Timer display
        self.timer_label = tk.Label(right_frame, text="25:00", 
                                    font=("Segoe UI", 72, "bold"), 
                                    bg="#1e1e1e", fg="#3498db")
        self.timer_label.pack(pady=20)
        
        # Timer controls
        control_frame = tk.Frame(right_frame, bg="#1e1e1e")
        control_frame.pack(pady=20)
        
        # Time adjustment
        adjust_frame = tk.Frame(control_frame, bg="#1e1e1e")
        adjust_frame.pack(pady=10)
        
        tk.Label(adjust_frame, text="Set Minutes:", 
                font=("Segoe UI", 11), 
                bg="#1e1e1e", fg="#ffffff").pack(side=tk.LEFT, padx=5)
        
        minus_btn = tk.Button(adjust_frame, text="-", 
                             command=self.decrease_time,
                             bg="#4a4a4a", fg="#ffffff", 
                             font=("Segoe UI", 14, "bold"),
                             width=3,
                             relief=tk.FLAT, cursor="hand2")
        minus_btn.pack(side=tk.LEFT, padx=5)
        
        time_display = tk.Label(adjust_frame, textvariable=self.timer_minutes, 
                               font=("Segoe UI", 16, "bold"), 
                               bg="#2b2b2b", fg="#ffffff",
                               width=4, relief=tk.FLAT)
        time_display.pack(side=tk.LEFT, padx=5)
        
        plus_btn = tk.Button(adjust_frame, text="+", 
                            command=self.increase_time,
                            bg="#4a4a4a", fg="#ffffff", 
                            font=("Segoe UI", 14, "bold"),
                            width=3,
                            relief=tk.FLAT, cursor="hand2")
        plus_btn.pack(side=tk.LEFT, padx=5)
        
        # Start/Stop button
        self.start_btn = tk.Button(control_frame, text="▶ Start Focus Session", 
                                   command=self.toggle_timer,
                                   bg="#27ae60", fg="#ffffff", 
                                   font=("Segoe UI", 14, "bold"),
                                   width=20, height=2,
                                   relief=tk.FLAT, cursor="hand2")
        self.start_btn.pack(pady=20)
        
        # Status
        self.status_label = tk.Label(right_frame, text="Ready to focus", 
                                     font=("Segoe UI", 10), 
                                     bg="#1e1e1e", fg="#95a5a6")
        self.status_label.pack(pady=10)
        
        # Preset buttons
        preset_frame = tk.Frame(right_frame, bg="#1e1e1e")
        preset_frame.pack(pady=20)
        
        tk.Label(preset_frame, text="Quick Presets:", 
                font=("Segoe UI", 10), 
                bg="#1e1e1e", fg="#aaaaaa").pack(pady=(0, 10))
        
        preset_buttons = tk.Frame(preset_frame, bg="#1e1e1e")
        preset_buttons.pack()
        
        for minutes in [15, 25, 45, 60]:
            btn = tk.Button(preset_buttons, text=f"{minutes}m", 
                           command=lambda m=minutes: self.set_preset_time(m),
                           bg="#34495e", fg="#ffffff", 
                           font=("Segoe UI", 9),
                           width=6,
                           relief=tk.FLAT, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=5)
    
    def increase_time(self):
        """Increase timer by 5 minutes"""
        if not self.timer_running:
            current = self.timer_minutes.get()
            self.timer_minutes.set(min(current + 5, 180))
            self.update_timer_display()
    
    def decrease_time(self):
        """Decrease timer by 5 minutes"""
        if not self.timer_running:
            current = self.timer_minutes.get()
            self.timer_minutes.set(max(current - 5, 5))
            self.update_timer_display()
    
    def set_preset_time(self, minutes):
        """Set a preset time"""
        if not self.timer_running:
            self.timer_minutes.set(minutes)
            self.update_timer_display()
    
    def update_timer_display(self):
        """Update the timer display"""
        mins = self.timer_minutes.get()
        secs = self.timer_seconds
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
    
    def toggle_timer(self):
        """Start or stop the timer"""
        if not self.timer_running:
            self.start_focus_session()
        else:
            self.stop_focus_session()
    
    def start_focus_session(self):
        """Start the focus session"""
        # Check if any websites are selected
        selected_sites = [site for site, blocked in self.website_states.items() if blocked]
        if not selected_sites:
            messagebox.showwarning("No Websites Selected", 
                                  "Please select at least one website to block!")
            return
        
        self.timer_running = True
        self.timer_seconds = 0
        
        # Update UI
        self.start_btn.config(text="⏸ Stop Session", bg="#e74c3c")
        self.status_label.config(text="🎯 Focus session active - Stay focused!", fg="#27ae60")
        self.timer_label.config(fg="#e74c3c")
        
        # Start the blocker process
        self.start_blocker()
        
        # Start countdown
        self.countdown()
    
    def stop_focus_session(self):
        """Stop the focus session"""
        self.timer_running = False
        
        # Update UI
        self.start_btn.config(text="▶ Start Focus Session", bg="#27ae60")
        self.status_label.config(text="Ready to focus", fg="#95a5a6")
        self.timer_label.config(fg="#3498db")
        
        # Stop blocker
        self.stop_blocker()
        
        # Reset timer
        self.timer_seconds = 0
        self.update_timer_display()
    
    def countdown(self):
        """Countdown timer"""
        if self.timer_running:
            if self.timer_minutes.get() == 0 and self.timer_seconds == 0:
                # Timer finished
                self.stop_focus_session()
                messagebox.showinfo("Session Complete", 
                                   "🎉 Focus session complete! Great work!")
                return
            
            if self.timer_seconds == 0:
                self.timer_minutes.set(self.timer_minutes.get() - 1)
                self.timer_seconds = 59
            else:
                self.timer_seconds -= 1
            
            self.update_timer_display()
            self.root.after(1000, self.countdown)
    
    def start_blocker(self):
        """Start the blocker subprocess"""
        try:
            # Start mvp_blocker.py with --enable-pac
            self.blocking_process = subprocess.Popen(
                [sys.executable, "mvp_blocker.py", "--enable-pac"],
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            print("Blocker started")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start blocker: {e}")
            self.timer_running = False
    
    def stop_blocker(self):
        """Stop the blocker subprocess"""
        if self.blocking_process:
            try:
                self.blocking_process.terminate()
                self.blocking_process.wait(timeout=5)
                print("Blocker stopped")
            except Exception as e:
                print(f"Error stopping blocker: {e}")
            finally:
                self.blocking_process = None

def main():
    root = tk.Tk()
    app = FocusAppUI(root)
    
    # Handle window close
    def on_closing():
        if app.timer_running:
            if messagebox.askokcancel("Quit", "Focus session is active. Stop and quit?"):
                app.stop_focus_session()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
