import tkinter as tk
import psutil
from tkinter import messagebox

def check_wifi_connection():
    # Check if WiFi is connected by looking for an active wireless interface
    interfaces = psutil.net_if_addrs()
    for interface in interfaces:
        if 'wlan' in interface:  # 'wlan' typically represents Wi-Fi interfaces
            return True
    return False

def on_check_wifi_button_click():
    if check_wifi_connection():
        messagebox.showinfo("WiFi Status", "WiFi is connected.")
    else:
        messagebox.showwarning("WiFi Status", "WiFi is not connected.")

# Set up the Tkinter window
window = tk.Tk()
window.title("WiFi Status")

# Add a button to check WiFi status
check_button = tk.Button(window, text="Check WiFi Status", command=on_check_wifi_button_click)
check_button.pack(pady=20)

# Run the GUI
window.mainloop()
