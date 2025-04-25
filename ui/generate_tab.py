import os
import threading
import logging
import tkinter as tk
from pathlib import Path
from typing import Optional
from PIL import Image, ImageTk

import customtkinter as ctk

from core.api_client import APIClient
from core.db import Database
from core.settings import ensure_dirs, DEFAULT_IMAGE_SIZE, API_PROVIDER, APP_CONFIG

logger = logging.getLogger(__name__)

class GenerateTab:
    """Tab for generating images from text prompts."""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        
        # Use the new configuration system for API client initialization
        self.api_client = APIClient(
            api_key=APP_CONFIG.get("api_key", None),
            provider=APP_CONFIG.get("api_provider", None)
        )
        
        self.db = Database()
        self.frame = None
        self.preview_image = None
        self.generated_image = None
        self.generated_path = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI elements for the generate tab."""
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        
        # Input frame (top)
        input_frame = ctk.CTkFrame(self.frame)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Prompt label
        prompt_label = ctk.CTkLabel(
            input_frame,
            text="Prompt:",
            font=ctk.CTkFont(size=14)
        )
        prompt_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        # Prompt input
        self.prompt_var = ctk.StringVar()
        self.prompt_entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.prompt_var,
            placeholder_text="Describe the image you want to generate...",
            height=35,
            font=ctk.CTkFont(size=13)
        )
        self.prompt_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Negative prompt label
        neg_prompt_label = ctk.CTkLabel(
            input_frame,
            text="Negative Prompt:",
            font=ctk.CTkFont(size=14)
        )
        neg_prompt_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        # Negative prompt input
        self.neg_prompt_var = ctk.StringVar()
        self.neg_prompt_entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.neg_prompt_var,
            placeholder_text="Elements to avoid in the image (optional)",
            height=35,
            font=ctk.CTkFont(size=13)
        )
        self.neg_prompt_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Size selection
        size_label = ctk.CTkLabel(
            input_frame,
            text="Size:",
            font=ctk.CTkFont(size=14)
        )
        size_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        
        # Get appropriate size options for the current provider
        self.size_var = ctk.StringVar()
        
        self.size_options = self._get_size_options_for_provider(self.api_client.provider)
        self.size_var.set(self.size_options[0])  # Default to first option
        
        self.size_dropdown = ctk.CTkOptionMenu(
            input_frame,
            variable=self.size_var,
            values=self.size_options
        )
        self.size_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        # Generate button
        generate_btn = ctk.CTkButton(
            input_frame,
            text="Generate",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=35,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._on_generate
        )
        generate_btn.grid(row=2, column=1, padx=10, pady=10, sticky="e")
        
        # Preview frame (center)
        preview_frame = ctk.CTkFrame(self.frame)
        preview_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # Preview canvas
        self.canvas = tk.Canvas(
            preview_frame,
            bg="#2B2B2B" if ctk.get_appearance_mode() == "dark" else "#EBEBEB",
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Action buttons frame (bottom)
        action_frame = ctk.CTkFrame(self.frame)
        action_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            action_frame,
            text="Enter a prompt and click Generate",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=10)
    
    def show(self):
        """Show this tab."""
        self.frame.grid(row=0, column=0, sticky="nsew")
    
    def hide(self):
        """Hide this tab."""
        self.frame.grid_forget()
    
    def _on_generate(self):
        """Handle generate button click."""
        prompt = self.prompt_var.get().strip()
        if not prompt:
            self.main_window.show_error("Error", "Please enter a prompt")
            return
        
        # Disable UI during generation
        self._set_ui_state(False)
        self.status_label.configure(text="Generating image...")
        self.main_window.set_status("Generating image...")
        
        # Parse size
        size_str = self.size_var.get()
        width, height = map(int, size_str.split("x"))
        
        # Get negative prompt if any
        negative_prompt = self.neg_prompt_var.get().strip() or None
        
        # Start generation in a separate thread to keep UI responsive
        thread = threading.Thread(
            target=self._generate_image_thread,
            args=(prompt, (width, height), negative_prompt)
        )
        thread.daemon = True
        thread.start()
    
    def _generate_image_thread(self, prompt, size, negative_prompt=None):
        """Generate image in a background thread."""
        try:
            # Generate the image
            image = self.api_client.generate_image(prompt, size, negative_prompt)
            
            if image:
                # Save to temp location
                save_dir = ensure_dirs()
                self.generated_path = self.api_client.save_image(image, save_dir, prompt)
                self.generated_image = image
                
                # Save to database
                self.db.add_image(
                    prompt=prompt,
                    filename=Path(self.generated_path).name,
                    filepath=self.generated_path,
                    provider=self.api_client.provider,
                    width=image.width,
                    height=image.height
                )
                
                # Update UI in main thread
                self.frame.after(0, lambda: self._update_preview(image))
                self.frame.after(0, lambda: self._set_ui_state(True))
                self.frame.after(0, lambda: self.status_label.configure(text="Image generated successfully"))
                self.frame.after(0, lambda: self.main_window.set_status("Image generated successfully"))
            else:
                # Handle failure
                self.frame.after(0, lambda: self._set_ui_state(True))
                self.frame.after(0, lambda: self.status_label.configure(text="Failed to generate image"))
                self.frame.after(0, lambda: self.main_window.set_status("Failed to generate image"))
                self.frame.after(0, lambda: self.main_window.show_error("Error", "Failed to generate image"))
        except Exception as e:
            logger.exception("Error generating image")
            # Handle exception
            error_msg = str(e)
            self.frame.after(0, lambda: self._set_ui_state(True))
            self.frame.after(0, lambda: self.status_label.configure(text=f"Error: {error_msg[:50]}..."))
            self.frame.after(0, lambda: self.main_window.set_status(f"Error: {error_msg[:50]}..."))
            self.frame.after(0, lambda: self.main_window.show_error("Error", error_msg))
    
    def _update_preview(self, image):
        """Update the preview with the generated image."""
        # Clear canvas
        self.canvas.delete("all")
        
        # Resize for preview (maintaining aspect ratio)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # If canvas is not ready yet, use default size
        if canvas_width < 50 or canvas_height < 50:
            canvas_width = 500
            canvas_height = 500
        
        # Calculate scaling factor
        img_width, img_height = image.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        
        new_width = int(img_width * scale * 0.9)  # 90% of available space
        new_height = int(img_height * scale * 0.9)
        
        # Resize image for display
        display_img = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to PhotoImage
        self.preview_image = ImageTk.PhotoImage(display_img)
        
        # Calculate center position
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        
        # Display on canvas
        self.canvas.create_image(x, y, anchor="nw", image=self.preview_image)
    
    def _set_ui_state(self, enabled):
        """Enable or disable UI elements during generation."""
        state = "normal" if enabled else "disabled"
        self.prompt_entry.configure(state=state)
        self.neg_prompt_entry.configure(state=state)
        self.size_dropdown.configure(state=state)
    
    def _get_size_options_for_provider(self, provider):
        """Return appropriate size options based on the provider."""
        provider = provider.lower()
        
        if provider == "openai":
            return [
                "256x256", "512x512", "1024x1024",
                "1024x1792", "1792x1024"
            ]
        elif provider == "stability":
            # Updated to only use supported dimensions for SDXL model
            return [
                "1024x1024", "1152x896", "896x1152",
                "1216x832", "832x1216", "1344x768", "768x1344",
                "1536x640", "640x1536"
            ]
        elif provider == "gemini":
            return ["1024x1024", "1024x1792", "1792x1024"]
        else:
            # Default options
            return ["512x512", "768x768", "1024x1024"]
    
    def update_size_options(self, provider):
        """Update the size dropdown based on the selected provider."""
        new_options = self._get_size_options_for_provider(provider)
        
        # Update dropdown values
        self.size_dropdown.configure(values=new_options)
        
        # Set to first option if current selection is not valid
        if self.size_var.get() not in new_options:
            self.size_var.set(new_options[0]) 