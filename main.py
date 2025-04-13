import tkinter as tk
from tkinter import ttk, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import mylib

class CacheSimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CPU Cache Simulator")
        self.geometry("1200x700")
        
        # Initialize C++ cache (backend)
        self.cache = mylib.MultiLevelCache()
        self.time_counter = 0
        self.current_page = None
        
        # Data containers
        self.cache_entries = {"L1": [], "L2": [], "L3": []}
        self.time_points = []
        self.hit_ratios_read = []
        self.hit_ratios_write = []
        self.log_messages = []
        
        # Setup GUI
        self.setup_gui()
        self.after(100, self.initialize_cache)

    def setup_gui(self):
        # Top menu
        self.menu_frame = tk.Frame(self)
        self.menu_frame.pack(fill=tk.X, pady=10)
        
        self.selected_option = tk.StringVar(value="Simple Read/Write")
        self.dropdown = ttk.Combobox(
            self.menu_frame, 
            textvariable=self.selected_option,
            values=["Simple Read/Write", "Memory Tracking"],
            state="readonly"
        )
        self.dropdown.pack(side=tk.RIGHT, padx=20)
        self.dropdown.bind("<<ComboboxSelected>>", lambda e: self.switch_page(self.selected_option.get()))
        
        # Main content area
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        
        self.switch_page("Simple Read/Write")

    def switch_page(self, page_name):
        # Clear current page
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.current_page = page_name
        if page_name == "Simple Read/Write":
            self.simple_read_write_page()
        elif page_name == "Memory Tracking":
            self.memory_tracking_page()

    def simple_read_write_page(self):
        frame = tk.Frame(self.main_frame)
        frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Left panel
        left_frame = tk.Frame(frame)
        left_frame.pack(side="left", fill="both", expand=True)
        
        # Right panel with graph
        right_frame = tk.Frame(frame, width=300, height=300, bg="white", relief="solid", bd=2)
        right_frame.pack(side="left", padx=30, pady=20)
        right_frame.pack_propagate(False)
        
        # Graph setup
        self.fig, self.ax = plt.subplots(figsize=(3.5, 3.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.update_graph()
        
        # Input components
        self.build_input_layout(left_frame)

    def build_input_layout(self, parent):
        label_font = ("Arial", 14, "bold")
        entry_font = ("Arial", 13)
        button_font = ("Arial", 12)
        
        # Write section
        tk.Label(parent, text="Write to Memory", font=label_font).grid(row=0, column=0, columnspan=3, pady=10, sticky="w")
        tk.Label(parent, text="Address:", font=entry_font).grid(row=1, column=0, padx=5, sticky="w")
        self.write_address_entry = tk.Entry(parent, width=12, font=entry_font)
        self.write_address_entry.grid(row=1, column=1, padx=5, sticky="w")
        tk.Label(parent, text="Value:", font=entry_font).grid(row=1, column=2, padx=5, sticky="w")
        self.write_value_entry = tk.Entry(parent, width=12, font=entry_font)
        self.write_value_entry.grid(row=1, column=3, padx=5, sticky="w")
        self.write_value_entry.bind("<Return>", lambda e: self.write_memory())
        tk.Button(parent, text="Write", command=self.write_memory, font=button_font, width=10).grid(row=1, column=4, padx=10, sticky="w")
        
        # Read section
        tk.Label(parent, text="Read from Memory", font=label_font).grid(row=2, column=0, columnspan=3, pady=10, sticky="w")
        tk.Label(parent, text="Address:", font=entry_font).grid(row=3, column=0, padx=5, sticky="w")
        self.read_address_entry = tk.Entry(parent, width=12, font=entry_font)
        self.read_address_entry.grid(row=3, column=1, padx=5, sticky="w")
        self.read_address_entry.bind("<Return>", lambda e: self.read_memory())
        tk.Button(parent, text="Read", command=self.read_memory, font=button_font, width=10).grid(row=3, column=2, padx=10, sticky="w")
        
        # Log section
        tk.Button(parent, text="Refresh", command=self.clear_logs, bg="red", fg="white", 
                 font=button_font, width=12).grid(row=4, column=0, columnspan=3, pady=10, sticky="w")
        self.log_output = scrolledtext.ScrolledText(parent, width=70, height=18, font=("Arial", 12))
        self.log_output.grid(row=5, column=0, columnspan=5, pady=20, sticky="w")
        self.update_log_output()

    def memory_tracking_page(self):
        frame = tk.Frame(self.main_frame)
        frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Control panel
        control_frame = tk.Frame(frame)
        control_frame.pack(fill='x', pady=10)
        
        # Search components
        self.search_entry = ttk.Entry(control_frame, width=15, font=('Arial', 12))
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind("<Return>", lambda e: self.start_cache_search())
        ttk.Button(control_frame, text="Search Address", command=self.start_cache_search).pack(side='left', padx=5)
        
        # Cache visualization
        self.create_cache_visualization(frame)
        self.refresh_cache_display()

    def create_cache_visualization(self, parent):
        # Clear existing entries
        for level in self.cache_entries.values():
            level.clear()
        
        cache_container = tk.Frame(parent)
        cache_container.pack(expand=True, fill='both')
        
        for level in ["L1", "L2", "L3"]:
            cache = getattr(self.cache, level)
            level_frame = tk.Frame(cache_container, bd=2, relief='groove')
            level_frame.pack(side='left', expand=True, fill='both', padx=5)
            
            # Header
            header = f"{level} Cache\n{cache.num_sets} Sets × {cache.associativity}-Way"
            tk.Label(level_frame, text=header, font=('Arial', 10, 'bold')).pack(pady=5)
            
            # Create sets
            for set_idx in range(cache.num_sets):
                set_frame = tk.Frame(level_frame, bd=1, relief='ridge')
                set_frame.pack(fill='x', padx=2, pady=2)
                tk.Label(set_frame, text=f"Set {set_idx}", width=6).pack(side='left')
                
                # Create blocks
                for _ in range(cache.associativity):
                    block = tk.Label(set_frame, width=15, height=3, relief='ridge', bg="white", font=('Arial', 9), anchor='center')
                    block.pack(side='left', padx=2)
                    self.cache_entries[level].append(block)
        
        # RAM visualization
        self.ram_frame = tk.Frame(parent, height=50, bg='lightgray', bd=1, relief='sunken')
        self.ram_frame.pack(fill='x', pady=10)
        tk.Label(self.ram_frame, text="Main Memory", font=('Arial', 12, 'bold')).pack(pady=5)

    # Core functionality for read/write
    def write_memory(self):
        address = self.write_address_entry.get()
        value = self.write_value_entry.get()
        if address and value:
            try:
                self.time_counter += 1
                addr = int(address)
            
                # Write to memory (uses our camelCase alias)
                result = self.cache.write_memory(
                    addr, 
                    self.time_counter,
                    lambda msg: self.log_messages.append(f"WRITE: {msg}")
                    )
                
                # Update metrics
                total = self.cache.getTotalHits() + self.cache.getTotalMisses()
                if total > 0:
                    self.hit_ratios_write.append(self.cache.getTotalHits() / total)
                    self.time_points.append(self.time_counter)
                    self.update_graph()
                
                self.refresh_cache_display()
                
            except ValueError:
                self.log_messages.append("Invalid address/value")
        else:
            self.log_messages.append("Missing address/value")
        self.update_log_output()
        self.write_address_entry.delete(0, tk.END)
        self.write_value_entry.delete(0, tk.END)

    def read_memory(self):
        address = self.read_address_entry.get()
        if address:
            try:
                self.time_counter += 1
                addr = int(address)
                result = self.cache.accessMemory(addr, self.time_counter,
                           lambda msg: self.log_messages.append(msg))
                
                # Update metrics
                total = self.cache.getTotalHits() + self.cache.getTotalMisses()
                if total > 0:
                    self.hit_ratios_read.append(self.cache.getTotalHits() / total)
                    self.time_points.append(self.time_counter)
                    self.update_graph()
                
                self.refresh_cache_display()
                
            except ValueError:
                self.log_messages.append("Invalid address")
        else:
            self.log_messages.append("Missing address")
        self.update_log_output()
        self.read_address_entry.delete(0, tk.END)

    # Animated cache search routines
    def start_cache_search(self):
        address = self.search_entry.get()
        if address:
            self.animate_cache_search(address)
            self.search_entry.delete(0, tk.END)

    def animate_cache_search(self, address):
        try:
            addr = int(address)
            self.reset_cache_colors()
            self.time_counter += 1
            self.search_level = 0
            self.levels = ["L1", "L2", "L3"]
            self.search_address = addr
            self.found = False
            self.search_next_level()
        except ValueError:
            self.log_messages.append(f"Invalid address: {address}")
            self.update_log_output()

    def search_next_level(self):
        if self.search_level >= len(self.levels) or self.found:
            if not self.found:
                self.animate_ram_access()
            return
        
        level = self.levels[self.search_level]
        cache = getattr(self.cache, level)
        index = mylib.getIndex(self.search_address, cache.block_size, cache.num_sets)
        tag = mylib.getTag(self.search_address, cache.block_size, cache.num_sets)
        
        # Highlight current set
        set_blocks = self.get_set_blocks(level, index, cache.associativity)
        self.highlight_set(set_blocks, "#fff3cd")
        
        # Check for hit
        hit_index = -1
        for i, block in enumerate(cache.sets[index].blocks):
            if block.valid and block.tag == tag:
                hit_index = i
                break
        
        self.after(800, lambda: self.process_hit_miss(level, index, hit_index, set_blocks))

    def process_hit_miss(self, level, index, hit_index, set_blocks):
        if hit_index != -1:
            self.handle_hit(level, index, hit_index, set_blocks)
        else:
            self.handle_miss(level, index, set_blocks)

    def handle_hit(self, level, index, hit_index, set_blocks):
        set_blocks[hit_index].config(bg="#d4edda")
        for i, block in enumerate(set_blocks):
            if i != hit_index:
                block.config(bg="#f0f0f0")
        self.log_messages.append(f"{level} HIT: Set {index} Block {hit_index}")
        self.update_log_output()
        self.found = True
        self.after(1000, self.reset_cache_colors)

    def handle_miss(self, level, index, set_blocks):
        for block in set_blocks:
            block.config(bg="#f8d7da")
        self.log_messages.append(f"{level} MISS: Set {index}")
        self.update_log_output()
        self.search_level += 1
        self.after(1000, self.continue_search)

    def continue_search(self):
        self.reset_cache_colors()
        self.search_next_level()

    def animate_ram_access(self):
        self.ram_frame.config(bg="#ffd700")
        self.log_messages.append(f"RAM ACCESS: {self.search_address}")
        self.update_log_output()
    
        # Update all cache levels in reverse order (from L3 up to L1)
        for level in reversed(self.levels):
            cache = getattr(self.cache, level)
            index = mylib.getIndex(self.search_address, cache.block_size, cache.num_sets)
            tag = mylib.getTag(self.search_address, cache.block_size, cache.num_sets)
        
            # Find and replace LRU block in the cache set
            lru_index = min(range(cache.associativity), 
                        key=lambda i: cache.sets[index].blocks[i].lastUsedTime)
            cache.sets[index].blocks[lru_index].tag = tag
            cache.sets[index].blocks[lru_index].valid = True
            cache.sets[index].blocks[lru_index].lastUsedTime = self.time_counter
        
            # Compute the full address based on the formula:
            computed_address = (tag * cache.num_sets + index) * cache.block_size
        
            # Prepare the display text with address, tag, and index
            display_text = f"Addr: {computed_address}\nTag: {tag}\nIdx: {index}"
        
            # Update GUI for this level using Label's config
            set_blocks = self.get_set_blocks(level, index, cache.associativity)
            set_blocks[lru_index].config(text=display_text, bg="#d4edda")
    
        # Reset colors after animations
        self.after(1500, self.continue_ram_animation)


    def continue_ram_animation(self):
        self.ram_frame.config(bg="lightgray")
        self.reset_cache_colors()

    # Helper methods
    def get_set_blocks(self, level, index, associativity):
        start = index * associativity
        return self.cache_entries[level][start:start+associativity]

    def highlight_set(self, blocks, color):
        for block in blocks:
            block.config(bg=color)

    def reset_cache_colors(self):
        for level in self.cache_entries.values():
            for block in level:
                block.config(bg="white")

    def refresh_cache_display(self):
        for level in ["L1", "L2", "L3"]:
            cache = getattr(self.cache, level)
            entries = self.cache_entries.get(level, [])
        
            idx = 0
            for set_idx in range(cache.num_sets):
                for block_idx in range(cache.associativity):
                    if idx >= len(entries):
                        break
                
                    cpp_block = cache.sets[set_idx].blocks[block_idx]
                    gui_block = entries[idx]
                
                    if cpp_block.valid:
                        # Compute the full address using the same formula as initialization:
                        computed_address = (cpp_block.tag * cache.num_sets + set_idx) * cache.block_size
                        # Prepare a multiline text with all three values
                        text = f"Addr: {computed_address}\nTag: {cpp_block.tag}\nIdx: {set_idx}"
                        gui_block.config(text=text, fg="red" if cpp_block.dirty else "black")
                    else:
                        gui_block.config(text="")
                    gui_block.config(bg='white')
                    idx += 1

    def update_graph(self):
        self.ax.clear()
        self.ax.set_title("Hit Ratio Over Time")
        self.ax.set_xlabel("Operations")
        self.ax.set_ylabel("Hit Ratio")
        if self.time_points:
            self.ax.plot(self.time_points, self.hit_ratios_read, label='Reads', color='blue')
            self.ax.plot(self.time_points, self.hit_ratios_write, label='Writes', color='green')
            self.ax.legend()
        self.canvas.draw()

    def update_log_output(self):
        if self.log_output.winfo_exists():
            self.log_output.delete("1.0", tk.END)
            for msg in self.log_messages[-20:]:  # Show last 20 messages
                self.log_output.insert(tk.END, msg + "\n")
            self.log_output.see(tk.END)

    def clear_logs(self):
        self.log_messages.clear()
        self.update_log_output()
        self.write_address_entry.delete(0, tk.END)
        self.write_value_entry.delete(0, tk.END)
        self.read_address_entry.delete(0, tk.END)

    def initialize_cache(self):
        """Initialize cache with unique tags by forcing block allocation in each level separately."""
        try:
            level_base_tags = {"L3": 0, "L2": 1000, "L1": 2000}
        
            for level in ["L3", "L2", "L1"]:
                cache = getattr(self.cache, level)
                block_size = cache.block_size
                num_sets = cache.num_sets
                associativity = cache.associativity
                base_tag = level_base_tags[level]
            
                for set_idx in range(num_sets):
                    for way in range(associativity):
                        # Generate unique tag and address
                        tag = base_tag + (set_idx * associativity) + way
                        # The address is calculated so that the index is correctly derived.
                        address = (tag * num_sets + set_idx) * block_size
                    
                        # Force block allocation by writing directly to the lower-level cache
                        # (Using the lower-level write method rather than the multi-level write)
                        cache.write(address, self.time_counter, lambda msg: None)
                        self.time_counter += 1
        
            self.refresh_cache_display()
        except Exception as e:
            print(f"Initialization error: {e}")
            
if __name__ == "__main__":
    app = CacheSimulatorGUI()
    app.mainloop()
