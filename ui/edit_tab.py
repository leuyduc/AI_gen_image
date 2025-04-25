import logging
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
import os
from datetime import datetime
from typing import Optional, Tuple
import uuid

from core.image_editor import ImageEditor
from core.db import Database
from core.settings import ensure_dirs

logger = logging.getLogger(__name__)

class EditTab:
    """Tab for editing images with crop, rotate, and flip functionality."""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.db = Database()
        
        self.frame = None
        self.canvas = None
        self.current_image = None
        self.display_image = None
        self.tk_image = None
        self.original_image = None
        self.edit_history = []
        self.history_index = -1
        
        # Crop variables
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_rect = None
        self.is_cropping = False
        self.crop_preview = None
        
        # Image position
        self.image_pos = (0, 0)
        self.image_size = (0, 0)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI elements for the edit tab."""
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        
        # Top toolbar
        toolbar = ctk.CTkFrame(self.frame)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Load image button
        self.load_btn = ctk.CTkButton(
            toolbar,
            text="Load Image",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._on_load_image
        )
        self.load_btn.pack(side="left", padx=5)
        
        # Button separator
        ctk.CTkLabel(toolbar, text="│").pack(side="left", padx=10)
        
        # Crop button
        self.crop_btn = ctk.CTkButton(
            toolbar,
            text="Start Crop",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._toggle_crop_mode,
            state="disabled"
        )
        self.crop_btn.pack(side="left", padx=5)
        
        # Apply crop button
        self.apply_crop_btn = ctk.CTkButton(
            toolbar,
            text="Apply Crop",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._apply_crop,
            state="disabled"
        )
        self.apply_crop_btn.pack(side="left", padx=5)
        
        # Button separator
        ctk.CTkLabel(toolbar, text="│").pack(side="left", padx=10)
        
        # Rotate buttons
        self.rotate_left_btn = ctk.CTkButton(
            toolbar,
            text="Rotate Left",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=lambda: self._rotate_image(-90),
            state="disabled"
        )
        self.rotate_left_btn.pack(side="left", padx=5)
        
        self.rotate_right_btn = ctk.CTkButton(
            toolbar,
            text="Rotate Right",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=lambda: self._rotate_image(90),
            state="disabled"
        )
        self.rotate_right_btn.pack(side="left", padx=5)
        
        # Button separator
        ctk.CTkLabel(toolbar, text="│").pack(side="left", padx=10)
        
        # Flip buttons
        self.flip_h_btn = ctk.CTkButton(
            toolbar,
            text="Flip Horizontal",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._flip_horizontal,
            state="disabled"
        )
        self.flip_h_btn.pack(side="left", padx=5)
        
        self.flip_v_btn = ctk.CTkButton(
            toolbar,
            text="Flip Vertical",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._flip_vertical,
            state="disabled"
        )
        self.flip_v_btn.pack(side="left", padx=5)
        
        # Canvas frame (center)
        canvas_frame = ctk.CTkFrame(self.frame)
        canvas_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas for image display
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#2B2B2B",
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Canvas event bindings
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        
        # Bottom toolbar with history controls and save
        bottom_toolbar = ctk.CTkFrame(self.frame)
        bottom_toolbar.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Undo/Redo buttons
        self.undo_btn = ctk.CTkButton(
            bottom_toolbar,
            text="Undo",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._undo,
            state="disabled"
        )
        self.undo_btn.pack(side="left", padx=5)
        
        self.redo_btn = ctk.CTkButton(
            bottom_toolbar,
            text="Redo",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._redo,
            state="disabled"
        )
        self.redo_btn.pack(side="left", padx=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            bottom_toolbar,
            text="Load an image to begin editing",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=20)
        
        # Save button
        self.save_btn = ctk.CTkButton(
            bottom_toolbar,
            text="Save Image",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=120,
            height=30,
            fg_color=["#3B8ED0", "#1F6AA5"],
            hover_color=["#36719F", "#144870"],
            command=self._save_image,
            state="disabled"
        )
        self.save_btn.pack(side="right", padx=5)
    
    def _on_load_image(self):
        """Handle load image button click."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Load the image
            image = Image.open(file_path)
            
            # Store original
            self.original_image = image.copy()
            self.current_image = image.copy()
            
            # Reset history
            self.edit_history = [self.current_image.copy()]
            self.history_index = 0
            
            # Display the image
            self._update_display()
            
            # Update UI state
            self._update_button_states()
            self.status_label.configure(text=f"Loaded image: {os.path.basename(file_path)}")
            self.main_window.set_status(f"Loaded: {os.path.basename(file_path)}")
            
        except Exception as e:
            logger.exception("Error loading image")
            self.main_window.show_error("Error", f"Failed to load image: {str(e)}")
    
    def _update_display(self):
        """Update the canvas with the current image."""
        if self.current_image is None:
            return
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Use default dimensions if canvas is not ready
        if canvas_width < 50 or canvas_height < 50:
            canvas_width = 800
            canvas_height = 600
        
        # Calculate scaling factor to fit image in canvas
        img_width, img_height = self.current_image.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        
        # Scale down to 90% of available space
        new_width = int(img_width * scale * 0.9)
        new_height = int(img_height * scale * 0.9)
        
        # Resize image for display
        self.display_image = self.current_image.resize((new_width, new_height), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        
        # Calculate center position
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        
        # Store image position and size for crop calculations
        self.image_pos = (x, y)
        self.image_size = (new_width, new_height)
        
        # Display on canvas
        self.canvas.create_image(x, y, anchor="nw", image=self.tk_image, tags="image")
    
    def _update_button_states(self):
        """Update button states based on current state."""
        has_image = self.current_image is not None
        state = "normal" if has_image else "disabled"
        
        self.crop_btn.configure(state=state)
        self.rotate_left_btn.configure(state=state)
        self.rotate_right_btn.configure(state=state)
        self.flip_h_btn.configure(state=state)
        self.flip_v_btn.configure(state=state)
        self.save_btn.configure(state=state)
        
        # Apply crop button is enabled only in crop mode
        self.apply_crop_btn.configure(state="disabled")
        
        # Undo/Redo buttons
        self.undo_btn.configure(state="normal" if self.history_index > 0 else "disabled")
        self.redo_btn.configure(state="normal" if self.history_index < len(self.edit_history) - 1 else "disabled")
    
    def _toggle_crop_mode(self):
        """Toggle crop mode on/off."""
        if not self.is_cropping:
            self.is_cropping = True
            self.crop_btn.configure(text="Cancel Crop")
            self.status_label.configure(text="Click and drag to select crop area")
        else:
            self.is_cropping = False
            self.crop_btn.configure(text="Start Crop")
            self.status_label.configure(text="Crop cancelled")
            
            # Remove crop rectangle if exists
            if self.crop_rect:
                self.canvas.delete(self.crop_rect)
                self.crop_rect = None
    
    def _on_canvas_press(self, event):
        """Handle mouse button press on canvas."""
        if not self.is_cropping or self.current_image is None:
            return
        
        # Get coordinates relative to image
        x, y = event.x, event.y
        img_x, img_y = self.image_pos
        img_w, img_h = self.image_size
        
        # Check if click is inside image
        if (img_x <= x <= img_x + img_w and img_y <= y <= img_y + img_h):
            self.crop_start_x = x
            self.crop_start_y = y
            
            # Create initial rectangle
            self.crop_rect = self.canvas.create_rectangle(
                x, y, x, y,
                outline="red",
                width=2,
                tags="crop"
            )
    
    def _on_canvas_drag(self, event):
        """Handle mouse drag on canvas."""
        if not self.is_cropping or self.crop_start_x is None or self.crop_rect is None:
            return
        
        # Update rectangle
        x, y = event.x, event.y
        img_x, img_y = self.image_pos
        img_w, img_h = self.image_size
        
        # Constrain to image boundaries
        x = max(img_x, min(x, img_x + img_w))
        y = max(img_y, min(y, img_y + img_h))
        
        self.canvas.coords(self.crop_rect, self.crop_start_x, self.crop_start_y, x, y)
        
        # Enable apply button when we have a selection
        self.apply_crop_btn.configure(state="normal")
    
    def _on_canvas_release(self, event):
        """Handle mouse button release on canvas."""
        if not self.is_cropping or self.crop_start_x is None or self.crop_rect is None:
            return
        
        # Finalize rectangle
        x, y = event.x, event.y
        img_x, img_y = self.image_pos
        img_w, img_h = self.image_size
        
        # Constrain to image boundaries
        x = max(img_x, min(x, img_x + img_w))
        y = max(img_y, min(y, img_y + img_h))
        
        self.canvas.coords(self.crop_rect, self.crop_start_x, self.crop_start_y, x, y)
        
        # Enable apply button only if we have a meaningful selection
        if abs(x - self.crop_start_x) > 10 and abs(y - self.crop_start_y) > 10:
            self.apply_crop_btn.configure(state="normal")
        else:
            self.canvas.delete(self.crop_rect)
            self.crop_rect = None
            self.apply_crop_btn.configure(state="disabled")
    
    def _apply_crop(self):
        """Apply crop to the current image."""
        if self.crop_rect is None or self.current_image is None:
            return
        
        # Get crop rectangle coordinates
        coords = self.canvas.coords(self.crop_rect)
        if len(coords) != 4:
            return
        
        # Convert from canvas coordinates to image coordinates
        x1, y1, x2, y2 = coords
        img_x, img_y = self.image_pos
        img_w, img_h = self.image_size
        
        # Ensure correct ordering (top-left to bottom-right)
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        
        # Convert to image scale
        orig_w, orig_h = self.current_image.size
        scale_x = orig_w / img_w
        scale_y = orig_h / img_h
        
        crop_left = int((left - img_x) * scale_x)
        crop_top = int((top - img_y) * scale_y)
        crop_right = int((right - img_x) * scale_x)
        crop_bottom = int((bottom - img_y) * scale_y)
        
        # Apply crop
        try:
            # Use our image editor to crop
            cropped_image = ImageEditor.crop_image(
                self.current_image, 
                (crop_left, crop_top, crop_right, crop_bottom)
            )
            
            # If the crop was successful (image dimensions changed)
            if cropped_image.size != self.current_image.size:
                # Add to history
                self._add_to_history(cropped_image)
                
                # Update display
                self._update_display()
                self.status_label.configure(text="Image cropped successfully")
                self.main_window.set_status("Image cropped")
            else:
                self.status_label.configure(text="Crop failed - invalid selection")
            
        except Exception as e:
            logger.exception("Error applying crop")
            self.main_window.show_error("Error", f"Failed to crop image: {str(e)}")
        
        # Exit crop mode
        self.is_cropping = False
        self.crop_btn.configure(text="Start Crop")
        self.canvas.delete(self.crop_rect)
        self.crop_rect = None
        self.crop_start_x = None
        self.crop_start_y = None
        self.apply_crop_btn.configure(state="disabled")
        
        # Update button states
        self._update_button_states()
    
    def _rotate_image(self, angle):
        """Rotate the image by the specified angle."""
        if self.current_image is None:
            return
        
        try:
            # Use our image editor to rotate
            rotated_image = ImageEditor.rotate_image(self.current_image, angle)
            
            # Add to history
            self._add_to_history(rotated_image)
            
            # Update display
            self._update_display()
            self.status_label.configure(text=f"Image rotated {abs(angle)}° {'counter-clockwise' if angle > 0 else 'clockwise'}")
            self.main_window.set_status(f"Image rotated {abs(angle)}°")
            
        except Exception as e:
            logger.exception("Error rotating image")
            self.main_window.show_error("Error", f"Failed to rotate image: {str(e)}")
    
    def _flip_horizontal(self):
        """Flip the image horizontally."""
        if self.current_image is None:
            return
        
        try:
            # Use our image editor to flip
            flipped_image = ImageEditor.flip_image_horizontal(self.current_image)
            
            # Add to history
            self._add_to_history(flipped_image)
            
            # Update display
            self._update_display()
            self.status_label.configure(text="Image flipped horizontally")
            self.main_window.set_status("Image flipped horizontally")
            
        except Exception as e:
            logger.exception("Error flipping image")
            self.main_window.show_error("Error", f"Failed to flip image: {str(e)}")
    
    def _flip_vertical(self):
        """Flip the image vertically."""
        if self.current_image is None:
            return
        
        try:
            # Use our image editor to flip
            flipped_image = ImageEditor.flip_image_vertical(self.current_image)
            
            # Add to history
            self._add_to_history(flipped_image)
            
            # Update display
            self._update_display()
            self.status_label.configure(text="Image flipped vertically")
            self.main_window.set_status("Image flipped vertically")
            
        except Exception as e:
            logger.exception("Error flipping image")
            self.main_window.show_error("Error", f"Failed to flip image: {str(e)}")
    
    def _add_to_history(self, image):
        """Add a new state to edit history."""
        # Truncate history if we're not at the end
        if self.history_index < len(self.edit_history) - 1:
            self.edit_history = self.edit_history[:self.history_index + 1]
        
        # Add new state and update index
        self.edit_history.append(image)
        self.history_index = len(self.edit_history) - 1
        
        # Update current image
        self.current_image = image
        
        # Update button states
        self._update_button_states()
    
    def _undo(self):
        """Undo the last edit."""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_image = self.edit_history[self.history_index]
            self._update_display()
            self._update_button_states()
            self.status_label.configure(text="Undo successful")
            self.main_window.set_status("Undo")
    
    def _redo(self):
        """Redo the last undone edit."""
        if self.history_index < len(self.edit_history) - 1:
            self.history_index += 1
            self.current_image = self.edit_history[self.history_index]
            self._update_display()
            self._update_button_states()
            self.status_label.configure(text="Redo successful")
            self.main_window.set_status("Redo")
    
    def _save_image(self):
        """Save the edited image."""
        if self.current_image is None:
            return
        
        try:
            # Generate save path
            save_dir = ensure_dirs()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"edited_{timestamp}_{uuid.uuid4().hex[:8]}.png"
            save_path = os.path.join(save_dir, filename)
            
            # Save the image
            self.current_image.save(save_path)
            
            # Add to database
            self.db.add_image(
                prompt="Edited image",
                filename=filename,
                filepath=save_path,
                provider="Local Edit",
                width=self.current_image.width,
                height=self.current_image.height
            )
            
            self.status_label.configure(text=f"Image saved: {filename}")
            self.main_window.set_status(f"Saved: {filename}")
            self.main_window.show_info("Success", f"Image saved successfully to:\n{save_path}")
            
            # Update history tab if it exists
            self.main_window.update_history()
            
        except Exception as e:
            logger.exception("Error saving image")
            self.main_window.show_error("Error", f"Failed to save image: {str(e)}")
    
    def show(self):
        """Show this tab."""
        self.frame.grid(row=0, column=0, sticky="nsew")
        # Update display if needed (e.g., window resize happened while tab was hidden)
        if self.current_image is not None:
            self._update_display()
    
    def hide(self):
        """Hide this tab."""
        self.frame.grid_forget() 