import os
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import shutil
import logging
from typing import Dict, Any, Callable, Optional
import platform
import subprocess

from core.db import Database
from core.settings import ensure_dirs

logger = logging.getLogger(__name__)

class HistoryTab(ctk.CTkFrame):
    """Tab for viewing and managing image generation history."""
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.parent = parent
        self.main_window = main_window
        self.db = Database()
        self.history_frames = []
        self.current_items = []
        
        # Create layout
        self._create_widgets()
        
        # Initially hidden
        self.hide()
        
    def _create_widgets(self):
        """Create and configure widgets."""
        # Top controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.refresh_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Refresh", 
            width=100,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self.refresh
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.controls_frame,
            width=200,
            placeholder_text="Search prompts...",
            textvariable=self.search_var
        )
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        self.search_btn = ctk.CTkButton(
            self.controls_frame,
            text="Search",
            width=100,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._on_search
        )
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_search_btn = ctk.CTkButton(
            self.controls_frame,
            text="Clear",
            width=100,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=lambda: (self.search_var.set(""), self.refresh())
        )
        self.clear_search_btn.pack(side=tk.LEFT, padx=5)
        
        # Scrollable frame for history items
        self.history_container = ctk.CTkScrollableFrame(self)
        self.history_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def refresh(self):
        """Refresh the history list."""
        # Clear existing items
        for frame in self.history_frames:
            frame.destroy()
        self.history_frames = []
        
        # Get search term if exists
        search_term = self.search_var.get().strip()
        
        # Fetch entries
        if search_term:
            items = self.db.search_images(search_term)
        else:
            items = self.db.get_all_images()
        
        self.current_items = items
        
        # Create history items
        for i, item in enumerate(items):
            frame = self._create_history_item(item, i)
            frame.pack(fill=tk.X, expand=True, pady=5)
            self.history_frames.append(frame)
        
        if not items:
            no_items_label = ctk.CTkLabel(
                self.history_container,
                text="No history items found.",
                font=("Arial", 14),
                text_color="grey" if ctk.get_appearance_mode() == "light" else "darkgrey"
            )
            no_items_label.pack(pady=20)
            self.history_frames.append(no_items_label)
    
    def _create_history_item(self, item: Dict[str, Any], index: int) -> ctk.CTkFrame:
        """Create a history item widget."""
        frame = ctk.CTkFrame(self.history_container)
        
        # Container for image and info
        content_frame = ctk.CTkFrame(frame)
        content_frame.pack(fill=tk.X, expand=True, padx=10, pady=10)
        
        # Try to load the thumbnail
        try:
            filepath = item["filepath"]
            
            if os.path.exists(filepath):
                img = Image.open(filepath)
                # Resize for thumbnail
                img.thumbnail((150, 150))
                img_tk = ImageTk.PhotoImage(img)
                
                # Image display
                img_label = tk.Label(content_frame, image=img_tk, bg="#484747" if ctk.get_appearance_mode().lower() == "dark" else "#DFDEDE")
                img_label.image = img_tk  # Keep a reference
                img_label.pack(side=tk.LEFT, padx=10, pady=10)
            else:
                # If file is missing, show placeholder
                missing_label = ctk.CTkLabel(
                    content_frame,
                    text="Image\nFile\nMissing",
                    font=("Arial", 12),
                    width=150,
                    height=150,
                    text_color="grey" if ctk.get_appearance_mode() == "light" else "darkgrey"
                )
                missing_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        except Exception as e:
            logger.error(f"Error loading history image: {e}")
            error_label = ctk.CTkLabel(
                content_frame,
                text="Error\nLoading\nImage",
                font=("Arial", 12),
                width=150,
                height=150,
                text_color="red"
            )
            error_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Info frame
        info_frame = ctk.CTkFrame(content_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Prompt
        prompt_label = ctk.CTkLabel(
            info_frame,
            text="Prompt:",
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        prompt_label.pack(anchor="w")
        
        prompt_text = ctk.CTkTextbox(
            info_frame,
            height=60,
            wrap="word",
            activate_scrollbars=False
        )
        prompt_text.insert("1.0", item["prompt"])
        prompt_text.configure(state="disabled")
        prompt_text.pack(fill=tk.X, expand=True, pady=5)
        
        # Date and details
        details_label = ctk.CTkLabel(
            info_frame,
            text=f"Created: {item['created_at']} | Provider: {item['provider']} | Size: {item.get('width', 'N/A')}x{item.get('height', 'N/A')}",
            font=("Arial", 10),
            text_color="grey" if ctk.get_appearance_mode() == "light" else "darkgrey",
            anchor="w"
        )
        details_label.pack(anchor="w", pady=5)
        
        # Action buttons
        buttons_frame = ctk.CTkFrame(info_frame)
        buttons_frame.pack(anchor="w", pady=5)
        
        open_btn = ctk.CTkButton(
            buttons_frame,
            text="Open",
            width=80,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=lambda i=item: self._on_open(i)
        )
        open_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            width=80,
            fg_color=["#D32F2F", "#D32F2F"],
            hover_color=["#B71C1C", "#B71C1C"],
            command=lambda i=item: self._on_delete(i)
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        return frame
    
    def _on_search(self):
        """Handle search button click."""
        self.refresh()
    
    def _on_open(self, item: Dict[str, Any]):
        """Open the image file."""
        filepath = item["filepath"]
        if os.path.exists(filepath):
            # Use the system's default application to open the file
            logger.debug(f"Opening file: {filepath}")
            
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', filepath))
            else:  # Linux
                subprocess.call(('xdg-open', filepath))
        else:
            logger.warning(f"File not found: {filepath}")
            # Show error message
            messagebox.showerror(
                "Error",
                f"The file {filepath} does not exist."
            )
    
    def _on_delete(self, item: Dict[str, Any]):
        """Delete an image from history."""
        # Confirm delete
        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this image from history?"
        ):
            return
        
        # Delete from database
        success = self.db.delete_image(item["id"])
        
        if success:
            # Also delete the file
            filepath = item["filepath"]
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.debug(f"Deleted file: {filepath}")
                except Exception as e:
                    logger.error(f"Error deleting file: {e}")
            
            # Refresh the list
            self.refresh()
        else:
            logger.error(f"Failed to delete item: {item['id']}")
    
    def update_ui_colors(self):
        """Update UI colors based on current appearance mode."""
        # Cập nhật màu cho các phần tử hiện có
        for frame in self.history_frames:
            # Chỉ cập nhật nhãn hình ảnh
            for child in frame.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for item in child.winfo_children():
                        if isinstance(item, tk.Label):
                            item.configure(bg="#484747" if ctk.get_appearance_mode().lower() == "dark" else "#DFDEDE")
        
    def show(self):
        """Show this tab and refresh the content."""
        self.grid(row=0, column=0, sticky="nsew")
        self.refresh()  # Load latest entries
    
    def hide(self):
        """Hide this tab."""
        self.grid_forget() 