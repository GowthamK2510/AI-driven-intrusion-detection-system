import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import platform
import os
import re
import shutil
import socket
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import time
from datetime import datetime
import logging
import concurrent.futures
import nmap
from scapy.all import ARP, Ether, srp, IP, TCP, sr1, send, Raw

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("network_scanner.log"),
        logging.StreamHandler()
    ]
)

class AdvancedNetworkScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("CyberSentinel Network Scanner")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1e1e1e")
        
        # Locate Nmap executable path
        nmap_path = 'nmap'
        if platform.system() == "Windows":
            common_paths = [
                'nmap',
                os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Nmap', 'nmap.exe'),
                os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Nmap', 'nmap.exe')
            ]
            for p in common_paths:
                if shutil.which(p) or os.path.exists(p):
                    nmap_path = p
                    break

        # Nmap controller
        self.nm = nmap.PortScanner(nmap_search_path=(nmap_path,))
        
        # Initialize variables
        self.scan_active = False
        self.current_scan = None
        self.scan_results = {}
        self.target = tk.StringVar(value="192.168.1.0/24")
        self.ports = tk.StringVar(value="22,80,443,8080")
        self.scan_type = tk.StringVar(value="syn")
        self.vuln_scan = tk.BooleanVar(value=False)
        self.auto_save = tk.BooleanVar(value=True)
        
        # Create UI
        self.create_widgets()
        self.create_menu()
        self.setup_styles()
        
        # Set icon (if available)
        try:
            self.root.iconbitmap('cyber.ico')
        except:
            pass

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', background='#1e1e1e', foreground='#e0e0e0')
        style.configure('TButton', background='#2a2a2a', foreground='#e0e0e0')
        style.configure('TEntry', fieldbackground='#2a2a2a', foreground='#e0e0e0')
        style.configure('TCombobox', fieldbackground='#2a2a2a', foreground='#e0e0e0')
        style.configure('TRadiobutton', background='#1e1e1e', foreground='#e0e0e0')
        style.configure('TCheckbutton', background='#1e1e1e', foreground='#e0e0e0')
        
        style.map('TButton',
                 background=[('active', '#3a3a3a')],
                 foreground=[('active', '#ffffff')])

    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Results", command=self.save_results)
        file_menu.add_command(label="Export Report", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Scan menu
        scan_menu = tk.Menu(menubar, tearoff=0)
        scan_menu.add_command(label="Start Scan", command=self.start_scan)
        scan_menu.add_command(label="Stop Scan", command=self.stop_scan)
        scan_menu.add_separator()
        scan_menu.add_command(label="Clear Results", command=self.clear_results)
        menubar.add_cascade(label="Scan", menu=scan_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Network Discovery", command=self.discover_network)
        tools_menu.add_command(label="Port Banner Grab", command=self.banner_grab)
        tools_menu.add_command(label="Advanced Route Tracker", command=self.route_tracker)
        tools_menu.add_command(label="Vulnerability DB Update", command=self.update_vuln_db)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        self.root.config(menu=menubar)

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Target configuration
        target_frame = ttk.LabelFrame(main_frame, text="Scan Configuration", padding=10)
        target_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(target_frame, text="Target Network:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(target_frame, textvariable=self.target, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(target_frame, text="Ports (comma-separated):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(target_frame, textvariable=self.ports, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(target_frame, text="Scan Type:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        scan_types = ttk.Combobox(target_frame, textvariable=self.scan_type, state="readonly", width=15)
        scan_types['values'] = ('syn', 'connect', 'ack', 'window', 'maimon', 'ftp-bounce')
        scan_types.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Checkbutton(target_frame, text="Vulnerability Scan", variable=self.vuln_scan).grid(
            row=0, column=2, padx=20, pady=5, sticky=tk.W)
        ttk.Checkbutton(target_frame, text="Auto-Save Results", variable=self.auto_save).grid(
            row=1, column=2, padx=20, pady=5, sticky=tk.W)
        
        # Control buttons
        btn_frame = ttk.Frame(target_frame)
        btn_frame.grid(row=2, column=2, padx=20, pady=5, sticky=tk.E)
        ttk.Button(btn_frame, text="Start Scan", command=self.start_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Stop Scan", command=self.stop_scan).pack(side=tk.LEFT, padx=5)
        
        # Results area
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left panel - Hosts and ports
        left_panel = ttk.Frame(results_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        hosts_label = ttk.Label(left_panel, text="Discovered Hosts")
        hosts_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        self.hosts_tree = ttk.Treeview(left_panel, columns=("IP", "Status", "OS"), show="headings")
        self.hosts_tree.heading("IP", text="IP Address")
        self.hosts_tree.heading("Status", text="Status")
        self.hosts_tree.heading("OS", text="OS Guess")
        self.hosts_tree.column("IP", width=120)
        self.hosts_tree.column("Status", width=80)
        self.hosts_tree.column("OS", width=150)
        self.hosts_tree.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Details and visualization
        right_panel = ttk.Frame(results_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Tabs for different views
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Details tab
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="Details")
        
        self.details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, 
                                                   bg="#2a2a2a", fg="#e0e0e0", 
                                                   font=("Consolas", 10))
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visualization tab
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="Visualization")
        
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Recommendations tab
        rec_frame = ttk.Frame(self.notebook)
        self.notebook.add(rec_frame, text="Recommendations")
        
        self.rec_text = scrolledtext.ScrolledText(rec_frame, wrap=tk.WORD, 
                                               bg="#2a2a2a", fg="#e0e0e0",
                                               font=("Consolas", 10))
        self.rec_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def discover_network(self):
        """Network discovery using ARP ping"""
        self.status_var.set("Discovering network...")
        self.update_idletasks()
        
        network = self.target.get()
        if not network:
            messagebox.showerror("Error", "Please enter a network range")
            return
            
        self.details_text.insert(tk.END, f"Starting network discovery for {network}...\n")
        
        try:
            # Create ARP request packet
            arp_request = ARP(pdst=network)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether/arp_request
            
            # Send packets and capture responses
            result = srp(packet, timeout=3, verbose=0)[0]
            
            # Process results
            discovered = []
            for sent, received in result:
                discovered.append(received.psrc)
                self.details_text.insert(tk.END, f"Discovered: {received.psrc} - {received.hwsrc}\n")
            
            self.status_var.set(f"Discovered {len(discovered)} hosts")
            return discovered
        except Exception as e:
            self.details_text.insert(tk.END, f"Error: {str(e)}\n")
            self.status_var.set("Error in network discovery")
            return []

    def start_scan(self):
        """Start the network scan in a separate thread"""
        if self.scan_active:
            return
            
        self.scan_active = True
        self.current_scan = threading.Thread(target=self.run_scan, daemon=True)
        self.current_scan.start()
        self.update_status("Scan in progress...")

    def run_scan(self):
        """Execute the actual scan with Nmap"""
        try:
            target = self.target.get()
            ports = self.ports.get()
            
            if not target:
                self.update_status("Error: Target required")
                return
                
            self.update_status(f"Scanning {target}...")
            
            # Build Nmap arguments
            arguments = "-sS -sV -O"
            if self.vuln_scan.get():
                arguments += " --script vuln"
            if ports:
                arguments += f" -p {ports}"
            
            # Run scan
            self.nm.scan(hosts=target, arguments=arguments)
            
            # Process results
            self.process_results()
            
            # Generate recommendations
            self.generate_recommendations()
            
            # Auto-save if enabled
            if self.auto_save.get():
                self.save_results()
                
        except Exception as e:
            logging.exception("Scan failed")
            self.update_status(f"Error: {str(e)}")
        finally:
            self.scan_active = False
            if not self.scan_active:
                self.update_status("Scan completed")

    def process_results(self):
        """Process and display scan results"""
        self.scan_results = {}
        self.hosts_tree.delete(*self.hosts_tree.get_children())
        
        for host in self.nm.all_hosts():
            if 'tcp' in self.nm[host]:
                ports = []
                for port in self.nm[host]['tcp']:
                    state = self.nm[host]['tcp'][port]['state']
                    service = self.nm[host]['tcp'][port].get('name', '')
                    version = self.nm[host]['tcp'][port].get('version', '')
                    ports.append(f"{port} ({state}) - {service} {version}")
                
                os_guess = "Unknown"
                if 'osmatch' in self.nm[host] and self.nm[host]['osmatch']:
                    os_guess = self.nm[host]['osmatch'][0]['name']
                
                self.hosts_tree.insert("", "end", values=(host, "Up", os_guess))
                self.scan_results[host] = {
                    'ports': ports,
                    'os': os_guess,
                    'status': self.nm[host].state()
                }
            
            # Update details
            self.details_text.insert(tk.END, f"\nHost: {host} ({self.nm[host].state()})\n")
            self.details_text.insert(tk.END, f"OS Guess: {os_guess}\n")
            self.details_text.insert(tk.END, "Open Ports:\n")
            
            if 'tcp' in self.nm[host]:
                for port in self.nm[host]['tcp']:
                    self.details_text.insert(tk.END, 
                        f"  {port}/{self.nm[host]['tcp'][port]['name']}: "
                        f"{self.nm[host]['tcp'][port]['state']} "
                        f"({self.nm[host]['tcp'][port].get('version', '')})\n")
            else:
                self.details_text.insert(tk.END, "  No open ports found\n")

        # Update visualization
        self.update_visualization()

    def update_visualization(self):
        """Create network visualization"""
        self.ax.clear()
        
        # Count open ports by host
        host_ports = {}
        for host, data in self.scan_results.items():
            host_ports[host] = len(data['ports'])
        
        if host_ports:
            # Create pie chart for port distribution
            self.ax.pie(host_ports.values(), labels=host_ports.keys(), 
                       autopct='%1.1f%%', startangle=90)
            self.ax.set_title("Host Port Distribution")
            self.canvas.draw()
        else:
            self.ax.text(0.5, 0.5, "No data available", 
                        ha='center', va='center', fontsize=12)
            self.canvas.draw()

    def generate_recommendations(self):
        """Generate security recommendations based on scan results"""
        self.rec_text.delete(1.0, tk.END)
        
        if not self.scan_results:
            self.rec_text.insert(tk.END, "No scan results available\n")
            return
            
        # Check for common vulnerabilities
        recommendations = []
        
        for host, data in self.scan_results.items():
            for port_data in data['ports']:
                port = re.search(r'(\d+)', port_data)
                if port:
                    port = int(port.group())
                    
                    # Check for vulnerable ports
                    if port in [21, 22, 23, 80, 443, 3389]:
                        if "unknown" in port_data.lower():
                            recommendations.append(
                                f"⚠️ Critical: Unknown service on {host}:{port} - "
                                "Verify if necessary and secure"
                            )
                        elif "apache" in port_data.lower() or "nginx" in port_data.lower():
                            recommendations.append(
                                f"⚠️ High: Web server ({host}:{port}) - "
                                "Check for latest security patches"
                            )
                        elif "ssh" in port_data.lower() and "1.0" in port_data:
                            recommendations.append(
                                f"⚠️ Critical: SSHv1 detected on {host}:{port} - "
                                "Upgrade to SSHv2 immediately"
                            )
        
        # Add general recommendations
        recommendations.append("\nGeneral Recommendations:")
        recommendations.append("• Implement firewall rules to restrict access to critical ports")
        recommendations.append("• Apply the principle of least privilege for all services")
        recommendations.append("• Enable logging and monitoring for all network devices")
        recommendations.append("• Perform regular vulnerability scanning and patch management")
        
        # Display recommendations
        for rec in recommendations:
            self.rec_text.insert(tk.END, rec + "\n")

    def banner_grab(self):
        """Perform banner grabbing on open ports"""
        selected = self.hosts_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a host first")
            return
            
        host = self.hosts_tree.item(selected[0])['values'][0]
        self.details_text.insert(tk.END, f"\nPerforming banner grab on {host}...\n")
        
        try:
            for port in [21, 22, 23, 80, 443, 3389]:  # Common ports
                try:
                    pkt = IP(dst=host)/TCP(dport=port, flags="S")
                    resp = sr1(pkt, timeout=2, verbose=0)
                    if resp and resp.haslayer(TCP) and resp[TCP].flags == 0x12:
                        # Send RST to close connection
                        send(IP(dst=host)/TCP(dport=port, flags="R"), verbose=0)
                        
                        # Get banner
                        banner = self.get_banner(host, port)
                        if banner:
                            self.details_text.insert(tk.END, 
                                f"Banner on {host}:{port}: {banner}\n")
                except:
                    continue
        except Exception as e:
            self.details_text.insert(tk.END, f"Error: {str(e)}\n")

    def get_banner(self, ip, port):
        """Get service banner from port"""
        try:
            pkt = IP(dst=ip)/TCP(dport=port, flags="S")
            resp = sr1(pkt, timeout=2, verbose=0)
            if resp and resp.haslayer(TCP) and resp[TCP].flags == 0x12:
                # Send ACK to establish connection
                send(IP(dst=ip)/TCP(dport=port, flags="A", seq=resp[TCP].ack, ack=resp[TCP].seq+1), verbose=0)
                
                # Send data request
                data = b"GET / HTTP/1.1\r\nHost: test\r\n\r\n"
                resp = sr1(IP(dst=ip)/TCP(dport=port, flags="PA", seq=resp[TCP].ack, ack=resp[TCP].seq+1)/data, 
                          timeout=3, verbose=0)
                
                if resp and resp.haslayer(TCP) and resp.haslayer(Raw):
                    return resp[Raw].load.decode('utf-8', errors='ignore')[:100]
            return None
        except:
            return None

    def route_tracker(self):
        """Advanced Route Tracker with device categorization"""
        tracker_window = tk.Toplevel(self.root)
        tracker_window.title("Advanced Route Tracker")
        tracker_window.geometry("800x600")
        tracker_window.configure(bg="#1e1e1e")
        
        # Target input
        input_frame = ttk.Frame(tracker_window, padding=10)
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="Target IP/Domain:").pack(side=tk.LEFT, padx=5)
        # Attempt to get a default IP from the main scan target
        target_val = self.target.get().split('/')[0] if self.target.get() else ""
        target_var = tk.StringVar(value=target_val)
        ttk.Entry(input_frame, textvariable=target_var, width=30).pack(side=tk.LEFT, padx=5)
        
        tree = ttk.Treeview(tracker_window, columns=("Hop", "IP", "Hostname", "Time"), show="headings")
        tree.heading("Hop", text="Hop")
        tree.heading("IP", text="IP Address")
        tree.heading("Hostname", text="Hostname / Device Type")
        tree.heading("Time", text="Latency")
        
        tree.column("Hop", width=50, anchor=tk.CENTER)
        tree.column("IP", width=120)
        tree.column("Hostname", width=450)
        tree.column("Time", width=80, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        status_lbl = ttk.Label(tracker_window, text="Ready", foreground="#e0e0e0")
        status_lbl.pack(side=tk.BOTTOM, anchor=tk.W, padx=10, pady=5)
        
        def run_trace():
            target = target_var.get()
            if not target:
                return
            tree.delete(*tree.get_children())
            status_lbl.config(text=f"Tracing route to {target}...")
            
            def trace_thread():
                system = platform.system().lower()
                cmd = ['tracert', '-d', target] if system == 'windows' else ['traceroute', '-n', target]
                
                try:
                    kwargs = {}
                    if system == 'windows':
                        kwargs['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
                        
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kwargs)
                    
                    hop = 1
                    for line in iter(process.stdout.readline, ''):
                        line = line.strip()
                        if not line or line.startswith("Tracing") or line.startswith("traceroute") or line.startswith("over a maximum"):
                            continue
                            
                        # Extract IP using regex
                        ip_match = re.search(r'\\b(?:[0-9]{1,3}\\.){3}[0-9]{1,3}\\b', line)
                        if ip_match:
                            ip = ip_match.group()
                            
                            # Extract time (e.g., "<1 ms" or "5 ms")
                            time_match = re.search(r'([<0-9]+)\\s*ms', line)
                            time_str = time_match.group() if time_match else "*"
                            
                            # Attempt reverse DNS to classify
                            device_type = "Network Device"
                            try:
                                hostname = socket.gethostbyaddr(ip)[0]
                                name_lower = hostname.lower()
                                if any(x in name_lower for x in ['router', 'gateway', 'edge', 'core', 'gw']):
                                    device_type = "Router / Gateway"
                                elif any(x in name_lower for x in ['isp', 'dynamic', 'hsd', 'broadband', 'telecom']):
                                    device_type = "ISP Tower / Node"
                                elif 'compute' in name_lower or 'cloud' in name_lower or 'server' in name_lower or 'aws' in name_lower:
                                    device_type = "Cloud Server"
                                hostname_display = f"{hostname} ({device_type})"
                            except socket.herror:
                                hostname_display = "Unknown Device"
                                
                            self.root.after(0, lambda h=hop, i=ip, hs=hostname_display, t=time_str: tree.insert("", tk.END, values=(h, i, hs, t)))
                            hop += 1
                        elif "*" in line:
                            self.root.after(0, lambda h=hop: tree.insert("", tk.END, values=(h, "Request Timed Out", "-", "-")))
                            hop += 1
                            
                    process.wait()
                    self.root.after(0, lambda: status_lbl.config(text="Trace complete."))
                except Exception as e:
                    self.root.after(0, lambda err=e: status_lbl.config(text=f"Error: {str(err)}"))
                    
            threading.Thread(target=trace_thread, daemon=True).start()
            
        ttk.Button(input_frame, text="Start Trace", command=run_trace).pack(side=tk.LEFT, padx=10)

    def save_results(self):
        """Save scan results to JSON file"""
        if not self.scan_results:
            messagebox.showinfo("Info", "No results to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump({
                        "scan_time": datetime.now().isoformat(),
                        "target": self.target.get(),
                        "results": self.scan_results
                    }, f, indent=2)
                messagebox.showinfo("Success", f"Results saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save results: {str(e)}")

    def export_report(self):
        """Export detailed PDF report"""
        if not self.scan_results:
            messagebox.showinfo("Info", "No results to export")
            return
            
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                doc = SimpleDocTemplate(filename, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                # Title
                story.append(Paragraph("CyberSentinel Network Security Report", styles['Title']))
                story.append(Spacer(1, 12))
                
                # Scan info
                story.append(Paragraph(f"Target: {self.target.get()}", styles['Normal']))
                story.append(Paragraph(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Add recommendations
                story.append(Paragraph("Security Recommendations:", styles['Heading2']))
                recs = self.rec_text.get(1.0, tk.END).split('\n')
                for rec in recs:
                    if rec.strip():
                        story.append(Paragraph(rec, styles['Normal']))
                
                doc.build(story)
                messagebox.showinfo("Success", f"Report exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export report: {str(e)}")

    def update_vuln_db(self):
        """Update vulnerability database (simulated)"""
        self.update_status("Updating vulnerability database...")
        try:
            # In real implementation, this would update NSE scripts
            subprocess.run(["nmap", "--script-updatedb"], check=True)
            self.update_status("Vulnerability database updated")
            messagebox.showinfo("Success", "Vulnerability database updated successfully")
        except Exception as e:
            self.update_status(f"Update failed: {str(e)}")
            messagebox.showerror("Error", f"Update failed: {str(e)}")

    def stop_scan(self):
        """Stop the active scan"""
        if self.scan_active:
            self.scan_active = False
            self.update_status("Scan stopped by user")
            self.details_text.insert(tk.END, "\n*** Scan stopped by user ***\n")

    def clear_results(self):
        """Clear all scan results"""
        self.hosts_tree.delete(*self.hosts_tree.get_children())
        self.details_text.delete(1.0, tk.END)
        self.rec_text.delete(1.0, tk.END)
        self.ax.clear()
        self.ax.text(0.5, 0.5, "No data available", 
                    ha='center', va='center', fontsize=12)
        self.canvas.draw()
        self.update_status("Results cleared")

    def update_status(self, message):
        """Update status bar with thread-safe method"""
        self.status_var.set(message)
        self.root.update_idletasks()

    def update_idletasks(self):
        """Override to ensure thread safety"""
        try:
            self.root.update_idletasks()
        except tk.TclError:
            pass

if __name__ == "__main__":
    # Verify Nmap installation
    nmap_found = False
    if shutil.which('nmap') or shutil.which('nmap.exe'):
        nmap_found = True
    elif platform.system() == "Windows":
        common_paths = [
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Nmap', 'nmap.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Nmap', 'nmap.exe')
        ]
        if any(os.path.exists(p) for p in common_paths):
            nmap_found = True

    if not nmap_found:
        if platform.system() == "Windows":
            messagebox.showerror("Error", "Nmap not found. Please install Nmap from https://nmap.org (Make sure to add it to PATH during installation).")
        else:
            messagebox.showerror("Error", "Nmap not found. Install with: sudo apt install nmap")
        exit(1)

    # Create and run the application
    root = tk.Tk()
    app = AdvancedNetworkScanner(root)
    root.mainloop()
