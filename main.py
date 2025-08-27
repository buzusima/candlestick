"""
🎮 Pure Candlestick Trading System - Main GUI (FIXED)
main.py

🔧 FIXED ISSUES:
✅ log_text attribute error
✅ OHLC data 'get' method error
✅ numpy.void object handling
✅ Complete GUI initialization

🚀 Features:
✅ MT5 Terminal Scanner (คงเดิม)
✅ Account Selection (คงเดิม)  
✅ Pure Candlestick Dashboard
✅ Real-time Signal Monitoring
✅ Position Management Interface
✅ Performance Tracking
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import ระบบ Pure Candlestick ใหม่
from mt5_connector import MT5Connector          # คงเดิม 100%
from api_connector import BackendAPIConnector   # คงเดิม 100%  
from candlestick_analyzer import CandlestickAnalyzer
from signal_generator import SignalGenerator
from order_executor import OrderExecutor
from position_monitor import PositionMonitor
from performance_tracker import PerformanceTracker
from risk_manager import RiskManager
from data_persistence import create_persistence_manager, integrate_with_analyzer, integrate_with_generator

class PureCandlestickGUI:
    """
    🎮 Pure Candlestick Trading System - Main Interface (FIXED)
    
    🔧 Features:
    - MT5 Terminal Scanner & Account Selection (คงเดิม)
    - Pure Candlestick Analysis Dashboard  
    - Real-time Signal Generation & Monitoring
    - Position Management Interface
    - Performance Analytics
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("🕯️ Pure Candlestick Trading System v1.0")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a1a")
        
        # ตัวแปรระบบ
        self.config = self.load_config()
        self.is_trading = False
        self.trading_thread = None
        
        # Initialize Components
        self.mt5_connector = MT5Connector()
        self.api_connector = None
        self.candlestick_analyzer = None
        self.signal_generator = None  
        self.order_executor = None
        self.position_monitor = None
        self.performance_tracker = None
        self.risk_manager = None
        
        # 🔧 FIXED: Initialize GUI FIRST
        self.setup_gui()
        
        # เริ่ม GUI updates หลังจาก setup เสร็จ
        self.start_gui_updates()
        
        # Log system start
        self.log("🚀 Pure Candlestick Trading System Started")
        self.log("🔍 Scanning for MT5 terminals...")
        
        # Auto scan for MT5 installations
        self.scan_mt5_terminals()
    
    def load_config(self) -> Dict:
        """โหลดการตั้งค่าจากไฟล์"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("✅ Configuration loaded successfully")  # ใช้ print ก่อน log_text ready
                return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")  # ใช้ print ก่อน log_text ready
            # Return default config
            return {
                "trading": {"symbol": "XAUUSD.v", "timeframe": "M5"},
                "candlestick_rules": {
                    "buy_conditions": {"min_body_ratio": 0.1},
                    "sell_conditions": {"min_body_ratio": 0.1},
                    "signal_strength": {"min_signal_strength": 0.6}
                },
                "lot_sizing": {"base_lot": 0.01},
                "risk_management": {"max_positions": 30}
            }
    
    def setup_gui(self):
        """สร้าง GUI Layout - Pure Candlestick Style (FIXED)"""
        
        # ==========================================
        # 🎯 HEADER SECTION 
        # ==========================================
        header_frame = tk.Frame(self.root, bg="#2d2d2d", height=60)
        header_frame.pack(fill="x", padx=5, pady=2)
        header_frame.pack_propagate(False)
        
        # Title และ Status
        title_label = tk.Label(
            header_frame, text="🕯️ Pure Candlestick Trading System", 
            font=("Arial", 16, "bold"), fg="white", bg="#2d2d2d"
        )
        title_label.pack(side="left", padx=10, pady=15)
        
        self.status_label = tk.Label(
            header_frame, text="🔍 Scanning...", 
            font=("Arial", 10), fg="#00ff88", bg="#2d2d2d"
        )
        self.status_label.pack(side="right", padx=10, pady=15)
        
        # ==========================================
        # 🔍 MT5 CONNECTION SECTION (คงเดิม)
        # ==========================================
        connection_frame = tk.LabelFrame(
            self.root, text="🔍 MT5 Terminal & Account Selection", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333"
        )
        connection_frame.pack(fill="x", padx=5, pady=2)
        
        # MT5 Terminals List
        terminals_frame = tk.Frame(connection_frame, bg="#333333")
        terminals_frame.pack(fill="x", padx=5, pady=3)
        
        tk.Label(terminals_frame, text="📟 Available MT5 Terminals:", 
                fg="white", bg="#333333").pack(anchor="w")
        
        self.terminals_listbox = tk.Listbox(
            terminals_frame, height=3, font=("Consolas", 9),
            bg="#404040", fg="white", selectbackground="#0066cc"
        )
        self.terminals_listbox.pack(fill="x", pady=2)
        
        # MT5 Control Buttons
        mt5_buttons_frame = tk.Frame(connection_frame, bg="#333333")
        mt5_buttons_frame.pack(fill="x", padx=5, pady=3)
        
        self.scan_button = tk.Button(
            mt5_buttons_frame, text="🔍 Scan MT5", command=self.scan_mt5_terminals,
            bg="#4a90e2", fg="white", font=("Arial", 9)
        )
        self.scan_button.pack(side="left", padx=2)
        
        self.connect_button = tk.Button(
            mt5_buttons_frame, text="🔗 Connect", command=self.connect_mt5,
            bg="#50c878", fg="white", font=("Arial", 9)
        )
        self.connect_button.pack(side="left", padx=2)
        
        self.disconnect_button = tk.Button(
            mt5_buttons_frame, text="🔌 Disconnect", command=self.disconnect_mt5,
            bg="#ff6b6b", fg="white", font=("Arial", 9), state="disabled"
        )
        self.disconnect_button.pack(side="left", padx=2)
        
        # Account Selection
        accounts_frame = tk.Frame(connection_frame, bg="#333333")
        accounts_frame.pack(fill="x", padx=5, pady=3)
        
        tk.Label(accounts_frame, text="👤 Trading Accounts:", 
                fg="white", bg="#333333").pack(anchor="w")
        
        self.accounts_listbox = tk.Listbox(
            accounts_frame, height=2, font=("Consolas", 9),
            bg="#404040", fg="white", selectbackground="#0066cc"
        )
        self.accounts_listbox.pack(fill="x", pady=2)
        
        # ==========================================
        # 🕯️ PURE CANDLESTICK DASHBOARD
        # ==========================================
        dashboard_frame = tk.Frame(self.root, bg="#1a1a1a")
        dashboard_frame.pack(fill="both", expand=True, padx=5, pady=2)
        
        # Left Panel - Candlestick Analysis & Signals
        left_panel = tk.LabelFrame(
            dashboard_frame, text="🕯️ Candlestick Analysis & Signals", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333", width=400
        )
        left_panel.pack(side="left", fill="both", expand=False, padx=2, pady=2)
        left_panel.pack_propagate(False)
        
        # Current Candlestick Info
        self.candlestick_info = scrolledtext.ScrolledText(
            left_panel, height=8, font=("Consolas", 9),
            bg="#2a2a2a", fg="#00ff88", wrap="word"
        )
        self.candlestick_info.pack(fill="x", padx=5, pady=3)
        
        # Signal Panel
        signal_frame = tk.Frame(left_panel, bg="#333333")
        signal_frame.pack(fill="x", padx=5, pady=3)
        
        tk.Label(signal_frame, text="🎯 Current Signal:", 
                fg="white", bg="#333333", font=("Arial", 9, "bold")).pack()
        
        self.current_signal = tk.Label(
            signal_frame, text="⏳ Waiting...", 
            font=("Arial", 12, "bold"), fg="#ffaa00", bg="#333333"
        )
        self.current_signal.pack(pady=5)
        
        self.signal_strength = tk.Label(
            signal_frame, text="Strength: 0%", 
            font=("Arial", 9), fg="#cccccc", bg="#333333"
        )
        self.signal_strength.pack()
        
        # Trading Controls
        controls_frame = tk.Frame(left_panel, bg="#333333")
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_button = tk.Button(
            controls_frame, text="🚀 Start Trading", command=self.start_trading,
            bg="#50c878", fg="white", font=("Arial", 10, "bold"), state="disabled"
        )
        self.start_button.pack(side="left", padx=2, fill="x", expand=True)
        
        self.stop_button = tk.Button(
            controls_frame, text="⏹️ Stop Trading", command=self.stop_trading,
            bg="#ff6b6b", fg="white", font=("Arial", 10, "bold"), state="disabled"
        )
        self.stop_button.pack(side="right", padx=2, fill="x", expand=True)
        
        # Right Panel - Positions & Performance
        right_panel = tk.Frame(dashboard_frame, bg="#1a1a1a")
        right_panel.pack(side="right", fill="both", expand=True, padx=2, pady=2)
        
        # Positions Panel
        positions_frame = tk.LabelFrame(
            right_panel, text="💰 Active Positions", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333"
        )
        positions_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Positions Table Headers
        headers_frame = tk.Frame(positions_frame, bg="#333333")
        headers_frame.pack(fill="x", padx=5, pady=2)
        
        headers = ["ID", "Type", "Size", "Open", "Current", "P&L", "Age"]
        for i, header in enumerate(headers):
            label = tk.Label(headers_frame, text=header, font=("Arial", 9, "bold"), 
                           fg="white", bg="#333333", width=10)
            label.grid(row=0, column=i, padx=1, sticky="w")
        
        # Positions List
        self.positions_tree = ttk.Treeview(
            positions_frame, columns=headers, show="tree", height=10
        )
        self.positions_tree.pack(fill="both", expand=True, padx=5, pady=2)
        
        # Configure columns
        for i, header in enumerate(headers):
            self.positions_tree.heading(f"#{i+1}", text=header)
            self.positions_tree.column(f"#{i+1}", width=80, anchor="center")
        
        # Position Controls
        position_controls = tk.Frame(positions_frame, bg="#333333")
        position_controls.pack(fill="x", padx=5, pady=3)
        
        self.close_selected_button = tk.Button(
            position_controls, text="❌ Close Selected", 
            command=self.close_selected_position,
            bg="#ff9500", fg="white", font=("Arial", 9)
        )
        self.close_selected_button.pack(side="left", padx=2)
        
        self.close_all_button = tk.Button(
            position_controls, text="🚨 Emergency Close All", 
            command=self.emergency_close_all,
            bg="#ff3333", fg="white", font=("Arial", 9)
        )
        self.close_all_button.pack(side="right", padx=2)
        
        # Performance Panel
        performance_frame = tk.LabelFrame(
            right_panel, text="📊 Performance Metrics", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333"
        )
        performance_frame.pack(fill="x", padx=2, pady=2)
        
        # Performance Metrics
        self.performance_info = scrolledtext.ScrolledText(
            performance_frame, height=6, font=("Consolas", 9),
            bg="#2a2a2a", fg="#00aaff", wrap="word"
        )
        self.performance_info.pack(fill="x", padx=5, pady=3)
        
        # ==========================================
        # 📝 LOG PANEL (FIXED)
        # ==========================================
        log_frame = tk.LabelFrame(
            self.root, text="📝 System Log", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333"
        )
        log_frame.pack(fill="x", padx=5, pady=2)
        
        # 🔧 FIXED: สร้าง log_text attribute
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=8, font=("Consolas", 9),
            bg="#1a1a1a", fg="#cccccc", wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=3)
        
        # Initialize empty displays
        self.update_candlestick_display("⏳ Waiting for connection...")
        self.update_performance_display("📊 No data available")
    
    # ==========================================
    # 🔍 MT5 CONNECTION METHODS (คงเดิม)
    # ==========================================
    
    def scan_mt5_terminals(self):
        """สแกนหา MT5 terminals ทั้งหมด - คงเดิม"""
        try:
            self.log("🔍 Scanning for MT5 terminals...")
            
            # Clear previous results
            self.terminals_listbox.delete(0, tk.END)
            self.accounts_listbox.delete(0, tk.END)
            
            # Find installations
            installations = self.mt5_connector.find_running_mt5_installations()
            
            if not installations:
                self.log("❌ No running MT5 terminals found")
                self.terminals_listbox.insert(0, "❌ No MT5 terminals running")
                return
            
            self.log(f"✅ Found {len(installations)} MT5 terminal(s)")
            
            # Add to listbox
            for i, inst in enumerate(installations):
                exe_type = "64-bit" if "64" in inst.executable_type else "32-bit"
                display_text = f"{i}: 🟢 {inst.broker} ({exe_type})"
                self.terminals_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            self.log(f"❌ MT5 scan error: {e}")
    
    def connect_mt5(self):
        """เชื่อมต่อกับ MT5 terminal ที่เลือก - คงเดิม"""
        try:
            selection = self.terminals_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select MT5 terminal first")
                return
            
            terminal_index = selection[0]
            self.log(f"🔗 Connecting to MT5 terminal #{terminal_index}...")
            
            # Connect to selected terminal
            if self.mt5_connector.connect_to_installation(terminal_index):
                self.log("✅ MT5 connection successful")
                self.status_label.config(text="🟢 MT5 Connected", fg="#00ff88")
                
                # เปิดใช้งาน buttons
                self.connect_button.config(state="disabled")
                self.disconnect_button.config(state="normal")
                self.start_button.config(state="normal")
                
                # Load accounts
                self.load_accounts()
                
                # Initialize trading components
                self.initialize_trading_components()
                
            else:
                self.log("❌ MT5 connection failed")
                
        except Exception as e:
            self.log(f"❌ MT5 connection error: {e}")
    
    def disconnect_mt5(self):
        """ตัดการเชื่อมต่อ MT5 - คงเดิม"""
        try:
            self.log("🔌 Disconnecting from MT5...")
            
            # Stop trading first
            if self.is_trading:
                self.stop_trading()
            
            # Disconnect
            if self.mt5_connector.disconnect():
                self.log("✅ MT5 disconnected successfully")
                self.status_label.config(text="🔍 Disconnected", fg="#ffaa00")
                
                # Reset buttons
                self.connect_button.config(state="normal")
                self.disconnect_button.config(state="disabled") 
                self.start_button.config(state="disabled")
                self.stop_button.config(state="disabled")
                
                # Clear displays
                self.accounts_listbox.delete(0, tk.END)
                self.update_candlestick_display("⏳ Waiting for connection...")
                self.update_positions_display([])
                self.update_performance_display("📊 No data available")
            
        except Exception as e:
            self.log(f"❌ MT5 disconnect error: {e}")
    
    def load_accounts(self):
        """โหลดรายการบัญชี - คงเดิม"""
        try:
            self.accounts_listbox.delete(0, tk.END)
            
            account_info = self.mt5_connector.get_account_info()
            if account_info:
                account_text = f"👤 {account_info.get('login', 'Unknown')} - {account_info.get('company', 'Unknown')}"
                self.accounts_listbox.insert(0, account_text)
                self.log(f"✅ Account loaded: {account_info.get('login')}")
            else:
                self.accounts_listbox.insert(0, "❌ No account information")
                
        except Exception as e:
            self.log(f"❌ Error loading accounts: {e}")
    
    # ==========================================
    # 🕯️ PURE CANDLESTICK METHODS (ใหม่)
    # ==========================================
    
    def initialize_trading_components(self):
        """เริ่มต้น Pure Candlestick Trading Components"""
        try:
            self.log("🕯️ Initializing Pure Candlestick components...")
            
            # เช็คว่าเชื่อมต่อ MT5 แล้วหรือยัง
            if not self.mt5_connector.is_connected:
                self.log("❌ MT5 not connected - cannot initialize components")
                return
            
            # Initialize components ตามลำดับ
            self.candlestick_analyzer = CandlestickAnalyzer(self.mt5_connector, self.config)
            self.signal_generator = SignalGenerator(self.candlestick_analyzer, self.config)
            self.order_executor = OrderExecutor(self.mt5_connector, self.config)
            self.position_monitor = PositionMonitor(self.mt5_connector, self.config)
            self.performance_tracker = PerformanceTracker(self.config)
            self.risk_manager = RiskManager(self.mt5_connector, self.config)
            
            self.log("✅ All Pure Candlestick components initialized")
            
        except Exception as e:
            self.log(f"❌ Component initialization error: {e}")
            self.log("💡 Some features may not work properly")
    
    def start_trading(self):
        """เริ่ม Pure Candlestick Trading"""
        try:
            if self.is_trading:
                self.log("⚠️ Trading is already running")
                return
            
            if not self.mt5_connector.is_connected:
                messagebox.showwarning("Warning", "Please connect to MT5 first")
                return
            
            self.log("🚀 Starting Pure Candlestick Trading System...")
            self.is_trading = True
            
            # Update UI
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal") 
            self.status_label.config(text="🟢 Trading Active", fg="#00ff88")
            
            # Start trading thread
            self.trading_thread = threading.Thread(target=self.trading_loop, daemon=True)
            self.trading_thread.start()
            
            self.log("✅ Pure Candlestick Trading started")
            
        except Exception as e:
            self.log(f"❌ Start trading error: {e}")
            self.is_trading = False
    
    def stop_trading(self):
        """หยุด Pure Candlestick Trading"""
        try:
            self.log("⏹️ Stopping Pure Candlestick Trading...")
            self.is_trading = False
            
            # Update UI
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="🟡 Trading Stopped", fg="#ffaa00")
            
            self.log("✅ Pure Candlestick Trading stopped")
            
        except Exception as e:
            self.log(f"❌ Stop trading error: {e}")
    
    def trading_loop(self):
        """หลัก Trading Loop - Pure Candlestick Logic"""
        self.log("🔄 Pure Candlestick trading loop started")
        
        while self.is_trading:
            try:
                # 1. วิเคราะห์แท่งเทียนปัจจุบัน
                if self.candlestick_analyzer:
                    candlestick_data = self.candlestick_analyzer.get_current_analysis()
                    
                    if candlestick_data:
                        # Update display
                        self.update_candlestick_display_from_data(candlestick_data)
                        
                        # 2. สร้าง signal
                        if self.signal_generator:
                            signal_data = self.signal_generator.generate_signal(candlestick_data)
                            
                            if signal_data and signal_data.get('action') != 'WAIT':
                                # Update signal display
                                self.update_signal_display(signal_data)
                                
                                # บันทึก signal ใน performance tracker
                                if self.performance_tracker:
                                    self.performance_tracker.record_signal(signal_data)
                                
                                # 3. ส่งออเดอร์ (ถ้ามี signal)
                                if self.order_executor:
                                    execution_result = self.order_executor.execute_signal(signal_data)
                                    
                                    if execution_result:
                                        self.log(f"✅ Order executed: {signal_data.get('action')} - {execution_result.get('success', False)}")
                                        
                                        # บันทึก execution ใน performance tracker
                                        if self.performance_tracker:
                                            self.performance_tracker.record_execution(execution_result, signal_data)
                
                # 4. ติดตาม positions
                if self.position_monitor:
                    positions = self.position_monitor.get_all_positions()
                    self.update_positions_display(positions)
                    
                    # ตรวจสอบการปิดออเดอร์อัจฉริยะ
                    close_actions = self.position_monitor.check_smart_close_opportunities()
                    if close_actions:
                        self.log(f"🎯 Smart close opportunities: {len(close_actions)}")
                        for action in close_actions[:2]:  # ทำแค่ 2 actions ต่อ cycle
                            if self.position_monitor.execute_close_action(action):
                                self.log(f"✅ Smart close executed: {action.get('action_type')}")
                
                # 5. อัพเดท performance
                if self.performance_tracker:
                    performance = self.performance_tracker.get_current_metrics()
                    self.update_performance_display_from_data(performance)
                
                # 6. ตรวจสอบ risk
                if self.risk_manager:
                    risk_status = self.risk_manager.check_risk_levels()
                    if risk_status.get('emergency_stop', False):
                        self.log("🚨 EMERGENCY STOP triggered by risk manager!")
                        self.emergency_close_all()
                        break
                
                # Sleep before next iteration
                time.sleep(3)  # ทุก 3 วินาที
                
            except Exception as e:
                self.log(f"❌ Trading loop error: {e}")
                time.sleep(5)  # รอนานกว่าถ้าเกิด error
        
        self.log("🔄 Pure Candlestick trading loop ended")
    
    # ==========================================
    # 📊 DISPLAY UPDATE METHODS
    # ==========================================
    
    def update_candlestick_display(self, message: str):
        """อัพเดท Candlestick Display แบบง่าย"""
        try:
            self.candlestick_info.delete(1.0, tk.END)
            self.candlestick_info.insert(tk.END, message)
            self.candlestick_info.see(tk.END)
        except Exception as e:
            print(f"❌ Candlestick display error: {e}")
    
    def update_candlestick_display_from_data(self, data: Dict):
        """อัพเดท Candlestick Display จากข้อมูลจริง"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # สร้างข้อความแสดงผล
            display_text = f"""🕯️ CANDLESTICK ANALYSIS [{timestamp}]
{'='*40}

📊 Current Candle:
   Open:  ${data.get('open', 0):.2f}
   High:  ${data.get('high', 0):.2f}  
   Low:   ${data.get('low', 0):.2f}
   Close: ${data.get('close', 0):.2f}
   
🎨 Candle Properties:
   Color: {data.get('candle_color', 'unknown')}
   Body Ratio: {data.get('body_ratio', 0)*100:.1f}%
   Price Direction: {data.get('price_direction', 'unknown')}
   
📈 Volume Analysis:
   Current: {data.get('current_volume', 'N/A')}
   Average: {data.get('avg_volume', 'N/A')}
   Factor: {data.get('volume_factor', 'N/A')}
   
🧠 Analysis:
   Pattern: {data.get('pattern_name', 'Standard')}
   Strength: {data.get('analysis_strength', 0)*100:.1f}%
   Context: {data.get('market_context', 'Normal')}
"""
            
            self.update_candlestick_display(display_text)
            
        except Exception as e:
            self.log(f"❌ Candlestick data display error: {e}")
    
    def update_signal_display(self, signal_data: Dict):
        """อัพเดท Signal Display"""
        try:
            action = signal_data.get('action', 'WAIT')
            strength = signal_data.get('strength', 0) * 100
            
            # สี signal
            if action == 'BUY':
                color = "#00ff88"
                emoji = "🟢"
            elif action == 'SELL':
                color = "#ff6b6b" 
                emoji = "🔴"
            else:
                color = "#ffaa00"
                emoji = "⏳"
            
            # อัพเดท labels
            self.current_signal.config(text=f"{emoji} {action}", fg=color)
            self.signal_strength.config(text=f"Strength: {strength:.1f}%")
            
        except Exception as e:
            self.log(f"❌ Signal display error: {e}")
    
    def update_positions_display(self, positions: List[Dict]):
        """อัพเดท Positions Table"""
        try:
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            
            # Add positions
            for pos in positions:
                values = [
                    pos.get('id', ''),
                    pos.get('type', ''),
                    f"{pos.get('volume', 0):.2f}",
                    f"${pos.get('price_open', 0):.2f}",
                    f"${pos.get('price_current', 0):.2f}",
                    f"${pos.get('total_pnl', 0):.2f}",
                    pos.get('age', '')
                ]
                
                # สีตาม profit/loss
                tags = ()
                profit = pos.get('total_pnl', 0)
                if profit > 0:
                    tags = ('profit',)
                elif profit < 0:
                    tags = ('loss',)
                
                self.positions_tree.insert('', 'end', values=values, tags=tags)
            
            # Configure colors
            self.positions_tree.tag_configure('profit', foreground='#00ff88')
            self.positions_tree.tag_configure('loss', foreground='#ff6b6b')
            
        except Exception as e:
            self.log(f"❌ Positions display error: {e}")
    
    def update_performance_display(self, message: str):
        """อัพเดท Performance Display แบบง่าย"""
        try:
            self.performance_info.delete(1.0, tk.END)
            self.performance_info.insert(tk.END, message)
            self.performance_info.see(tk.END)
        except Exception as e:
            self.log(f"❌ Performance display error: {e}")
    
    def update_performance_display_from_data(self, data: Dict):
        """อัพเดท Performance Display จากข้อมูลจริง"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            display_text = f"""📊 PERFORMANCE METRICS [{timestamp}]
{'='*35}

