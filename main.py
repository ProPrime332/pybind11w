import tkinter as tk
from tkinter import ttk, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import random
import mylib

class CacheSimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CPU Cache Simulator")
        self.geometry("1200x700")
        
        # Initialize C++ MultiLevelCache
        self.cache = mylib.MultiLevelCache()
        self.time_counter = 0
        
        # Initialize data containers
        self.time_points = []
        self.hit_ratios_read = []
        self.hit_ratios_write = []
        self.log_messages = ["System initialized.", "Ready for operations."]
        
        # Initialize UI components
        self.setup_gui()
        
    def setup_gui(self):
        # Top Dropdown Menu
        self.menu_frame = tk.Frame(self)
        self.menu_frame.pack(fill=tk.X, pady=10)

        self.selected_option = tk.StringVar(value="Simple Read/Write")
        self.dropdown = ttk.Combobox(self.menu_frame, textvariable=self.selected_option, 
                                   values=["Simple Read/Write", "Memory Tracking"], state="readonly")
        self.dropdown.pack(side=tk.RIGHT, padx=20)
        self.dropdown.bind("<<ComboboxSelected>>", lambda event: self.switch_page(self.selected_option.get()))

        # Main Content Area
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')

        # Start with Simple Read/Write page
        self.switch_page("Simple Read/Write")

    def switch_page(self, page_name):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        if page_name == "Simple Read/Write":
            self.simple_read_write_page()
        elif page_name == "Memory Tracking":
            self.memory_tracking_page()

    def simple_read_write_page(self):
        frame = tk.Frame(self.main_frame)
        frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Left frame for input and log
        left_frame = tk.Frame(frame)
        left_frame.pack(side="left", fill="both", expand=True)

        # Right frame for graph
        right_frame = tk.Frame(frame, width=300, height=300, bg="white", relief="solid", bd=2)
        right_frame.pack(side="left", padx=30, pady=20)
        right_frame.pack_propagate(False)

        # Initialize matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(3.5, 3.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.update_graph()

        # Input components
        self.write_address_entry = tk.Entry(left_frame, width=12, font=("Arial", 13))
        self.write_value_entry = tk.Entry(left_frame, width=12, font=("Arial", 13))
        self.read_address_entry = tk.Entry(left_frame, width=12, font=("Arial", 13))
        self.log_output = scrolledtext.ScrolledText(left_frame, width=70, height=18, font=("Arial", 12))

        # Build left frame layout
        self.build_input_layout(left_frame)
        
    def build_input_layout(self, parent):
        label_font = ("Arial", 14, "bold")
        entry_font = ("Arial", 13)
        button_font = ("Arial", 12)

        # Write Section
        tk.Label(parent, text="Write to Memory", font=label_font).grid(row=0, column=0, columnspan=3, pady=10, sticky="w")
        tk.Label(parent, text="Address:", font=entry_font).grid(row=1, column=0, padx=5, sticky="w")
        self.write_address_entry.grid(row=1, column=1, padx=5, sticky="w")
        tk.Label(parent, text="Value:", font=entry_font).grid(row=1, column=2, padx=5, sticky="w")
        self.write_value_entry.grid(row=1, column=3, padx=5, sticky="w")
        self.write_value_entry.bind("<Return>", lambda event: self.write_memory())
        
        tk.Button(parent, text="Write", command=self.write_memory, font=button_font, width=10
                 ).grid(row=1, column=4, padx=10, sticky="w")

        # Read Section
        tk.Label(parent, text="Read from Memory", font=label_font).grid(row=2, column=0, columnspan=3, pady=10, sticky="w")
        tk.Label(parent, text="Address:", font=entry_font).grid(row=3, column=0, padx=5, sticky="w")
        self.read_address_entry.grid(row=3, column=1, padx=5, sticky="w")
        self.read_address_entry.bind("<Return>", lambda event: self.read_memory())
        
        tk.Button(parent, text="Read", command=self.read_memory, font=button_font, width=10
                 ).grid(row=3, column=2, padx=10, sticky="w")

        # Log Section
        tk.Button(parent, text="Refresh", command=self.clear_logs, bg="red", fg="white",
                 font=button_font, width=12).grid(row=4, column=0, columnspan=3, pady=10, sticky="w")
        self.log_output.grid(row=5, column=0, columnspan=5, pady=20, sticky="w")
        self.update_log_output()

    def update_graph(self):
        self.ax.clear()
        self.ax.set_title("Cache Access Time vs Hit Ratio", fontsize=14)
        self.ax.set_xlabel("Time / Operations", fontsize=12)
        self.ax.set_ylabel("Hit Ratio", fontsize=12)
        
        if self.time_points:
            self.ax.plot(self.time_points, self.hit_ratios_read, color='blue', label='Read', marker='o')
            self.ax.plot(self.time_points, self.hit_ratios_write, color='green', label='Write', marker='x')
            self.ax.legend()
        
        self.canvas.draw()

    def clear_logs(self):
        self.log_output.delete("1.0", tk.END)
        self.write_address_entry.delete(0, tk.END)
        self.write_value_entry.delete(0, tk.END)
        self.read_address_entry.delete(0, tk.END)

    def update_log_output(self):
        self.log_output.delete("1.0", tk.END)
        for msg in self.log_messages:
            self.log_output.insert(tk.END, f"{msg}\n")
        self.log_output.see(tk.END)

    def write_memory(self):
        address = self.write_address_entry.get()
        value = self.write_value_entry.get()
        if address and value:
            try:
                self.time_counter += 1
                # Access through accessMemory instead of direct L1 access
                result = self.cache.accessMemory(int(address), self.time_counter,
                            lambda msg: self.log_messages.append(f"WRITE: {msg}"))
            
                # Update graph with real hit ratio
                total_accesses = self.cache.getTotalHits() + self.cache.getTotalMisses()
                hit_ratio = self.cache.getTotalHits() / total_accesses if total_accesses > 0 else 0
            
                self.time_points.append(self.time_counter)
                self.hit_ratios_write.append(hit_ratio)
                self.update_graph()
            
            except ValueError:
                self.log_messages.append("Invalid address/value format")
        else:
            self.log_messages.append("Error: Address and value required")
        self.update_log_output()
        self.write_address_entry.delete(0, tk.END)
        self.write_value_entry.delete(0, tk.END)

    def read_memory(self):
        address = self.read_address_entry.get()
        if address:
            try:
                self.time_counter += 1
                result = self.cache.accessMemory(int(address), self.time_counter,
                           lambda msg: self.log_messages.append(msg))
                
                total_accesses = self.cache.getTotalHits() + self.cache.getTotalMisses()
                hit_ratio = self.cache.getTotalHits() / total_accesses if total_accesses > 0 else 0
                
                self.time_points.append(self.time_counter)
                self.hit_ratios_read.append(hit_ratio)
                self.update_graph()
                
            except ValueError:
                self.log_messages.append("Invalid address format")
        else:
            self.log_messages.append("Error: Please enter a memory address")
        self.update_log_output()
        self.read_address_entry.delete(0, tk.END)

    def memory_tracking_page(self):
        frame = tk.Frame(self.main_frame)
        frame.pack(expand=True, pady=20, padx=10)
        
        # Memory Tracking page implementation
        # (Add your memory tracking components here following the same pattern)

if __name__ == "__main__":
    app = CacheSimulatorGUI()
    app.mainloop()