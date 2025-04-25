import os
import tkinter as tk
from typing import Dict, Callable
import logging
import webbrowser
from tkinter import messagebox
from PIL import Image, ImageTk

import customtkinter as ctk

from core.settings import API_PROVIDER, AI_API_KEY, DARK_MODE, APP_CONFIG, save_setting

logger = logging.getLogger(__name__)

class APISettingsDialog(ctk.CTkToplevel):
    """Dialog for configuring API settings."""
    
    def __init__(self, parent, callback: Callable = None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        
        # Window setup
        self.title("API Settings")
        self.geometry("500x500")
        self.minsize(500, 500)
        self.resizable(False, False)
        
        # Make this window modal
        self.transient(parent)
        self.grab_set()
        
        # Store current values - try from config first, then globals, then from parent
        self.current_provider = APP_CONFIG.get("api_provider", API_PROVIDER)
        self.current_api_key = APP_CONFIG.get("api_key", AI_API_KEY)
        
        # Đọc giá trị dark_mode từ nhiều nguồn để đảm bảo chính xác
        self.current_dark_mode = None
        
        # 1. Nếu parent có thuộc tính is_dark_mode, sử dụng nó
        if hasattr(parent, "is_dark_mode"):
            self.current_dark_mode = parent.is_dark_mode
            logger.info(f"Got dark mode from parent: {self.current_dark_mode}")
        # 2. Nếu không, thử đọc từ cấu hình
        elif "dark_mode" in APP_CONFIG:
            self.current_dark_mode = bool(APP_CONFIG.get("dark_mode"))
            logger.info(f"Got dark mode from APP_CONFIG: {self.current_dark_mode}")
        # 3. Nếu không, sử dụng giá trị mặc định từ settings
        else:
            self.current_dark_mode = bool(DARK_MODE)
            logger.info(f"Using default DARK_MODE: {self.current_dark_mode}")
            
        # 4. Cuối cùng, kiểm tra giá trị hiện tại của customtkinter
        current_ctk_mode = ctk.get_appearance_mode().lower() == "dark"
        logger.info(f"Current customtkinter mode: {ctk.get_appearance_mode()} (is dark: {current_ctk_mode})")
        
        # Đảm bảo giá trị hiện tại là boolean
        self.current_dark_mode = bool(self.current_dark_mode)
        logger.info(f"Final settings dialog dark mode value: {self.current_dark_mode}")
        
        # Flag to indicate we're done
        self.result = None
        
        self._create_widgets()
        
        # Make dialog modal
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_visibility()
        self.focus_set()
        
        # Center the dialog window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        logger.debug("API Settings dialog initialized")
    
    def _create_widgets(self):
        """Create the UI elements."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Description text should expand
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="API Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Provider selection
        provider_frame = ctk.CTkFrame(self)
        provider_frame.grid(row=1, column=0, padx=20, pady=(20, 5), sticky="ew")
        provider_frame.grid_columnconfigure(1, weight=1)
        
        provider_label = ctk.CTkLabel(
            provider_frame,
            text="API Provider:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        provider_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.provider_var = ctk.StringVar(value=self.current_provider)
        self.provider_menu = ctk.CTkOptionMenu(
            provider_frame,
            values=["openai", "stability", "gemini"],
            variable=self.provider_var,
            command=self._on_provider_change,
            width=200
        )
        self.provider_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # API Key
        key_frame = ctk.CTkFrame(self)
        key_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        key_frame.grid_columnconfigure(2, weight=1)
        
        self.key_label = ctk.CTkLabel(
            key_frame,
            text="API Key:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.key_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.key_var = ctk.StringVar(value=self.current_api_key)
        self.key_entry = ctk.CTkEntry(
            key_frame,
            textvariable=self.key_var,
            width=300,
            show="•"
        )
        self.key_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Show/Hide key
        self.show_key = False
        self.show_key_btn = ctk.CTkButton(
            key_frame,
            text="👁️",
            width=30,
            command=self._toggle_key_visibility
        )
        self.show_key_btn.grid(row=0, column=2, padx=(0, 10), pady=10, sticky="e")
        
        # Description frame
        desc_frame = ctk.CTkFrame(self)
        desc_frame.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        desc_frame.grid_columnconfigure(0, weight=1)
        desc_frame.grid_rowconfigure(0, weight=1)
        
        # Description text
        self.desc_text = ctk.CTkTextbox(desc_frame, height=200, wrap="word")
        self.desc_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.desc_text.configure(state="disabled")
        
        # Update description based on current provider
        self._update_description()
        
        # Button frame - đặt ở cuối dialog và cho thấy rõ ràng
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="ew")
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Save button - đặt bên trái
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Save",
            width=150,
            command=self._on_save
        )
        save_btn.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        # Cancel button - đặt bên phải
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            width=150,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            command=self._on_cancel
        )
        cancel_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")
    
    def _update_description(self):
        """Update the description based on the selected provider."""
        provider = self.provider_var.get()
        
        # Enable text editing
        self.desc_text.configure(state="normal")
        self.desc_text.delete("1.0", "end")
        
        if provider == "openai":
            self.desc_text.insert("1.0", (
                "OpenAI API for DALL-E image generation.\n\n"
                "To use this API:\n"
                "1. Register at https://platform.openai.com/\n"
                "2. Create an API key in your dashboard\n"
                "3. Paste your API key here\n\n"
                "The DALL-E models can generate high-quality images from text prompts."
            ))
        elif provider == "stability":
            self.desc_text.insert("1.0", (
                "Stability AI API for SDXL image generation.\n\n"
                "To use this API:\n"
                "1. Register at https://platform.stability.ai/\n"
                "2. Create an API key in your dashboard\n"
                "3. Paste your API key here\n\n"
                "Stability AI offers state-of-the-art AI image generation."
            ))
        elif provider == "gemini":
            self.desc_text.insert("1.0", (
                "Google's Gemini API for image generation.\n\n"
                "To use this API:\n"
                "1. Register at https://aistudio.google.com/\n"
                "2. Create an API key in your Google AI Studio\n"
                "3. Paste your API key here\n\n"
                "Gemini is Google's multimodal AI that can generate images from text."
            ))
        
        # Disable text editing again
        self.desc_text.configure(state="disabled")
    
    def _on_provider_change(self, provider):
        """Handle provider change."""
        self._update_description()
        self.key_var.set(AI_API_KEY or "")
    
    def _toggle_key_visibility(self):
        """Toggle the visibility of the API key."""
        self.show_key = not self.show_key
        self.key_entry.configure(show="" if self.show_key else "•")
        self.show_key_btn.configure(text="👁️‍🗨️" if self.show_key else "👁️")
    
    def _on_save(self):
        """Save API settings."""
        provider = self.provider_var.get()
        api_key = self.key_var.get().strip()
        
        # Validate API key
        if not api_key:
            tk.messagebox.showerror("Error", "API key cannot be empty.")
            return
        
        # Save settings using the configuration system
        try:
            # Save API settings
            save_setting("API_KEY", api_key)
            save_setting("API_PROVIDER", provider)
            
            # Log the change
            logger.info(f"API settings saved: provider={provider}")
            
            # Execute callback if provided
            if self.callback:
                self.callback(provider, api_key)
            
            # Close dialog
            self.destroy()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            logger.error(f"Failed to save settings: {e}")
    
    def _on_cancel(self):
        """Cancel and close dialog."""
        self.destroy() 