🎯 Signal Statistics:
   Total Signals: {data.get('total_signals', 0)}
   Total Orders: {data.get('total_orders', 0)}
   Win Rate: {data.get('win_rate', 0)*100:.1f}%
   
💰 Trading Results:
   Total Profit: ${data.get('total_profit', 0):.2f}
   Winning Trades: {data.get('winning_trades', 0)}
   Losing Trades: {data.get('losing_trades', 0)}
   
🕯️ Candlestick Performance:
   Best Pattern: {data.get('best_pattern', 'N/A')}
   Execution Rate: {data.get('execution_rate', 0)*100:.1f}%
   Signal Accuracy: {data.get('signal_accuracy', 0)*100:.1f}%
   
⚡ Execution Metrics:
   Avg Execution Time: {data.get('avg_execution_time_ms', 0):.0f}ms
   Signals/Hour: {data.get('signals_per_hour', 0):.1f}
"""
            
            self.update_performance_display(display_text)
            
        except Exception as e:
            self.log(f"❌ Performance data display error: {e}")
    
    # ==========================================
    # 🎮 CONTROL METHODS
    # ==========================================
    
    def close_selected_position(self):
        """ปิดออเดอร์ที่เลือก"""
        try:
            selection = self.positions_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select position to close")
                return
            
            item = self.positions_tree.item(selection[0])
            position_id = item['values'][0]
            
            self.log(f"❌ Closing position #{position_id}...")
            
            if self.position_monitor:
                success = self.position_monitor.close_position_by_id(int(position_id), "Manual Close")
                if success:
                    self.log(f"✅ Position #{position_id} closed successfully")
                else:
                    self.log(f"❌ Failed to close position #{position_id}")
            
        except Exception as e:
            self.log(f"❌ Close position error: {e}")
    
    def emergency_close_all(self):
        """ปิดออเดอร์ทั้งหมดทันที - Emergency"""
        try:
            result = messagebox.askyesno(
                "🚨 Emergency Close", 
                "Close ALL positions immediately?\n\nThis action cannot be undone!"
            )
            
            if not result:
                return
                
            self.log("🚨 EMERGENCY CLOSE ALL POSITIONS!")
            
            if self.position_monitor:
                closed_count = self.position_monitor.emergency_close_all()
                self.log(f"🚨 Emergency closed {closed_count} positions")
            
            # Stop trading
            if self.is_trading:
                self.stop_trading()
                
        except Exception as e:
            self.log(f"❌ Emergency close error: {e}")
    
    # ==========================================
    # 📝 UTILITY METHODS (FIXED)
    # ==========================================
    
    def log(self, message: str):
        """🔧 FIXED: เขียน log ลงหน้าจอ"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"
            
            # 🔧 FIXED: ตรวจสอบว่า log_text พร้อมใช้งานหรือไม่
            if hasattr(self, 'log_text') and self.log_text:
                # Add to GUI
                self.log_text.insert(tk.END, log_message)
                self.log_text.see(tk.END)
                
                # Keep only last 100 lines
                lines = self.log_text.get(1.0, tk.END).split('\n')
                if len(lines) > 100:
                    self.log_text.delete(1.0, f"{len(lines)-100}.0")
            
            # Print to console (always work)
            print(log_message.strip())
            
        except Exception as e:
            # Fallback to console
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            print(f"Log error: {e}")
    
    def start_gui_updates(self):
        """เริ่ม GUI update loop"""
        def update_loop():
            while True:
                try:
                    # Update GUI ทุก 1 วินาที
                    time.sleep(1)
                except Exception as e:
                    self.log(f"❌ GUI update error: {e}")
        
        # เริ่ม background thread
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def on_closing(self):
        """เมื่อปิดโปรแกรม"""
        try:
            self.log("🔒 Shutting down Pure Candlestick Trading System...")
            
            # หยุด trading
            if self.is_trading:
                self.stop_trading()
                time.sleep(1)  # รอให้หยุด
            
            # ตัดการเชื่อมต่อ
            if self.mt5_connector.is_connected:
                self.disconnect_mt5()
            
            # ปิดโปรแกรม
            self.root.destroy()
            
        except Exception as e:
            print(f"Shutdown error: {e}")
            self.root.destroy()

# ==========================================
# 🚀 APPLICATION ENTRY POINT
# ==========================================

def main():
    """เริ่มต้นโปรแกรม Pure Candlestick Trading System"""
    
    print("🕯️ Pure Candlestick Trading System")
    print("=" * 50)
    print("🚀 Starting application...")
    
    # Create GUI
    root = tk.Tk()
    app = PureCandlestickGUI(root)
    
    # Handle window close
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start GUI
    try:
        print("✅ GUI started successfully")
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        app.on_closing()
    except Exception as e:
        print(f"❌ GUI error: {e}")

if __name__ == "__main__":
    main()