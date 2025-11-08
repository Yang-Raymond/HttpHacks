"""
Main application UI for Focus Timer App
"""
import customtkinter as ctk
from typing import List, Dict
import os


class AppEntry:
    """Represents a single app entry in the sidebar"""
    def __init__(self, parent, app_name: str, icon: str = "📱"):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.pack(fill="x", padx=10, pady=5)
        
        # Icon
        self.icon_label = ctk.CTkLabel(
            self.frame, 
            text=icon, 
            font=("Arial", 20),
            width=30
        )
        self.icon_label.pack(side="left", padx=(5, 10))
        
        # App name
        self.name_label = ctk.CTkLabel(
            self.frame, 
            text=app_name,
            font=("Arial", 14),
            anchor="w"
        )
        self.name_label.pack(side="left", fill="x", expand=True)
        
        # Toggle switch
        self.switch = ctk.CTkSwitch(
            self.frame, 
            text="",
            width=50,
            command=self.on_toggle
        )
        self.switch.pack(side="right", padx=5)
        
    def on_toggle(self):
        """Callback for when switch is toggled - backend will implement"""
        pass


class FocusTimerApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("Focus Timer")
        self.geometry("900x600")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create UI components
        self.create_sidebar()
        self.create_main_content()
        
        # App entries list
        self.app_entries: List[AppEntry] = []
        
        # Add sample apps (for demonstration)
        self.add_sample_apps()
        
    def create_sidebar(self):
        """Create the left sidebar with app list"""
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(1, weight=1)
        
        # Sidebar title
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="Blocked Apps",
            font=("Arial", 18, "bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Scrollable frame for app entries
        self.apps_container = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent"
        )
        self.apps_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add app button at bottom
        self.add_app_btn = ctk.CTkButton(
            self.sidebar,
            text="➕  Add app",
            font=("Arial", 14),
            height=40,
            fg_color="transparent",
            border_width=2,
            command=self.on_add_app
        )
        self.add_app_btn.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
    def create_main_content(self):
        """Create the main content area with timer and start button"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        
        # Center container
        center_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        center_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Timer circle frame
        self.timer_frame = ctk.CTkFrame(
            center_container,
            width=300,
            height=300,
            corner_radius=150,
            border_width=15,
            border_color=("#3B3B3B", "#2B2B2B"),
            fg_color="transparent"
        )
        self.timer_frame.pack(pady=(0, 40))
        
        # Timer label
        self.timer_label = ctk.CTkLabel(
            self.timer_frame,
            text="Hour:Min:Sec",
            font=("Arial", 24),
            text_color=("gray50", "gray60")
        )
        self.timer_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Start button
        self.start_btn = ctk.CTkButton(
            center_container,
            text="Start",
            font=("Arial", 18),
            width=200,
            height=50,
            corner_radius=25,
            command=self.on_start
        )
        self.start_btn.pack()
        
    def add_sample_apps(self):
        """Add sample app entries for demonstration"""
        # Instagram icon (using camera emoji as substitute)
        app1 = AppEntry(self.apps_container, "Appname", "📷")
        self.app_entries.append(app1)
        
        # YouTube icon (using play button emoji as substitute)
        app2 = AppEntry(self.apps_container, "Appname", "▶️")
        self.app_entries.append(app2)
        
    def add_app_entry(self, app_name: str, icon: str = "📱"):
        """Add a new app entry to the sidebar"""
        app_entry = AppEntry(self.apps_container, app_name, icon)
        self.app_entries.append(app_entry)
        
    def remove_app_entry(self, app_entry: AppEntry):
        """Remove an app entry from the sidebar"""
        if app_entry in self.app_entries:
            app_entry.frame.destroy()
            self.app_entries.remove(app_entry)
    
    def on_add_app(self):
        """Callback for Add app button - backend will implement"""
        pass
    
    def on_start(self):
        """Callback for Start button - backend will implement"""
        pass
    
    def update_timer(self, hours: int, minutes: int, seconds: int):
        """Update the timer display"""
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.timer_label.configure(text=time_str)
    
    def set_start_button_text(self, text: str):
        """Update the start button text (e.g., 'Stop', 'Pause', 'Resume')"""
        self.start_btn.configure(text=text)


def main():
    """Entry point for the application"""
    app = FocusTimerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
