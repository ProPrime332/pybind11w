import tkinter as tk
from tkinter import scrolledtext
import mylib  # This is your pybind11 C++ module
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class CacheSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cache Simulator")

        # Set up the Cache Simulator
        self.cache = mylib.MultiLevelCache()

        # Set up the UI elements
        self.create_widgets()

    def create_widgets(self):
        # Create a frame for input controls
        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=10, pady=10)

        # Address input field
        self.label_address = tk.Label(self.frame, text="Address:")
        self.label_address.grid(row=0, column=0, padx=5, pady=5)

        self.entry_address = tk.Entry(self.frame, width=20)
        self.entry_address.grid(row=0, column=1, padx=5, pady=5)

        # Time input field
        self.label_time = tk.Label(self.frame, text="Time:")
        self.label_time.grid(row=1, column=0, padx=5, pady=5)

        self.entry_time = tk.Entry(self.frame, width=20)
        self.entry_time.grid(row=1, column=1, padx=5, pady=5)

        # Access button
        self.button_access = tk.Button(self.frame, text="Access Memory", command=self.access_memory)
        self.button_access.grid(row=2, column=0, columnspan=2, pady=10)

        # Cache log area
        self.label_log = tk.Label(self.root, text="Cache Log:")
        self.label_log.pack(pady=5)

        self.cache_log = scrolledtext.ScrolledText(self.root, width=50, height=15, wrap=tk.WORD)
        self.cache_log.pack(padx=10, pady=10)

        # Visualization frame
        self.visualization_frame = tk.Frame(self.root)
        self.visualization_frame.pack(padx=10, pady=10)

        # Button for random address and time generation
        self.button_generate = tk.Button(self.visualization_frame, text="Generate Random Access", command=self.generate_random_access)
        self.button_generate.pack(side=tk.LEFT, padx=5, pady=5)

        # Plot for visualizing cache hits vs misses
        self.button_plot = tk.Button(self.visualization_frame, text="Plot Cache Hits vs Misses", command=self.plot_cache_hits)
        self.button_plot.pack(side=tk.LEFT, padx=5, pady=5)

    def access_memory(self):
        # Get address and time input values
        try:
            address = int(self.entry_address.get(), 16)  # Address in hexadecimal format
            time = int(self.entry_time.get())
        except ValueError:
            self.cache_log.insert(tk.END, "Invalid input! Please enter valid Address and Time.\n")
            return

        # Clear the previous log
        self.cache_log.delete(1.0, tk.END)

        # Callback function to log messages
        def log_message(message):
            self.cache_log.insert(tk.END, message)
            self.cache_log.yview(tk.END)  # Scroll to the bottom

        # Access memory via the MultiLevelCache object (this is where the C++ logic is invoked)
        self.cache.accessMemory(address, time, log_message)

    def generate_random_access(self):
        """Generate a random address and time for cache access and show the result."""
        address = random.randint(0, 0xFFFFF)  # Generate random address in hex
        time = random.randint(0, 100)  # Random time between 0 and 100
        self.entry_address.delete(0, tk.END)
        self.entry_address.insert(tk.END, hex(address))  # Display address in hexadecimal
        self.entry_time.delete(0, tk.END)
        self.entry_time.insert(tk.END, time)  # Display random time

        # Automatically access memory with the generated values
        self.access_memory()

    def plot_cache_hits(self):
        """Plot cache hits vs misses using matplotlib."""
        # Example data for plotting (you would replace this with actual hit/miss data)
        cache_hits = random.randint(50, 150)
        cache_misses = random.randint(50, 150)

        # Plot the data
        fig, ax = plt.subplots()
        ax.bar(['Cache Hits', 'Cache Misses'], [cache_hits, cache_misses], color=['green', 'red'])

        ax.set_title("Cache Hits vs Misses")
        ax.set_ylabel("Count")
        ax.set_xlabel("Cache Activity")

        # Embed the plot in the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=self.visualization_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

# Set up the main Tkinter window
root = tk.Tk()
app = CacheSimulatorApp(root)

# Start the Tkinter main loop
root.mainloop()
