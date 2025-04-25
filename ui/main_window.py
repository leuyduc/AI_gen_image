import os
import logging
import tkinter as tk
from pathlib import Path
import customtkinter as ctk

from ui.generate_tab import GenerateTab
from ui.history_tab import HistoryTab
from ui.settings_dialog import APISettingsDialog
from core.settings import DARK_MODE, DEFAULT_FONT, API_PROVIDER, APP_CONFIG, save_setting

logger = logging.getLogger(__name__)

class MainWindow(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        # Luôn sử dụng chế độ tối
        self.is_dark_mode = True
        logger.info("Initializing with dark mode only")
        
        # Set appearance mode explicitly to dark
        ctk.set_appearance_mode("dark")
        
        super().__init__()
        
        # Configure window
        self.title("AI Image Generator")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Set icon if available
        icon_path = Path(__file__).parent.parent / "resources" / "app_icon.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Tabs frame
        self.grid_rowconfigure(1, weight=1)  # Content frame
        self.grid_rowconfigure(2, weight=0)  # Status bar
        
        # Define common colors for the application
        self.colors = {
            "blue": {"light": "#3B8ED0", "dark": "#1F6AA5"},
            "blue_hover": {"light": "#36719F", "dark": "#144870"},
            "gray": {"light": "#DFDEDE", "dark": "#484747"},
            "gray_hover": {"light": "#C7C6C6", "dark": "#5A5959"},
            "canvas_bg": {"light": "#EBEBEB", "dark": "#2B2B2B"}
        }
        
        # Create tab buttons frame
        self.tab_frame = ctk.CTkFrame(self)
        self.tab_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.tab_frame.grid_columnconfigure(3, weight=1)  # Make the right side expandable
        
        # Create tabs
        self.current_tab = None
        
        # Create tab buttons
        self.generate_btn = self._create_tab_button("Generate", 0, lambda: self.show_tab("generate"))
        self.history_btn = self._create_tab_button("History", 1, lambda: self.show_tab("history"))

        # Create settings button on the right
        self.settings_btn = ctk.CTkButton(
            self.tab_frame,
            text="API Settings",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=self.colors["blue"]["dark"],
            hover_color=self.colors["blue_hover"]["dark"],
            command=self._show_api_settings
        )
        self.settings_btn.grid(row=0, column=4, padx=10, pady=0, sticky="e")
        
        # Get current provider from config
        current_provider = APP_CONFIG.get("api_provider", API_PROVIDER)
        
        # Create API provider label
        self.provider_label = ctk.CTkLabel(
            self.tab_frame,
            text=f"Using: {current_provider.upper()}",
            font=ctk.CTkFont(size=12),
            width=120,
        )
        self.provider_label.grid(row=0, column=3, padx=10, pady=0, sticky="e")
        
        # Create content frame
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Create tabs
        self.tabs = {
            "generate": GenerateTab(self.content_frame, self),
            "history": HistoryTab(self.content_frame, self)
        }
        
        # Create status bar
        self.status_bar = ctk.CTkLabel(
            self, 
            text="Ready", 
            font=ctk.CTkFont(size=11),
            anchor="w", 
            height=25
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        # Show default tab
        self.show_tab("generate")
        
        # Đảm bảo tất cả các màu sắc được đặt đúng khi khởi động
        self.after(100, self._update_all_button_colors)
        
        logger.info("Main window initialized")
    
    def _apply_appearance_mode(self, dark_mode):
        """Apply dark mode appearance."""
        try:
            # Luôn sử dụng chế độ tối, bỏ qua tham số
            self.is_dark_mode = True
            
            # Lưu vào cài đặt
            save_setting("DARK_MODE", True)
            
            # Thiết lập chế độ giao diện tối
            ctk.set_appearance_mode("dark")
            self.update_idletasks()
            
            # Cập nhật lại màu cho tất cả các nút
            self._update_all_button_colors()
            
        except Exception as e:
            logger.error(f"Error applying appearance mode: {e}", exc_info=True)
    
    def _update_all_button_colors(self):
        """Cập nhật màu sắc cho tất cả các nút dựa trên chế độ tối."""
        try:
            # Chỉ sử dụng chế độ tối 
            mode_key = "dark"
            
            logger.info("Updating UI colors for dark mode")
            
            # 1. Cập nhật nút trong tab bar
            self.settings_btn.configure(
                fg_color=self.colors["blue"][mode_key],
                hover_color=self.colors["blue_hover"][mode_key]
            )
            
            # 2. Cập nhật nút tab (dựa vào tab hiện tại)
            active_tab = self.current_tab
            if hasattr(self, "generate_btn") and hasattr(self, "history_btn"):
                self.generate_btn.configure(
                    fg_color=self.colors["blue" if active_tab == "generate" else "gray"][mode_key],
                    hover_color=self.colors["blue_hover" if active_tab == "generate" else "gray_hover"][mode_key]
                )
                self.history_btn.configure(
                    fg_color=self.colors["blue" if active_tab == "history" else "gray"][mode_key],
                    hover_color=self.colors["blue_hover" if active_tab == "history" else "gray_hover"][mode_key]
                )
            
            # 3. Cập nhật canvas trong Generate Tab
            if "generate" in self.tabs and hasattr(self.tabs["generate"], "canvas"):
                self.tabs["generate"].canvas.configure(bg=self.colors["canvas_bg"][mode_key])
            
            # 4. Cập nhật nút trong History Tab
            if "history" in self.tabs:
                hist_tab = self.tabs["history"]
                # Cập nhật nút chính trong History
                for btn_name in ["refresh_btn", "search_btn", "clear_search_btn"]:
                    if hasattr(hist_tab, btn_name):
                        btn = getattr(hist_tab, btn_name)
                        btn.configure(
                            fg_color=self.colors["blue"][mode_key],
                            hover_color=self.colors["blue_hover"][mode_key]
                        )
                
                # Cập nhật màu nền cho label ảnh
                if hasattr(hist_tab, "history_frames"):
                    for frame in hist_tab.history_frames:
                        try:
                            for child in frame.winfo_children():
                                if isinstance(child, ctk.CTkFrame):
                                    for item in child.winfo_children():
                                        if isinstance(item, tk.Label):
                                            item.configure(bg=self.colors["gray"][mode_key])
                        except Exception as e:
                            logger.error(f"Error updating history frames: {e}")
            
        except Exception as e:
            logger.error(f"Error updating button colors: {e}", exc_info=True)
    
    def _create_tab_button(self, text, col, command):
        """Create a tab button."""
        mode_key = "dark"
        
        # Tạo nút với màu tương ứng với chế độ tối
        btn = ctk.CTkButton(
            self.tab_frame,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=35,
            fg_color=self.colors["gray"][mode_key],
            hover_color=self.colors["gray_hover"][mode_key],
            command=command
        )
        btn.grid(row=0, column=col, padx=(0 if col > 0 else 0, 5), pady=0, sticky="w")
        return btn
    
    def show_tab(self, tab_name):
        """Switch to the specified tab."""
        if self.current_tab == tab_name:
            return
        
        # Hide current tab
        if self.current_tab:
            self.tabs[self.current_tab].hide()
            
        # Show new tab
        self.tabs[tab_name].show()
        self.current_tab = tab_name
        
        # Update button states and all UI colors
        self._update_all_button_colors()
        
        logger.debug(f"Switched to {tab_name} tab")
    
    def _show_api_settings(self):
        """Show API settings dialog."""
        # Pass the current dark mode setting to the dialog
        logger.info(f"Opening API settings dialog with current dark mode: {self.is_dark_mode}")
        APISettingsDialog(self, self._on_api_settings_changed)
    
    def _on_api_settings_changed(self, provider, api_key, dark_mode=True):
        """Handle API settings change."""
        # Log API settings change
        logger.info(f"API settings changed - provider: {provider}")
        
        # Update the provider label
        self.provider_label.configure(text=f"Using: {provider.upper()}")
        
        # Update the API client in the generate tab
        if hasattr(self.tabs["generate"], "api_client"):
            self.tabs["generate"].api_client.api_key = api_key
            self.tabs["generate"].api_client.provider = provider
            
            # Update the size dropdown in generate tab based on the new provider
            self.tabs["generate"].update_size_options(provider)
        
        # Set status message
        self.set_status(f"Settings updated: {provider.upper()}")
    
    def set_status(self, message):
        """Update status bar message."""
        self.status_bar.configure(text=message)
        self.update_idletasks()
    
    def show_error(self, title, message):
        """Show error dialog."""
        tk.messagebox.showerror(title, message)
    
    def show_info(self, title, message):
        """Show info dialog."""
        tk.messagebox.showinfo(title, message)
    
    def update_history(self):
        """Refresh history tab."""
        if self.current_tab == "history":
            self.tabs["history"].refresh() 