import os
import threading
import zipfile
import json
import random
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
import customtkinter as ctk
import requests
from time import sleep
from tkinter import ttk  # Import ttk module for the Notebook
import queue

# Constants
SKETCHFAB_API_URL = 'https://api.sketchfab.com/v3'
API_TOKEN = ''  # Replace with your actual API token

# Helper functions
def get_request_payload(api_key, data=None, files=None, json_payload=False):
    """
    Prepare the request payload for Sketchfab API requests.
    """
    headers = {'Authorization': f'Token {api_key}'}
    if json_payload:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    return {'data': data, 'files': files, 'headers': headers}

def fetch_sketchfab_data(api_key, endpoint):
    """
    Fetch data from a specified Sketchfab API endpoint.
    """
    headers = {'Authorization': f'Token {api_key}'}
    response = requests.get(f"{SKETCHFAB_API_URL}/{endpoint}", headers=headers)
    return response.json() if response.status_code == 200 else None

class UploadApp(TkinterDnD.Tk):
    """
    A Tkinter application for uploading 3D models to Sketchfab.
    """
    def __init__(self):
        super().__init__()
        self.title("Sketchfab Model Uploader")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.9)
        self.upload_semaphore = threading.Semaphore(6)
        self.patch_semaphore = threading.Semaphore(6)
        
        self.style = ttk.Style()
        self.style.theme_use("default")  # Using the default theme as a base
        self.upload_queue = queue.Queue() 
        # Create a new style for the Treeview that includes borders
        self.style.configure("Custom.Treeview", 
                             background="white",
                             foreground="black",
                             rowheight=25,
                             fieldbackground="white",
                             borderwidth=2,
                             relief="solid")  # Borders around each cell
        
        # Treeview Heading Style
        self.style.configure("Custom.Treeview.Heading",
                             font=('Calibri', 10, 'bold'),  # You can change the font to any that you prefer
                             background="lightgrey",
                             foreground="black",
                             relief="raised")  # Raised relief adds a 3D effect to the headings

        self.style.layout("Custom.Treeview", [('Custom.Treeview.treearea', {'sticky': 'nswe'})])  # Remove borders from the layout, only borders around cells
        
        self.folder_paths = []
        self.status_trees = {}
        self.upload_mode = ctk.IntVar(value=1)
        self.description = ctk.StringVar()
        self.tags = ctk.StringVar()
        self.private = ctk.IntVar(value=0)
        self.password = ctk.StringVar()
        self.isPublished = ctk.IntVar(value=0)
        self.isInspectable = ctk.IntVar(value=1)
        self.price = ctk.StringVar(value="")
        self.categories = []
        self.category_map1 = {}
        self.category_map2 = {}
        self.category1 = ctk.StringVar()
        self.category2 = ctk.StringVar()
        self.licenses = []
        self.api_key = ctk.StringVar()
        self.notebook = ttk.Notebook(self)  # Define notebook here
        self.notebook.pack(fill='both', expand=True)  # Pack it once
        self.thread_status = {}
        self.original_license = None

        self.fetch_data()
        self.create_widgets()
        self.configure_grid()
        self.state('zoomed')

    def fetch_data(self):
        """
        Fetch categories and licenses from Sketchfab API.
        """
        category_data = fetch_sketchfab_data(API_TOKEN, 'categories')['results']
        self.categories = [""] + [category['name'] for category in category_data]  # Include empty option at the start
        self.category_map1 = {category['name']: category['slug'] for category in category_data}
        self.category_map2 = self.category_map1.copy()
        self.licenses = [license['fullName'] for license in fetch_sketchfab_data(API_TOKEN, 'licenses')['results']]
        self.license_map = {license['fullName']: license['slug'] for license in fetch_sketchfab_data(API_TOKEN, 'licenses')['results']}

    def create_widgets(self):
        """
        Create the widgets for the application.
        """
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)

        # Create two tabs
        tab1 = ctk.CTkFrame(self.notebook)
        tab2 = ctk.CTkFrame(self.notebook)
        self.notebook.add(tab1, text='Uploads')

        self.setup_tab1(tab1)

    def setup_tab1(self, parent):
        """
        Setup the first tab for uploads.
        """
        # Configure the grid system of the parent to allow centering
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_rowconfigure(3, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Top frame for mode selection and file browsing
        top_frame = ctk.CTkFrame(parent)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        api_key_label = ctk.CTkLabel(top_frame, text="Sketchfab API Key:")
        api_key_label.grid(row=0, column=1, padx=10, pady=10)

        api_key_entry = ctk.CTkEntry(top_frame, textvariable=self.api_key, width=400)
        api_key_entry.grid(row=0, column=2, padx=10, pady=10)
        
        mode_label = ctk.CTkLabel(top_frame, text="Select Upload Mode:")
        mode_label.grid(row=1, column=0, padx=10, pady=10)

        single_folder_rb = ctk.CTkRadioButton(top_frame, text="Single Folder", variable=self.upload_mode, value=1, command=self.update_browse)
        single_folder_rb.grid(row=1, column=1, padx=10)

        multiple_folders_rb = ctk.CTkRadioButton(top_frame, text="Multiple Folders", variable=self.upload_mode, value=2, command=self.update_browse)
        multiple_folders_rb.grid(row=1, column=2, padx=10)

        browse_button = ctk.CTkButton(top_frame, text="Browse", command=self.delayed_browse_file)
        browse_button.grid(row=1, column=3, padx=10)

        self.file_entry = ctk.CTkEntry(top_frame, width=400)
        self.file_entry.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        # Drag and drop area
        drop_frame = ctk.CTkFrame(parent, height=100, fg_color="gray")
        drop_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        drop_frame.pack_propagate(False)

        drop_label = ctk.CTkLabel(drop_frame, text="Drag and Drop Folders Here")
        drop_label.pack(expand=True, fill="both")
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.on_drop)

        # Metadata input area
        metadata_frame = ctk.CTkFrame(parent)
        metadata_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        ctk.CTkLabel(metadata_frame, text="Description:").grid(row=0, column=0, sticky="e")
        description_text = ctk.CTkTextbox(metadata_frame, height=120, width=500)
        description_text.grid(row=0, column=1, sticky="ew", columnspan=3)
        self.description_textbox = description_text
        self.description_textbox.configure(padx=4, pady=4)

        ctk.CTkLabel(metadata_frame, text="Tags (new-line-separated):").grid(row=1, column=0, sticky="e")
        self.tags_textbox = ctk.CTkTextbox(metadata_frame, height=90, width=500)
        self.tags_textbox.grid(row=1, column=1, sticky="ew", columnspan=3)

        ctk.CTkLabel(metadata_frame, text="Category 1").grid(row=2, column=0, sticky="e")
        self.category1_combobox = ctk.CTkComboBox(metadata_frame, values=self.categories, command=lambda value: self.update_category1(value))
        self.category1_combobox.grid(row=2, column=1, sticky="ew")

        ctk.CTkLabel(metadata_frame, text="Category 2").grid(row=3, column=0, sticky="e")
        # Category 2 ComboBox
        self.category2_combobox = ctk.CTkComboBox(metadata_frame, values=self.categories, command=lambda value: self.update_category2(value))
        self.category2_combobox.grid(row=3, column=1, sticky="ew")

        ctk.CTkLabel(metadata_frame, text="License:").grid(row=4, column=0, sticky="e")
        self.license_combobox = ctk.CTkComboBox(metadata_frame, values=self.licenses, command=self.toggle_price_field)
        self.license_combobox.grid(row=4, column=1, sticky="ew")

        ctk.CTkLabel(metadata_frame, text="Price (if required):").grid(row=4, column=2, sticky="e")
        self.price_entry = ctk.CTkEntry(metadata_frame, textvariable=self.price)
        self.price_entry.grid(row=4, column=4, sticky="ew")
        self.price_entry.grid_remove()  # Initially hide the price entry field

        ctk.CTkLabel(metadata_frame, text="Private:").grid(row=6, column=0, sticky="e")
        private_checkbox = ctk.CTkCheckBox(metadata_frame, variable=self.private, command=self.toggle_password_field)
        private_checkbox.grid(row=6, column=1)

        ctk.CTkLabel(metadata_frame, text="Password (if private):").grid(row=6, column=2, sticky="e")
        self.password_entry = ctk.CTkEntry(metadata_frame, textvariable=self.password)
        self.password_entry.grid(row=6, column=4, sticky="ew")

        # Initially hide the password entry if the private box is not checked
        self.password_entry.grid_remove()  # This hides the widget without losing its grid configuration

        ctk.CTkLabel(metadata_frame, text="Published:").grid(row=8, column=0, sticky="e")
        ctk.CTkCheckBox(metadata_frame, variable=self.isPublished).grid(row=8, column=1)

        ctk.CTkLabel(metadata_frame, text="Inspectable:").grid(row=9, column=0, sticky="e")
        ctk.CTkCheckBox(metadata_frame, variable=self.isInspectable).grid(row=9, column=1)

        # Upload button and status
        action_frame = ctk.CTkFrame(parent)
        action_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=20)

        upload_button = ctk.CTkButton(action_frame, text="Upload", command=self.start_upload_manager)
        upload_button.pack(side="left", padx=10, pady=10)

        reset_button = ctk.CTkButton(action_frame, text="Reset form", command=self.reset_form)
        reset_button.pack(side="left", padx=10, pady=10)

        # Larger status field
        self.status_text = ctk.CTkTextbox(action_frame, height=100, width=100)  # Adjusted size
        self.status_text.pack(side="left", padx=10, pady=10, fill="both", expand=True)

    def setup_tab2(self, parent):
        """
        Setup the second tab for status tracking.
        """
        # Configure the grid system of the parent to allow centering
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Create the Treeview widget
        self.tree = ttk.Treeview(parent, columns=('Model Name', 'Upload Status', 'Processing Status', 'Patch Status', 'Batch Status'), show='headings')
        self.setup_treeview_tags()
        
        # Set the column headings
        self.tree.heading('Model Name', text='Model Name')
        self.tree.heading('Status', text='Upload Status')
        self.tree.heading('Progress', text='Processing Status')
        self.tree.heading('Batch Status', text='Batch Status')

        # Set the column widths and alignment
        self.tree.column('Model Name', width=200, anchor='center')
        self.tree.column('Status', width=150, anchor='center')
        self.tree.column('Progress', width=150, anchor='center')
        self.tree.column('Batch Status', width=150, anchor='center')

        # Grid the Treeview widget with centering options
        self.tree.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        # Configuring the scroll bar
        scroll = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scroll.set)

    def update_category1(self, selected_category):
        """
        Update the category1 variable based on the selected category.
        """
        # Logic to update category1 based on selected_category
        # For example, setting a class variable or updating UI components
        self.category1.set(self.category_map1.get(selected_category, ''))

    def update_category2(self, selected_category):
        """
        Update the category2 variable based on the selected category.
        """
        # Similar logic for category2
        self.category2.set(self.category_map2.get(selected_category, ''))
    
    def setup_treeview_tags(self):
        """
        Configure tags for the Treeview.
        """
        self.tree.tag_configure('Upload Failed', background='#ffcccc')  # light red
        self.tree.tag_configure('Failed', background='#ffcccc')  # light red
        self.tree.tag_configure('processing_failed', background='#ff6666')  # darker red
        self.tree.tag_configure('patch_failed', background='#990000')  # even darker red, near maroon
        self.tree.tag_configure('normal', background='#ffffff')
    
    def update_tree_view(self, model_name, status, progress, tab_name, patch_status, batch_status):
        """
        Update the Treeview with new status information.
        """
        tree = self.status_trees.get(tab_name)
        if tree:
            for item in tree.get_children():
                if tree.item(item, 'values')[0] == model_name:
                    # Determine the appropriate tag based on status or patch status
                    if status == 'Upload Failed':
                        tag = 'error'
                    elif patch_status == 'Patch Failed':
                        tag = 'patch_failed'
                    else:
                        tag = 'normal'

                    # Update the item with the determined tag
                    tree.item(item, values=(model_name, status, progress, patch_status, batch_status), tags=(tag,))
                    return

            # Insert new item with the appropriate tag
            if status == 'Upload Failed':
                tag = 'error'
            elif patch_status == 'Patch Failed':
                tag = 'patch_failed'
            else:
                tag = 'normal'

            tree.insert('', 'end', values=(model_name, status, progress, patch_status, batch_status), tags=(tag,))

        # Configure tags and their associated background colors
        tree.tag_configure('error', background='#ffcccc')  # light red for upload failures
        tree.tag_configure('patch_failed', background='#FFA500')  # orange for patch failures
        tree.tag_configure('normal', background='#ffffff')
    
    def determine_tag(self, status, patch_status):
        """
        Determine the appropriate tag based on status and patch status.
        """
        if 'Failed' in status:
            return 'upload_failed'
        elif 'Failed' in patch_status:
            return 'patch_failed'
        elif 'Aborted' in status or 'Aborted' in patch_status:
            return 'processing_failed'
        else:
            return 'normal'
    
    def update_status(self, message):
        """
        Update the GUI status text in a thread-safe manner.
        """
        """ Update the GUI status text in a thread-safe manner. """
        if self.status_text:  # Ensure the textbox is available
            self.status_text.delete(1.0, ctk.END)
            self.status_text.insert(ctk.END, message)
    
    def toggle_price_field(self, selected_license):
        """
        Toggle the visibility of the price entry field based on the selected license.
        """
        # Use the selected_license directly passed to the method
        if selected_license in ["Standard", "Editorial"]:  # Adjust these strings as needed
            self.price_entry.grid()  # Show the price entry field
        else:
            self.price_entry.grid_remove()  # Hide the price entry field
    
    def toggle_password_field(self):
        """
        Toggle the visibility of the password entry field based on the private checkbox.
        """
        if self.private.get() == 1:  # If the private checkbox is checked
            self.password_entry.grid()  # Show the password entry field
        else:
            self.password_entry.grid_remove()  # Hide the password entry field
            
    def check_and_update_status(self):
        """
        Check and update the status periodically.
        """
        # Check if updates are needed
        # Update GUI accordingly
        self.after(1000, self.check_and_update_status)  # Check every second

    def start(self):
        """
        Start the main application loop.
        """
        self.check_and_update_status()
        self.mainloop()
        
    def configure_grid(self):
        """
        Configure the grid layout for the main window.
        """
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Give more weight to metadata frame
        self.grid_rowconfigure(3, weight=2)  # Give more weight to action frame to allow larger status
        self.grid_columnconfigure(0, weight=1)

    def update_browse(self):
        """
        Clear the browse field based on the upload mode.
        """
        self.file_entry.delete(0, ctk.END)
        self.folder_paths = []

    def delayed_browse_file(self):
        """
        Delay the browse file dialog to allow for smoother UI transitions.
        """
        self.after(300, self.browse_file)

    def browse_file(self):
        """
        Open a file dialog to select a main folder, find all relevant subfolders, and append them to existing paths.
        """
        folder_path = filedialog.askdirectory()  # Ask user to select the main folder
        if folder_path:
            # Capture the main folder name for the status tab title
            main_folder_name = os.path.basename(os.path.normpath(folder_path))
            
            new_subfolders = self.find_subfolders_with_models(folder_path)
            
            # Depending on the upload mode, append new folders or reset the list
            if self.upload_mode.get() == 2:  # Multiple folders mode
                self.folder_paths.extend(new_subfolders)  # Append new subfolders
            else:
                self.folder_paths = new_subfolders  # Single folder mode, replace existing list
            
            self.display_browse_paths()
            
            # Store main folder name in instance for later use in creating status tab
            self.current_main_folder_name = main_folder_name

    def display_browse_paths(self):
        """
        Display the main folders in the browse field.
        """
        if self.upload_mode.get() == 2:  # Multiple folders mode
            main_folders = set(os.path.dirname(path) for path in self.folder_paths)  # Extract main folder paths from subfolders
            display_paths = "; ".join(main_folders)
        else:
            display_paths = "; ".join(set(os.path.dirname(path) for path in self.folder_paths))
        
        self.file_entry.delete(0, ctk.END)
        self.file_entry.insert(0, display_paths)  # Display the main folder paths

    def update_browse(self):
        """
        Clear the browse field based on upload mode or prepare for a new selection.
        """
        if self.upload_mode.get() == 2:  # Multiple folders mode
            self.file_entry.delete(0, ctk.END)
            self.folder_paths = [] 
        else:
            self.file_entry.delete(0, ctk.END)
            self.folder_paths = [] 
    
    def find_subfolders_with_models(self, main_folder):
        """
        Find all subfolders containing model files within the selected main folder.
        """
        subfolders = []
        for root, dirs, files in os.walk(main_folder):
            if any(file.endswith(('.zip', '.glb')) for file in files):  # Checking for model files
                subfolders.append(root)
        return subfolders

    def find_subfolders_with_files(self, main_folder):
        """
        Find subfolders with specific file types within a main folder.
        """
        subfolders = []
        for root, dirs, files in os.walk(main_folder):
            for file in files:
                if file.endswith(('.zip', '.glb')):  # Add other file types if necessary
                    subfolders.append(root)
                    break  # Only add each subfolder once
        return list(set(subfolders))  # Remove duplicates if any

    def on_drop(self, event):
        """
        Handle multiple folders dropped onto the application.
        """
        dropped_folders = self.tk.splitlist(event.data)
        model_folders = []
        main_folder_names = []

        for top_folder in dropped_folders:
            if os.path.isdir(top_folder):
                # Find all subfolders with models within each top-level folder
                subfolders = self.find_subfolders_with_models(top_folder)
                model_folders.extend(subfolders)  # Add all found subfolders to the list
                # Collect the main folder names for status tab naming
                main_folder_names.append(os.path.basename(top_folder))

        self.folder_paths.extend(model_folders)  # Update the main list with all found subfolders
        self.file_entry.delete(0, ctk.END)
        
        # Create a semicolon-separated list of main folder names for display
        display_names = "; ".join(main_folder_names)
        self.file_entry.insert(0, display_names)

        # Use the collected main folder names for other parts of the GUI, such as status tabs
        self.current_main_folder_name = display_names
    
    def start_upload_manager(self):
        """
        Start the upload manager in a separate thread.
        """
        threading.Thread(target=self.upload, daemon=True).start()
        self.update_status(f"Preparing to upload {len(self.folder_paths)} models...")

    def upload(self):
        """
        Manage the upload process by creating threads for each folder.
        """
        threads = []
        thread_id = 0
        base_delay = 2  # Base delay in seconds
        max_delay = 60  # Maximum delay in seconds
        current_delay = base_delay
        total_models = len(self.folder_paths)  # Total number of models to upload
        half_point = total_models // 2  # Determine the half point

        if not self.api_key.get():
            self.update_status("Please enter your Sketchfab API key.")
            return

        if self.folder_paths:
            self.create_status_tab(self.current_main_folder_name, len(self.folder_paths))

            while self.folder_paths:
                if len(self.folder_paths) == half_point:  # Check if we've reached the half point
                    self.update_status("Pausing for 2 minutes at half point...")
                    sleep(120)  # 2-minute pause
                while len(threads) < 6 and self.folder_paths:
                    folder_path = self.folder_paths.pop(0)
                    thread = threading.Thread(target=self.upload_folder, args=(folder_path, self.current_main_folder_name, thread_id))
                    threads.append(thread)
                    self.thread_status[thread_id] = 'starting'
                    thread.start()
                    thread_id += 1
                    sleep(2)
                
                threads = [t for t in threads if t.is_alive()]
                if any(self.thread_status[tid] == 429 for tid in self.thread_status):
                    current_delay = min(max_delay, current_delay * 2)  # Exponential backoff
                    sleep(5)
                else:
                    current_delay = max(base_delay, current_delay / 2)  # Decrease delay if no recent 429s
                    sleep(5)

                if not self.folder_paths and threads:  # Check before last model starts
                    self.update_status("Pausing for 2 minutes before the last model upload...")
                    sleep(180)  # 2-minute pause

            for t in threads:
                t.join()

            self.update_status("All uploads completed.")
        else:
            self.update_status("No folders selected for upload.")

        self.reset_browse_field()
        self.reset_form()
    
    def reset_browse_field(self):
        """
        Reset the browse field to be empty after uploading.
        """
        self.file_entry.delete(0, 'end')  # Clear the entry field
        self.folder_paths = []  # Clear the list of folder paths
    
    # Ensure when creating the Treeview, you specify the new style
    def create_status_tab(self, tab_name, model_count):
        """
        Create a tab with the given name for tracking upload status and show model count.
        """
        # Modify the tab title to show the count of models
        tab_label = f"{tab_name} - {model_count} Models"
        new_tab = ctk.CTkFrame(self.notebook)
        self.notebook.add(new_tab, text=tab_label)

        frame_for_treeview = ttk.Frame(new_tab)
        frame_for_treeview.pack(fill='both', expand=True)

        # Setup the Treeview with columns as before
        tree = ttk.Treeview(frame_for_treeview, columns=('Model Name', 'Status', 'Progress', 'Patch', 'Summary'), 
                            show='headings', style="Custom.Treeview")
        
        # Label for showing selection count
        self.selection_count_label = ctk.CTkLabel(frame_for_treeview, text="Selected Models: 0", text_color="black")
        self.selection_count_label.pack(side='top', fill='x')  # Ensure the label is at the top

        tree.bind("<<TreeviewSelect>>", self.on_selection_changed)
        tree.heading('Model Name', text='Model Name', anchor='center')
        tree.heading('Status', text='Upload Status', anchor='center')
        tree.heading('Progress', text='Processing Status', anchor='center')
        tree.heading('Patch', text='Patch Status', anchor='center')
        tree.heading('Summary', text='Summary')
        
        tree.column('Model Name', width=250, anchor='center')
        tree.column('Status', width=150, anchor='center')
        tree.column('Progress', width=150, anchor='center')
        tree.column('Patch', width=250, anchor='center')
        tree.column('Summary', width=150, anchor='center')

        tree.pack(fill='both', expand=True)
        scroll = ttk.Scrollbar(frame_for_treeview, orient="vertical", command=tree.yview)
        scroll.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scroll.set)
        self.status_trees[tab_name] = tree
    
    def on_selection_changed(self, event):
        """
        Update the selection count when the selection changes.
        """
        selected_items = event.widget.selection()
        selection_count = len(selected_items)
        self.display_selection_count(selection_count)
        
    def display_selection_count(self, count):
        """
        Display the count of selected models.
        """
        # Assuming there's a label in your GUI to display the count
        self.selection_count_label.configure(text=f"Selected Models: {count}")
    
    def reset_form(self):
        """
        Reset all inputs in the form, including browse field and any other UI elements.
        """
        # Reset the text fields
        description_textbox = self.description_textbox  # Assuming this is your variable name for the description CTkTextbox
        description_textbox.delete("1.0", ctk.END)
        self.tags_textbox.delete("1.0", ctk.END)  # For CTkTextbox
        self.price.set("")
        self.password.set("")

        # Reset the checkboxes
        self.private.set(0)
        self.isPublished.set(0)
        self.isInspectable.set(1)

        # Clear any status messages
        if self.status_text:
            self.status_text.delete(1.0, ctk.END)

        # Optionally, clear the file entry if needed
        self.file_entry.delete(0, ctk.END)
        self.folder_paths.clear()
        
    def upload_model(self, file_path, data):
        """
        Upload model to Sketchfab with an initial 'free-standard' license if required.
        """
        self.original_license = data.get('license')  # Save the original license
        if len(data['name']) > 48:
            data['name'] = data['name'][:48]  # Truncate to the maximum allowed length

        # Temporarily set license to 'free-st' for initial upload if it's 'st' or 'ed'
        if self.original_license in ['st', 'ed']:
            data['license'] = 'free-st'

        sleep(5)
        model_endpoint = f'{SKETCHFAB_API_URL}/models'
        headers = {'Authorization': f'Token {self.api_key.get()}'}
        try:
            with open(file_path, 'rb') as file:
                files = {'modelFile': (os.path.basename(file_path), file)}
                response = requests.post(model_endpoint, headers=headers, files=files, data=data)
                if response.status_code == requests.codes.created:
                    model_url = response.headers.get('Location')
                    model_uid = model_url.split('/')[-1]
                    # Restore the original license for return
                    data['license'] = self.original_license
                    return model_uid, model_url, 'success', self.original_license, None
                else:
                    return None, None, 'error', self.original_license, response.json().get('detail', 'Unknown error occurred')
        except Exception as e:
            return None, None, 'error', self.original_license, str(e)
    
    def clean_and_convert_price(self, input_price):
        """
        Converts a price input to the required whole number format by multiplying by 100.
        """
        if input_price is None:
            return None
        # Handle string input with commas as decimal separators
        if isinstance(input_price, str):
            input_price = input_price.replace(',', '.')  # Replace comma with dot for decimal
            try:
                price_float = float(input_price)
            except ValueError:
                return None
        elif isinstance(input_price, (int, float)):
            price_float = float(input_price)  # Ensure it's a float if not already
        else:
            return None

        # Convert to integer by multiplying by 100
        price_int = int(round(price_float * 100))
        if price_int < 399:  # Ensure the price meets the minimum required value
            return None
        return price_int
    
    def patch_model(self, uid, original_license, price):
        """
        Patch the model's license and price after initial upload.
        """
        with self.patch_semaphore:
            """Patch the model's license and price after initial upload."""
            # Added static delay to manage the rate of patch operations
            sleep(30)

            headers = {'Authorization': f'Token {self.api_key.get()}', 'Content-Type': 'application/json'}
            patch_data = {'license': self.original_license}

            if self.original_license in ['st', 'ed']:  # If the license type requires a price
                try:
                    price = self.clean_and_convert_price(price)
                    if price is None:
                        self.update_status(f"Invalid price for model {uid}. Patch aborted.")
                        return 'error'
                    patch_data['price'] = price
                except ValueError as e:
                    self.update_status(f"Price value error for model {uid}: {e}. Patch aborted.")
                    return 'error'

            patch_endpoint = f'{SKETCHFAB_API_URL}/models/{uid}'
            backoff_time = 20  # Start with a 10 second backoff time
            max_retries = 200  # Set a maximum number of retries to avoid infinite loops
            attempts = 0

            while attempts < max_retries:
                try:
                    response = requests.patch(patch_endpoint, headers=headers, data=json.dumps(patch_data))
                    if response.status_code in [200, 204]:
                        self.update_status(f"Model {uid} patched successfully.")
                        return 'success'
                    elif response.status_code == 429:  # Rate limit error
                        self.update_status(f"Rate limit hit while patching model {uid}. Retrying in {backoff_time} seconds.")
                        return 'error'
                    else:
                        self.update_status(f"Failed to patch model {uid}: {response.status_code} - {response.text}")
                        return 'error'
                except requests.RequestException as e:
                    self.update_status(f"Network error while patching model {uid}: {e}.")
                    return 'error'
                attempts += 1

            self.update_status(f"Max retries reached for model {uid}, patching aborted.")
            return 'error'

    
    def create_zip_from_folder(self, folder_path, zip_name):
        """
        Create a zip file from the contents of a folder.
        """
        zip_path = os.path.join(folder_path, zip_name)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path != zip_path and file.endswith(('.zip', '.glb')):
                        zipf.write(file_path, arcname=os.path.relpath(file_path, folder_path))
        return zip_path
    
    def poll_processing_status(self, model_url, model_name, tab_name, uid, original_license, price):
        """
        Poll the processing status of an uploaded model.
        """
        print(f"Polling status for {model_name} with UID {uid} at URL {model_url}")
        headers = {'Authorization': f'Token {self.api_key.get()}'}
        max_retries = 200
        retry_timeout = 30
        retry_count = 0
        patch_status = 'Not started'  # Initialize patch_status here

        while retry_count < max_retries:
            sleep(retry_timeout)
            try:
                response = requests.get(model_url, headers=headers)
                if response.status_code == 200:
                    status_info = response.json()
                    processing_status = status_info['status']['processing']
                    print(f"Processing status for {model_name}: {processing_status}")

                    if processing_status == 'SUCCEEDED':
                        print(self.original_license)
                        print(price)
                        self.update_tree_view(model_name, 'Complete', 'Processing Completed', tab_name, 'Starting...', 'Fully Completed')
                        sleep(5)
                        if self.original_license in ['st', 'ed']:
                            patch_result = self.patch_model(uid, self.original_license, price)
                            patch_status = 'Patch Successful' if patch_result == 'success' else 'Patch Failed'
                            self.update_tree_view(model_name, 'Complete', 'Processing Completed', tab_name, patch_status, 'Fully Completed')
                            break  # Break the loop since processing has succeeded
                        else:
                            patch_status = 'No Patch Required'
                            self.update_tree_view(model_name, 'Upload Successful', 'Completed', tab_name, patch_status, 'Fully Completed')
                    elif processing_status == 'FAILED':
                        patch_status = 'Patch Not Attempted'
                        self.update_tree_view(model_name, 'Processing Failed', processing_status, tab_name, patch_status, 'Aborted')

            except requests.RequestException as exc:
                patch_status = 'Patch Error'
                self.update_tree_view(model_name, 'Upload Failed', str(exc), tab_name, patch_status, 'Aborted')

        if retry_count >= max_retries:
            patch_status = 'Max retries reached'
            self.update_tree_view(model_name, 'Upload Failed', 'Max retries reached', tab_name, patch_status, 'Aborted')
    
    def upload_folder(self, folder_path, main_folder_name, thread_id):
        """
        Upload a folder containing a model to Sketchfab.
        """
        with self.upload_semaphore:
            try:
                self.thread_status[thread_id] = None

                # Validation checks
                if not hasattr(self, 'category1_combobox') or not hasattr(self, 'category2_combobox') or not hasattr(self, 'license_combobox'):
                    return

                model_name = os.path.basename(folder_path)
                display_name = model_name
                self.update_tree_view(model_name, 'Uploading...', 'In progress', main_folder_name, 'Patch Not Started', 'In Progress')

                # Collect and validate category and license information
                category1_slug = self.category_map1.get(self.category1_combobox.get())
                category2_slug = self.category_map2.get(self.category2_combobox.get())
                license_slug = self.license_map.get(self.license_combobox.get())
                if not category1_slug or not license_slug:
                    self.update_tree_view(display_name, 'Upload Failed', 'Invalid category or license', main_folder_name, 'Invalid', 'Aborted')
                    return

                description = self.description_textbox.get("1.0", ctk.END).strip()
                tags_input = self.tags_textbox.get("1.0", ctk.END).strip()
                tags_list = tags_input.split('\n') if tags_input else []

                zip_name = f"model_{random.randint(1000, 9999)}.zip"
                zip_file_path = self.create_zip_from_folder(folder_path, zip_name)

                # Handle pricing information for certain licenses
                price_float = None
                if license_slug in ['st', 'ed']:
                    normalized_price = self.price.get().replace(',', '.')
                    try:
                        price_float = float(normalized_price)
                    except ValueError:
                        self.update_tree_view(display_name, 'Invalid Price Format', 'Please enter a valid number', main_folder_name, 'Invalid', 'Aborted')
                        return

                data = {
                    'name': model_name,
                    'description': description,
                    'tags': tags_list,
                    'categories': [category1_slug] + ([category2_slug] if category2_slug else []),
                    'license': license_slug,
                    'private': bool(self.private.get()),
                    'password': self.password.get() if self.private.get() else None,
                    'isPublished': bool(self.isPublished.get()),
                    'isInspectable': bool(self.isInspectable.get()),
                    'price': price_float if price_float else None
                }

                uid, url, status, self.original_license, error_message = self.upload_model(zip_file_path, data)
                if status == 429:
                    self.thread_status[thread_id] = 429
                    return self.upload_folder(folder_path, main_folder_name, thread_id)  # Retry upload
                elif status == 'success':
                    self.thread_status[thread_id] = 'success'
                    print(self.original_license)
                    threading.Thread(target=self.poll_processing_status, args=(url, display_name, main_folder_name, uid, self.original_license, price_float), daemon=True).start()
                    self.update_tree_view(model_name, 'Upload Successful', 'Processing...', main_folder_name, 'Patch Not Started', 'In Progress')
                else:
                    self.thread_status[thread_id] = 'failed'
                    self.update_tree_view(display_name, 'Upload Failed', error_message or 'Error during upload', main_folder_name, 'Failed', 'Aborted')

                if os.path.exists(zip_file_path):
                    os.remove(zip_file_path)
            finally:
                print("Finished")

if __name__ == "__main__":
    app = UploadApp()
    app.mainloop()