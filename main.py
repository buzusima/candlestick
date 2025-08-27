"""
🎮 Enhanced Pure Candlestick Trading System - LOT-AWARE GUI
main.py

🔧 ENHANCED FEATURES:
✅ Lot Efficiency Display
✅ Margin Usage Visualization
✅ Volume Balance Indicator
✅ Enhanced Position Table
✅ Smart Close Recommendations

🆕 NEW DISPLAYS:
💰 Profit Per Lot Column
📊 Margin Efficiency Indicator  
⚖️ Portfolio Balance Chart
🎯 Close Priority Display
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import ระบบเดิม (mt5_connector + api_connector คงเดิม)
from mt5_connector import MT5Connector
from api_connector import BackendAPIConnector

# Import ระบบ Pure Candlestick ใหม่
from candlestick_analyzer import CandlestickAnalyzer
from signal_generator import SignalGenerator
from order_executor import OrderExecutor
from performance_tracker import PerformanceTracker
from risk_manager import RiskManager
from data_persistence import create_persistence_manager, integrate_with_analyzer, integrate_with_generator
from position_monitor import PositionMonitor

class EnhancedPureCandlestickGUI:
    """
    🎮 Enhanced Pure Candlestick GUI - LOT-AWARE VERSION
    
    🆕 Features:
    - Lot efficiency display
    - Margin optimization visualization
    - Volume balance monitoring  
    - Enhanced close recommendations
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("🕯️ Enhanced Pure Candlestick Trading System v2.0 (Lot-Aware)")
        self.root.geometry("1500x900")  # ขยายหน้าจอเพื่อแสดงข้อมูลเพิ่ม
        self.root.configure(bg="#1a1a1a")
        
        # ตัวแปรระบบ (เดิม)
        self.config = self.load_config()
        self.is_trading = False
        self.trading_thread = None
        
        # Initialize Components (เดิม)
        self.mt5_connector = MT5Connector()
        self.api_connector = None
        self.candlestick_analyzer = None
        self.signal_generator = None  
        self.order_executor = None
        self.position_monitor = None  # จะใช้ enhanced version
        self.performance_tracker = None
        self.risk_manager = None
        self.persistence_manager = None

        # 🆕 Enhanced GUI variables
        self.lot_efficiency_data = {}
        self.margin_analysis_data = {}
        self.portfolio_health_score = 0.0
        
        # Setup GUI
        self.setup_enhanced_gui()
        self.start_gui_updates()
        
        # Log system start
        self.log("🚀 Enhanced Pure Candlestick Trading System Started")
        self.log("🔍 Scanning for MT5 terminals...")
        self.initialize_persistence()

        # Auto scan
        self.scan_mt5_terminals()
    
    def load_config(self) -> Dict:
        """โหลดการตั้งค่าจากไฟล์ - เก็บเดิม"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("✅ Enhanced configuration loaded successfully")
                return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            # Return enhanced default config
            return {
                "trading": {"symbol": "XAUUSD.v", "timeframe": "M1"},
                "position_management": {
                    "min_efficiency_per_lot": 50.0,
                    "volume_balance_tolerance": 0.3,
                    "partial_close_enabled": True,
                    "margin_optimization": {"enabled": True}
                },
                "lot_sizing": {"base_lot": 0.01},
                "risk_management": {"max_positions": 50}
            }
    
    def setup_enhanced_gui(self):
        """สร้าง Enhanced GUI Layout - LOT-AWARE VERSION"""
        
        # ==========================================
        # 🎯 HEADER SECTION (เก็บเดิม)
        # ==========================================
        header_frame = tk.Frame(self.root, bg="#2d2d2d", height=60)
        header_frame.pack(fill="x", padx=5, pady=2)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, text="🕯️ Enhanced Pure Candlestick Trading (Lot-Aware)", 
            font=("Arial", 16, "bold"), fg="white", bg="#2d2d2d"
        )
        title_label.pack(side="left", padx=10, pady=15)
        
        self.status_label = tk.Label(
            header_frame, text="🔍 Scanning...", 
            font=("Arial", 10), fg="#00ff88", bg="#2d2d2d"
        )
        self.status_label.pack(side="right", padx=10, pady=15)
        
        # ==========================================
        # 🔍 MT5 CONNECTION SECTION (เก็บเดิม)
        # ==========================================
        connection_frame = tk.LabelFrame(
            self.root, text="🔍 MT5 Terminal & Account Selection", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333"
        )
        connection_frame.pack(fill="x", padx=5, pady=2)
        
        # MT5 Terminals + Controls (เก็บ logic เดิม)
        self._setup_mt5_connection_panel(connection_frame)
        
        # ==========================================
        # 📊 ENHANCED DASHBOARD
        # ==========================================
        dashboard_frame = tk.Frame(self.root, bg="#1a1a1a")
        dashboard_frame.pack(fill="both", expand=True, padx=5, pady=2)
        
        # Left Panel - Candlestick + Portfolio Health
        left_panel = tk.LabelFrame(
            dashboard_frame, text="🕯️ Analysis & Portfolio Health", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333", width=450
        )
        left_panel.pack(side="left", fill="both", expand=False, padx=2, pady=2)
        left_panel.pack_propagate(False)
        
        # Candlestick Info (เดิม)
        self.candlestick_info = scrolledtext.ScrolledText(
            left_panel, height=6, font=("Consolas", 9),
            bg="#2a2a2a", fg="#00ff88", wrap="word"
        )
        self.candlestick_info.pack(fill="x", padx=5, pady=3)
        
        # 🆕 Portfolio Health Panel
        health_frame = tk.LabelFrame(
            left_panel, text="🏥 Portfolio Health", 
            font=("Arial", 9, "bold"), fg="white", bg="#333333"
        )
        health_frame.pack(fill="x", padx=5, pady=3)
        
        self.health_score_label = tk.Label(
            health_frame, text="Health Score: 0.00", 
            font=("Arial", 11, "bold"), fg="#00ff88", bg="#333333"
        )
        self.health_score_label.pack(pady=2)
        
        # Volume Balance Indicator
        balance_frame = tk.Frame(health_frame, bg="#333333")
        balance_frame.pack(fill="x", padx=5, pady=2)
        
        tk.Label(balance_frame, text="Volume Balance:", 
                fg="white", bg="#333333", font=("Arial", 8)).pack(side="left")
        
        self.volume_balance_label = tk.Label(
            balance_frame, text="BUY: 0.00 | SELL: 0.00", 
            font=("Consolas", 8), fg="#ffaa00", bg="#333333"
        )
        self.volume_balance_label.pack(side="right")
        
        # 🆕 Margin Efficiency Indicator
        margin_frame = tk.Frame(health_frame, bg="#333333")
        margin_frame.pack(fill="x", padx=5, pady=2)
        
        tk.Label(margin_frame, text="Margin Efficiency:", 
                fg="white", bg="#333333", font=("Arial", 8)).pack(side="left")
        
        self.margin_efficiency_label = tk.Label(
            margin_frame, text="0.0000", 
            font=("Consolas", 8), fg="#ffaa00", bg="#333333"
        )
        self.margin_efficiency_label.pack(side="right")
        
        # Signal Panel (เดิม)
        self._setup_signal_panel(left_panel)
        
        # Trading Controls (เดิม)
        self._setup_trading_controls(left_panel)
        
        # Right Panel - Enhanced Positions & Performance
        right_panel = tk.Frame(dashboard_frame, bg="#1a1a1a")
        right_panel.pack(side="right", fill="both", expand=True, padx=2, pady=2)
        
        # 🆕 Enhanced Positions Panel
        positions_frame = tk.LabelFrame(
            right_panel, text="💰 Enhanced Positions (Lot-Aware)", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333"
        )
        positions_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # 🆕 Enhanced Headers
        headers_frame = tk.Frame(positions_frame, bg="#333333")
        headers_frame.pack(fill="x", padx=5, pady=2)
        
        # เพิ่ม columns สำหรับ lot analysis
        enhanced_headers = ["ID", "Type", "Lots", "P&L", "$/Lot", "Efficiency", "Age", "Priority"]
        for i, header in enumerate(enhanced_headers):
            width = 8 if header in ["ID", "Type", "Age"] else 10
            label = tk.Label(headers_frame, text=header, font=("Arial", 9, "bold"), 
                           fg="white", bg="#333333", width=width)
            label.grid(row=0, column=i, padx=1, sticky="w")
        
        # 🆕 Enhanced Positions Treeview
        self.positions_tree = ttk.Treeview(
            positions_frame, columns=enhanced_headers, show="tree", height=12
        )
        self.positions_tree.pack(fill="both", expand=True, padx=5, pady=2)
        
        # Configure enhanced columns
        column_widths = [60, 45, 60, 80, 70, 90, 70, 60]  # ปรับให้พอดี
        for i, (header, width) in enumerate(zip(enhanced_headers, column_widths)):
            self.positions_tree.heading(f"#{i+1}", text=header)
            self.positions_tree.column(f"#{i+1}", width=width, anchor="center")
        
        # 🆕 Enhanced Position Controls
        self._setup_enhanced_position_controls(positions_frame)
        
        # 🆕 Close Recommendations Panel
        recommendations_frame = tk.LabelFrame(
            right_panel, text="🧠 Smart Close Recommendations", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333"
        )
        recommendations_frame.pack(fill="x", padx=2, pady=2)
        
        self.recommendations_text = scrolledtext.ScrolledText(
            recommendations_frame, height=4, font=("Consolas", 8),
            bg="#2a2a2a", fg="#ffaa00", wrap="word"
        )
        self.recommendations_text.pack(fill="x", padx=5, pady=3)
        
        # Performance Panel (เก็บเดิมแต่ปรับขนาด)
        performance_frame = tk.LabelFrame(
            right_panel, text="📊 Performance & Efficiency Metrics", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333"
        )
        performance_frame.pack(fill="x", padx=2, pady=2)
        
        self.performance_info = scrolledtext.ScrolledText(
            performance_frame, height=5, font=("Consolas", 9),
            bg="#2a2a2a", fg="#00aaff", wrap="word"
        )
        self.performance_info.pack(fill="x", padx=5, pady=3)
        
        # ==========================================
        # 📝 LOG PANEL (เก็บเดิม)
        # ==========================================
        log_frame = tk.LabelFrame(
            self.root, text="📝 System Log", 
            font=("Arial", 10, "bold"), fg="white", bg="#333333"
        )
        log_frame.pack(fill="x", padx=5, pady=2)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=6, font=("Consolas", 9),
            bg="#1a1a1a", fg="#cccccc", wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=3)
        
        # Initialize displays
        self.update_candlestick_display("⏳ Waiting for connection...")
        self.update_performance_display("📊 No data available")
        self.update_recommendations_display("🧠 No recommendations yet")
    
    def _setup_mt5_connection_panel(self, parent_frame):
        """🔍 Setup MT5 Connection Panel - เก็บเดิม"""
        
        # MT5 Terminals List
        terminals_frame = tk.Frame(parent_frame, bg="#333333")
        terminals_frame.pack(fill="x", padx=5, pady=3)
        
        tk.Label(terminals_frame, text="📟 Available MT5 Terminals:", 
                fg="white", bg="#333333").pack(anchor="w")
        
        self.terminals_listbox = tk.Listbox(
            terminals_frame, height=3, font=("Consolas", 9),
            bg="#404040", fg="white", selectbackground="#0066cc"
        )
        self.terminals_listbox.pack(fill="x", pady=2)
        
        # MT5 Control Buttons
        mt5_buttons_frame = tk.Frame(parent_frame, bg="#333333")
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
        accounts_frame = tk.Frame(parent_frame, bg="#333333")
        accounts_frame.pack(fill="x", padx=5, pady=3)
        
        tk.Label(accounts_frame, text="👤 Trading Accounts:", 
                fg="white", bg="#333333").pack(anchor="w")
        
        self.accounts_listbox = tk.Listbox(
            accounts_frame, height=2, font=("Consolas", 9),
            bg="#404040", fg="white", selectbackground="#0066cc"
        )
        self.accounts_listbox.pack(fill="x", pady=2)
    
    def _setup_signal_panel(self, parent_frame):
        """🎯 Setup Signal Panel - เก็บเดิม"""
        signal_frame = tk.Frame(parent_frame, bg="#333333")
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
    
    def _setup_trading_controls(self, parent_frame):
        """🎮 Setup Trading Controls - เก็บเดิม"""
        controls_frame = tk.Frame(parent_frame, bg="#333333")
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
    
    def _setup_enhanced_position_controls(self, parent_frame):
        """💰 Setup Enhanced Position Controls"""
        position_controls = tk.Frame(parent_frame, bg="#333333")
        position_controls.pack(fill="x", padx=5, pady=3)
        
        # Row 1: Basic Controls
        basic_controls = tk.Frame(position_controls, bg="#333333")
        basic_controls.pack(fill="x", pady=1)
        
        self.close_selected_button = tk.Button(
            basic_controls, text="❌ Close Selected", 
            command=self.close_selected_position,
            bg="#ff9500", fg="white", font=("Arial", 8)
        )
        self.close_selected_button.pack(side="left", padx=2)
        
        self.close_all_button = tk.Button(
            basic_controls, text="🚨 Emergency Close All", 
            command=self.emergency_close_all,
            bg="#ff3333", fg="white", font=("Arial", 8)
        )
        self.close_all_button.pack(side="right", padx=2)
        
        # Row 2: Enhanced Controls
        enhanced_controls = tk.Frame(position_controls, bg="#333333")
        enhanced_controls.pack(fill="x", pady=1)
        
        self.optimize_margin_button = tk.Button(
            enhanced_controls, text="🔧 Optimize Margin", 
            command=self.execute_margin_optimization,
            bg="#4a90e2", fg="white", font=("Arial", 8)
        )
        self.optimize_margin_button.pack(side="left", padx=1)
        
        self.balance_volume_button = tk.Button(
            enhanced_controls, text="⚖️ Balance Volume", 
            command=self.execute_volume_balance,
            bg="#9966cc", fg="white", font=("Arial", 8)
        )
        self.balance_volume_button.pack(side="left", padx=1)
        
        self.smart_recovery_button = tk.Button(
            enhanced_controls, text="🎯 Smart Recovery", 
            command=self.execute_smart_recovery,
            bg="#ff6600", fg="white", font=("Arial", 8)
        )
        self.smart_recovery_button.pack(side="left", padx=1)
        
        self.refresh_analysis_button = tk.Button(
            enhanced_controls, text="🔄 Refresh Analysis", 
            command=self.refresh_lot_analysis,
            bg="#666666", fg="white", font=("Arial", 8)
        )
        self.refresh_analysis_button.pack(side="right", padx=1)
    
    # ==========================================
    # 🔍 MT5 CONNECTION METHODS (เก็บเดิมทั้งหมด)
    # ==========================================
    
    def scan_mt5_terminals(self):
        """สแกนหา MT5 terminals - เก็บเดิม"""
        try:
            self.log("🔍 Scanning for MT5 terminals...")
            
            self.terminals_listbox.delete(0, tk.END)
            self.accounts_listbox.delete(0, tk.END)
            
            installations = self.mt5_connector.find_running_mt5_installations()
            
            if not installations:
                self.log("❌ No running MT5 terminals found")
                self.terminals_listbox.insert(0, "❌ No MT5 terminals running")
                return
            
            self.log(f"✅ Found {len(installations)} MT5 terminal(s)")
            
            for i, inst in enumerate(installations):
                exe_type = "64-bit" if "64" in inst.executable_type else "32-bit"
                display_text = f"{i}: 🟢 {inst.broker} ({exe_type})"
                self.terminals_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            self.log(f"❌ MT5 scan error: {e}")
    
    def connect_mt5(self):
        """เชื่อมต่อ MT5 - เก็บเดิม"""
        try:
            selection = self.terminals_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select MT5 terminal first")
                return
            
            terminal_index = selection[0]
            self.log(f"🔗 Connecting to MT5 terminal #{terminal_index}...")
            
            if self.mt5_connector.connect_to_installation(terminal_index):
                self.log("✅ MT5 connection successful")
                self.status_label.config(text="🟢 MT5 Connected", fg="#00ff88")
                
                self.connect_button.config(state="disabled")
                self.disconnect_button.config(state="normal")
                self.start_button.config(state="normal")
                
                self.load_accounts()
                self.initialize_trading_components()
                
            else:
                self.log("❌ MT5 connection failed")
                
        except Exception as e:
            self.log(f"❌ MT5 connection error: {e}")
    
    def disconnect_mt5(self):
        """ตัดการเชื่อมต่อ MT5 - เก็บเดิม"""
        try:
            self.log("🔌 Disconnecting from MT5...")
            
            if self.is_trading:
                self.stop_trading()
            
            if self.mt5_connector.disconnect():
                self.log("✅ MT5 disconnected successfully")
                self.status_label.config(text="🔍 Disconnected", fg="#ffaa00")
                
                self.connect_button.config(state="normal")
                self.disconnect_button.config(state="disabled") 
                self.start_button.config(state="disabled")
                self.stop_button.config(state="disabled")
                
                self.accounts_listbox.delete(0, tk.END)
                self.update_candlestick_display("⏳ Waiting for connection...")
                self.update_enhanced_positions_display([])
                self.update_performance_display("📊 No data available")
            
        except Exception as e:
            self.log(f"❌ MT5 disconnect error: {e}")
    
    def load_accounts(self):
        """โหลดรายการบัญชี - เก็บเดิม"""
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
    # 🔧 COMPONENT INITIALIZATION (เก็บเดิม + เพิ่ม enhanced)
    # ==========================================
    
    def initialize_persistence(self):
        """🆕 เริ่มต้น Data Persistence - เก็บเดิม"""
        try:
            self.log("💾 Initializing Data Persistence Manager...")
            
            self.persistence_manager = create_persistence_manager()
            
            session_info = self.persistence_manager.load_session_info()
            if session_info:
                self.log(f"📂 Loaded previous session data")
                
            performance_data = self.persistence_manager.load_performance_data()
            if performance_data:
                self.log(f"📈 Loaded performance history: {performance_data.get('total_signals', 0)} signals")
            
            self.log("✅ Data Persistence Manager ready")
            
        except Exception as e:
            self.log(f"❌ Persistence initialization error: {e}")
            self.persistence_manager = None

    def initialize_trading_components(self):
        """เริ่มต้น Enhanced Trading Components"""
        try:
            self.log("🕯️ Initializing Enhanced Pure Candlestick components...")
            
            if not self.mt5_connector.is_connected:
                self.log("❌ MT5 not connected - cannot initialize components")
                return
            
            # Initialize components
            self.candlestick_analyzer = CandlestickAnalyzer(self.mt5_connector, self.config)
            self.signal_generator = SignalGenerator(self.candlestick_analyzer, self.config)
            self.order_executor = OrderExecutor(self.mt5_connector, self.config)
            
            # 🆕 Use Enhanced Position Monitor
            self.position_monitor = PositionMonitor(self.mt5_connector, self.config)            
            self.performance_tracker = PerformanceTracker(self.config)
            self.risk_manager = RiskManager(self.mt5_connector, self.config)
            
            # Persistence integration
            if self.persistence_manager:
                self.log("🔗 Integrating persistence with components...")
                integrate_with_analyzer(self.candlestick_analyzer, self.persistence_manager)
                integrate_with_generator(self.signal_generator, self.persistence_manager)
                self.log("✅ Persistence integration completed")
            
            self.log("✅ All Enhanced Pure Candlestick components initialized")
            self.log("🆕 Lot-aware analysis enabled")
            
        except Exception as e:
            self.log(f"❌ Component initialization error: {e}")
            
    def execute_margin_optimization(self):
        """🔧 Optimize Margin"""
        if self.position_monitor:
            self.position_monitor.execute_close_action({'action_type': 'margin_optimization'})
        else:
            messagebox.showwarning("Warning", "Position Monitor not initialized")

    def execute_volume_balance(self):
        """⚖️ Balance Volume"""  
        if self.position_monitor:
            self.position_monitor.execute_close_action({'action_type': 'volume_balance'})
        else:
            messagebox.showwarning("Warning", "Position Monitor not initialized")
            
    def execute_smart_recovery(self):
        """🎯 Smart Recovery"""
        if self.position_monitor:
            self.position_monitor.execute_close_action({'action_type': 'lot_aware_recovery'})
        else:
            messagebox.showwarning("Warning", "Position Monitor not initialized")

    def refresh_lot_analysis(self):
        """🔄 Refresh Analysis"""
        if self.position_monitor:
            self.position_monitor.force_lot_aware_analysis()
            self.log("🔄 Lot analysis refreshed")
        else:
            messagebox.showwarning("Warning", "Position Monitor not initialized")

    # ==========================================
    # 🎮 ENHANCED TRADING METHODS
    # ==========================================
    
    def start_trading(self):
        """🚀 เริ่ม Enhanced Trading - เก็บ logic เดิม"""
        try:
            if self.is_trading:
                self.log("⚠️ Trading is already running")
                return
            
            if not self.mt5_connector.is_connected:
                messagebox.showwarning("Warning", "Please connect to MT5 first")
                return
            
            self.log("🚀 Starting Enhanced Pure Candlestick Trading...")
            self.is_trading = True
            
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal") 
            self.status_label.config(text="🟢 Enhanced Trading Active", fg="#00ff88")
            
            self.trading_thread = threading.Thread(target=self.enhanced_trading_loop, daemon=True)
            self.trading_thread.start()
            
            self.log("✅ Enhanced Pure Candlestick Trading started")
            
        except Exception as e:
            self.log(f"❌ Start trading error: {e}")
            self.is_trading = False
    
    def enhanced_trading_loop(self):
        """🔄 Enhanced Trading Loop - เพิ่ม lot-aware analysis"""
        self.log("🔄 Enhanced trading loop started")
        
        while self.is_trading:
            try:
                # 1. วิเคราะห์แท่งเทียน (เดิม)
                if self.candlestick_analyzer:
                    candlestick_data = self.candlestick_analyzer.get_current_analysis()
                    
                    if not candlestick_data:
                        time.sleep(3)
                        continue
                    
                    self.update_candlestick_display_from_data(candlestick_data)
                    
                    # 2. สร้าง signal (เดิม)
                    if self.signal_generator:
                        signal_data = self.signal_generator.generate_signal(candlestick_data)
                        
                        if signal_data and signal_data.get('action') != 'WAIT':
                            self.update_signal_display(signal_data)
                            
                            if self.performance_tracker:
                                self.performance_tracker.record_signal(signal_data)
                            
                            # 3. ส่งออเดอร์ (เดิม)
                            if self.order_executor:
                                execution_result = self.order_executor.execute_signal(signal_data)
                                
                                if execution_result:
                                    self.log(f"Order executed: {signal_data.get('action')} - {execution_result.get('success', False)}")
                                    
                                    if self.performance_tracker:
                                        self.performance_tracker.record_execution(execution_result, signal_data)
                
                # 🆕 4. Enhanced Position Monitoring
                if self.position_monitor:
                    positions = self.position_monitor.get_all_positions()
                    self.update_enhanced_positions_display(positions)
                    
                    # 🆕 Enhanced Close Analysis
                    close_actions = self.position_monitor.check_smart_close_opportunities()
                    if close_actions:
                        self.log(f"🧠 Found {len(close_actions)} enhanced close opportunities")
                        self.update_recommendations_display_from_data(close_actions)
                        
                        # ดำเนินการ close ตาม priority
                        for action in close_actions[:2]:  # ทำแค่ 2 actions ต่อ cycle
                            if self.position_monitor.execute_close_action(action):
                                self.log(f"✅ Enhanced close executed: {action.get('action_type')}")
                
                # 🆕 5. Enhanced Performance Update
                if self.performance_tracker:
                    performance = self.performance_tracker.get_current_metrics()
                    
                    # เพิ่ม lot efficiency data
                    if self.position_monitor:
                        lot_efficiency = self.position_monitor.get_lot_efficiency_report()
                        performance['lot_efficiency'] = lot_efficiency
                    
                    self.update_enhanced_performance_display(performance)
                
                # 6. Risk Management (เดิม)
                if self.risk_manager:
                    risk_status = self.risk_manager.check_risk_levels()
                    if risk_status.get('emergency_stop', False):
                        self.log("🚨 EMERGENCY STOP triggered by risk manager!")
                        self.emergency_close_all()
                        break
                
                time.sleep(3)  # ทุก 3 วินาที
                
            except Exception as e:
                self.log(f"❌ Enhanced trading loop error: {e}")
                time.sleep(5)
        
        self.log("🔄 Enhanced trading loop ended")
    
    # ==========================================
    # 📊 ENHANCED DISPLAY UPDATE METHODS
    # ==========================================
    
    def update_enhanced_positions_display(self, positions: List[Dict]):
        """💰 อัพเดท Enhanced Positions Table"""
        try:
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            
            # Add enhanced position data
            for pos in positions:
                values = [
                    pos.get('id', ''),
                    pos.get('type', ''),
                    f"{pos.get('volume', 0):.2f}",
                    f"${pos.get('total_pnl', 0):.2f}",
                    f"${pos.get('profit_per_lot', 0):.0f}",  # 🆕 Profit per lot
                    pos.get('efficiency_category', 'unknown'),  # 🆕 Efficiency category
                    pos.get('age', ''),
                    f"{pos.get('close_priority', 0):.2f}"  # 🆕 Close priority
                ]
                
                # 🆕 Enhanced color coding
                tags = []
                efficiency = pos.get('efficiency_category', '')
                profit = pos.get('total_pnl', 0)
                
                if efficiency == 'excellent':
                    tags = ['excellent']
                elif efficiency == 'good':
                    tags = ['good']
                elif efficiency in ['poor', 'terrible']:
                    tags = ['poor']
                elif profit > 0:
                    tags = ['profit']
                elif profit < 0:
                    tags = ['loss']
                
                self.positions_tree.insert('', 'end', values=values, tags=tags)
            
            # 🆕 Enhanced color configuration
            self.positions_tree.tag_configure('excellent', foreground='#00ff00', background='#003300')
            self.positions_tree.tag_configure('good', foreground='#00ff88')
            self.positions_tree.tag_configure('profit', foreground='#88ff88')
            self.positions_tree.tag_configure('loss', foreground='#ff6b6b')
            self.positions_tree.tag_configure('poor', foreground='#ff3333', background='#330000')
            
            # 🆕 Update portfolio health indicator
            if self.position_monitor:
                portfolio_summary = self.position_monitor.get_enhanced_portfolio_summary()
                health_score = portfolio_summary.get('portfolio_health_score', 0)
                
                self.portfolio_health_score = health_score
                health_color = self._get_health_color(health_score)
                
                self.health_score_label.config(
                    text=f"Health Score: {health_score:.2f}",
                    fg=health_color
                )
                
                # Update volume balance
                buy_volume = portfolio_summary.get('total_buy_volume', 0)
                sell_volume = portfolio_summary.get('total_sell_volume', 0)
                self.volume_balance_label.config(
                    text=f"BUY: {buy_volume:.2f} | SELL: {sell_volume:.2f}"
                )
                
                # Update margin efficiency
                margin_efficiency = portfolio_summary.get('avg_margin_efficiency', 0)
                self.margin_efficiency_label.config(
                    text=f"{margin_efficiency:.4f}"
                )
            
        except Exception as e:
            self.log(f"❌ Enhanced positions display error: {e}")
    
    def _get_health_color(self, score: float) -> str:
        """🎨 เลือกสีตาม Health Score"""
        if score >= 0.8:
            return "#00ff88"  # เขียว
        elif score >= 0.6:
            return "#ffaa00"  # ส้ม
        elif score >= 0.4:
            return "#ff6600"  # ส้มแดง
        else:
            return "#ff3333"  # แดง
    
    def update_recommendations_display_from_data(self, close_actions: List[Dict]):
        """🧠 อัพเดท Close Recommendations Display"""
        try:
            if not close_actions:
                self.update_recommendations_display("🧠 No close recommendations")
                return
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            display_text = f"🧠 CLOSE RECOMMENDATIONS [{timestamp}]\n"
            display_text += "=" * 45 + "\n\n"
            
            for i, action in enumerate(close_actions[:5], 1):  # แสดง 5 อันดับแรก
                action_type = action.get('action_type', 'unknown')
                priority = action.get('priority', 10)
                reason = action.get('reason', '')
                
                # Icon ตาม action type
                if action_type == 'margin_optimization':
                    icon = "🔧"
                elif action_type == 'volume_balance':
                    icon = "⚖️"
                elif action_type == 'lot_aware_recovery':
                    icon = "🎯"
                elif action_type == 'enhanced_profit_target':
                    icon = "💰"
                else:
                    icon = "📋"
                
                display_text += f"{i}. {icon} {action_type.replace('_', ' ').title()}\n"
                display_text += f"   Priority: {priority} | {reason}\n"
                
                # แสดงรายละเอียดเพิ่มตาม type
                if 'net_profit' in action:
                    display_text += f"   Net Result: ${action.get('net_profit', 0):.2f}\n"
                
                if 'margin_freed' in action:
                    display_text += f"   Margin Freed: ${action.get('margin_freed', 0):.0f}\n"
                    
                if 'volume_match_ratio' in action:
                    display_text += f"   Volume Match: {action.get('volume_match_ratio', 0):.1%}\n"
                
                display_text += "\n"
            
            self.update_recommendations_display(display_text)
            
        except Exception as e:
            self.log(f"❌ Recommendations display error: {e}")
    
    def update_enhanced_performance_display(self, data: Dict):
        """📊 อัพเดท Enhanced Performance Display"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            display_text = f"📊 ENHANCED PERFORMANCE [{timestamp}]\n"
            display_text += "=" * 40 + "\n\n"
            
            # 🆕 Lot Efficiency Section
            lot_efficiency = data.get('lot_efficiency', {})
            if 'efficiency_breakdown' in lot_efficiency:
                display_text += "🔢 LOT EFFICIENCY BREAKDOWN:\n"
                
                breakdown = lot_efficiency['efficiency_breakdown']
                for category, stats in breakdown.items():
                    if stats:
                        display_text += f"   {category.title()}: {stats['count']} pos "
                        display_text += f"({stats['total_volume']:.2f} lots, "
                        display_text += f"${stats['avg_efficiency']:.0f}/lot)\n"
                display_text += "\n"
            
            # Trading Results (เดิม)
            display_text += "💰 TRADING RESULTS:\n"
            display_text += f"   Total Profit: ${data.get('total_profit', 0):.2f}\n"
            display_text += f"   Win Rate: {data.get('win_rate', 0)*100:.1f}%\n"
            display_text += f"   Total Orders: {data.get('total_orders', 0)}\n\n"
            
            # 🆕 Portfolio Health
            portfolio_health = self.portfolio_health_score
            display_text += f"🏥 PORTFOLIO HEALTH: {portfolio_health:.2f}\n"
            
            if portfolio_health >= 0.8:
                display_text += "   Status: 🟢 Excellent\n"
            elif portfolio_health >= 0.6:
                display_text += "   Status: 🟡 Good\n"
            elif portfolio_health >= 0.4:
                display_text += "   Status: 🟠 Fair\n"
            else:
                display_text += "   Status: 🔴 Needs Attention\n"
            
            display_text += "\n"
            
            # Execution Stats (เดิม)
            display_text += "⚡ EXECUTION STATS:\n"
            display_text += f"   Avg Execution: {data.get('avg_execution_time_ms', 0):.0f}ms\n"
            display_text += f"   Success Rate: {data.get('execution_rate', 0)*100:.1f}%\n"
            
            self.update_performance_display(display_text)
            
        except Exception as e:
            self.log(f"❌ Enhanced performance display error: {e}")
    
    # ==========================================
    # 🆕 NEW ENHANCED CONTROL METHODS
    # ==========================================
    
    def execute_margin_optimization(self):
        """🔧 Execute Margin Optimization"""
        try:
            if not self.position_monitor:
                messagebox.showwarning("Warning", "Position Monitor not initialized")
                return
            
            self.log("🔧 Executing margin optimization...")
            
            # หา margin optimization opportunities
            opportunities = self.position_monitor.check_smart_close_opportunities()
            margin_ops = [op for op in opportunities if op.get('action_type') == 'margin_optimization']
            
            if not margin_ops:
                messagebox.showinfo("Info", "No margin optimization opportunities found")
                return
            
            # Execute top margin optimization
            success = self.position_monitor.execute_close_action(margin_ops[0])
            
            if success:
                self.log("✅ Margin optimization executed successfully")
                margin_freed = margin_ops[0].get('margin_freed', 0)
                messagebox.showinfo("Success", f"Margin optimization completed!\nMargin freed: ${margin_freed:.0f}")
            else:
                self.log("❌ Margin optimization failed")
                messagebox.showerror("Error", "Margin optimization failed")
                
        except Exception as e:
            self.log(f"❌ Margin optimization error: {e}")
    
    def execute_volume_balance(self):
        """⚖️ Execute Volume Balance"""
        try:
            if not self.position_monitor:
                messagebox.showwarning("Warning", "Position Monitor not initialized")
                return
            
            self.log("⚖️ Executing volume balance...")
            
            # หา volume balance opportunities
            opportunities = self.position_monitor.check_smart_close_opportunities()
            balance_ops = [op for op in opportunities if op.get('action_type') == 'volume_balance']
            
            if not balance_ops:
                messagebox.showinfo("Info", "Portfolio volume is already balanced")
                return
            
            # Execute top volume balance
            success = self.position_monitor.execute_close_action(balance_ops[0])
            
            if success:
                self.log("✅ Volume balance executed successfully")
                volume_closed = balance_ops[0].get('volume_to_close', 0)
                messagebox.showinfo("Success", f"Volume balance completed!\nVolume balanced: {volume_closed:.2f} lots")
            else:
                self.log("❌ Volume balance failed")
                messagebox.showerror("Error", "Volume balance failed")
                
        except Exception as e:
            self.log(f"❌ Volume balance error: {e}")
    
    def execute_smart_recovery(self):
        """🎯 Execute Smart Recovery"""
        try:
            if not self.position_monitor:
                messagebox.showwarning("Warning", "Position Monitor not initialized") 
                return
            
            self.log("🎯 Executing smart recovery...")
            
            # หา recovery opportunities
            opportunities = self.position_monitor.check_smart_close_opportunities()
            recovery_ops = [op for op in opportunities if op.get('action_type') == 'lot_aware_recovery']
            
            if not recovery_ops:
                messagebox.showinfo("Info", "No smart recovery opportunities found")
                return
            
            # แสดงรายละเอียดให้ user เลือก
            top_recovery = recovery_ops[0]
            net_profit = top_recovery.get('net_profit', 0)
            volume_match = top_recovery.get('volume_match_ratio', 0)
            
            result = messagebox.askyesno(
                "🎯 Smart Recovery",
                f"Execute smart recovery?\n\n"
                f"Net Result: ${net_profit:.2f}\n"
                f"Volume Match: {volume_match:.1%}\n"
                f"Positions to close: {len(top_recovery.get('recovery_positions', [])) + 1}\n\n"
                f"Continue?"
            )
            
            if result:
                success = self.position_monitor.execute_close_action(top_recovery)
                
                if success:
                    self.log("✅ Smart recovery executed successfully")
                    messagebox.showinfo("Success", f"Smart recovery completed!\nNet result: ${net_profit:.2f}")
                else:
                    self.log("❌ Smart recovery failed")
                    messagebox.showerror("Error", "Smart recovery failed")
            
        except Exception as e:
            self.log(f"❌ Smart recovery error: {e}")
    
    def refresh_lot_analysis(self):
        """🔄 Refresh Lot Analysis"""
        try:
            if not self.position_monitor:
                messagebox.showwarning("Warning", "Position Monitor not initialized")
                return
            
            self.log("🔄 Refreshing lot-aware analysis...")
            
            # Force refresh analysis
            analysis_result = self.position_monitor.force_lot_aware_analysis()
            
            if 'error' not in analysis_result:
                self.log("✅ Lot analysis refreshed successfully")
                
                # แสดงสรุปใน message box
                total_positions = analysis_result.get('total_positions', 0)
                opportunities = analysis_result.get('close_opportunities', 0)
                health_score = analysis_result.get('portfolio_health', 0)
                
                messagebox.showinfo(
                    "🔄 Analysis Refreshed",
                    f"Analysis completed!\n\n"
                    f"Total Positions: {total_positions}\n"
                    f"Close Opportunities: {opportunities}\n" 
                    f"Portfolio Health: {health_score:.2f}\n\n"
                    f"Check recommendations panel for details."
                )
            else:
                self.log("❌ Lot analysis refresh failed")
                messagebox.showerror("Error", "Failed to refresh analysis")
                
        except Exception as e:
            self.log(f"❌ Refresh analysis error: {e}")
    
    # ==========================================
    # 📊 DISPLAY UPDATE METHODS (เก็บเดิม + ปรับปรุง)
    # ==========================================
    
    def update_candlestick_display(self, message: str):
        """🕯️ อัพเดท Candlestick Display - เก็บเดิม"""
        try:
            self.candlestick_info.delete(1.0, tk.END)
            self.candlestick_info.insert(tk.END, message)
            self.candlestick_info.see(tk.END)
        except Exception as e:
            print(f"❌ Candlestick display error: {e}")
    
    def update_candlestick_display_from_data(self, data: Dict):
        """🕯️ อัพเดท Candlestick จากข้อมูลจริง - เก็บเดิม"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            display_text = f"""🕯️ CANDLESTICK ANALYSIS [{timestamp}]
{'='*35}

📊 Current Candle:
   Open:  ${data.get('open', 0):.2f}
   High:  ${data.get('high', 0):.2f}  
   Low:   ${data.get('low', 0):.2f}
   Close: ${data.get('close', 0):.2f}
   
🎨 Properties:
   Color: {data.get('candle_color', 'unknown')}
   Body: {data.get('body_ratio', 0)*100:.1f}%
   Direction: {data.get('price_direction', 'unknown')}
   
📈 Analysis:
   Pattern: {data.get('pattern_name', 'Standard')}
   Strength: {data.get('signal_strength', 0)*100:.1f}%
"""
            
            self.update_candlestick_display(display_text)
            
        except Exception as e:
            self.log(f"❌ Candlestick data display error: {e}")
    
    def update_signal_display(self, signal_data: Dict):
        """🎯 อัพเดท Signal Display - เก็บเดิม"""
        try:
            action = signal_data.get('action', 'WAIT')
            strength = signal_data.get('strength', 0) * 100
            
            if action == 'BUY':
                color = "#00ff88"
                emoji = "🟢"
            elif action == 'SELL':
                color = "#ff6b6b" 
                emoji = "🔴"
            else:
                color = "#ffaa00"
                emoji = "⏳"
            
            self.current_signal.config(text=f"{emoji} {action}", fg=color)
            self.signal_strength.config(text=f"Strength: {strength:.1f}%")
            
        except Exception as e:
            self.log(f"❌ Signal display error: {e}")
    
    def update_performance_display(self, message: str):
        """📊 อัพเดท Performance Display - เก็บเดิม"""
        try:
            self.performance_info.delete(1.0, tk.END)
            self.performance_info.insert(tk.END, message)
            self.performance_info.see(tk.END)
        except Exception as e:
            print(f"❌ Performance display error: {e}")
    
    def update_recommendations_display(self, message: str):
        """🧠 อัพเดท Recommendations Display"""
        try:
            self.recommendations_text.delete(1.0, tk.END)
            self.recommendations_text.insert(tk.END, message)
            self.recommendations_text.see(tk.END)
        except Exception as e:
            print(f"❌ Recommendations display error: {e}")
    
    # ==========================================
    # 🎮 CONTROL METHODS (เก็บเดิม + ปรับปรุง)
    # ==========================================
    
    def stop_trading(self):
        """⏹️ หยุด Trading - เก็บเดิม"""
        try:
            self.log("⏹️ Stopping Enhanced Pure Candlestick Trading...")
            self.is_trading = False
            
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="🟡 Trading Stopped", fg="#ffaa00")
            
            self.log("✅ Enhanced Pure Candlestick Trading stopped")
            
        except Exception as e:
            self.log(f"❌ Stop trading error: {e}")
    
    def close_selected_position(self):
        """❌ ปิดออเดอร์ที่เลือก - เก็บเดิม"""
        try:
            selection = self.positions_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select position to close")
                return
            
            item = self.positions_tree.item(selection[0])
            position_id = item['values'][0]
            
            # 🆕 แสดงรายละเอียด lot efficiency
            profit_per_lot = item['values'][4]
            efficiency = item['values'][5]
            
            result = messagebox.askyesno(
                "❌ Close Position",
                f"Close position #{position_id}?\n\n"
                f"Profit per Lot: {profit_per_lot}\n"
                f"Efficiency: {efficiency}\n\n"
                f"Continue?"
            )
            
            if result:
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
        """🚨 ปิดออเดอร์ทั้งหมดฉุกเฉิน - เก็บเดิม"""
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
            
            if self.is_trading:
                self.stop_trading()
                
        except Exception as e:
            self.log(f"❌ Emergency close error: {e}")
    
    # ==========================================
    # 📝 UTILITY METHODS (เก็บเดิม)
    # ==========================================
    
    def log(self, message: str):
        """📝 เขียน log - เก็บเดิม"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"
            
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.insert(tk.END, log_message)
                self.log_text.see(tk.END)
                
                lines = self.log_text.get(1.0, tk.END).split('\n')
                if len(lines) > 100:
                    self.log_text.delete(1.0, f"{len(lines)-100}.0")
            
            print(log_message.strip())
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            print(f"Log error: {e}")
    
    def start_gui_updates(self):
        """🔄 เริ่ม GUI Updates - เก็บเดิม"""
        def update_loop():
            while True:
                try:
                    time.sleep(1)
                except Exception as e:
                    self.log(f"❌ GUI update error: {e}")
        
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def on_closing(self):
        """🔒 เมื่อปิดโปรแกรม - Enhanced with lot data saving"""
        try:
            self.log("🔒 Shutting down Enhanced Pure Candlestick System...")
            
            # หยุด trading
            if self.is_trading:
                self.stop_trading()
                time.sleep(1)
            
            # 🆕 บันทึกข้อมูล lot efficiency
            if self.persistence_manager and self.position_monitor:
                self.log("💾 Saving enhanced session data...")
                
                # รวบรวมข้อมูล session
                session_data = {
                    'last_shutdown': datetime.now().isoformat(),
                    'trading_was_active': self.is_trading,
                    'mt5_connected': self.mt5_connector.is_connected if self.mt5_connector else False,
                    'portfolio_health_score': self.portfolio_health_score,
                    'lot_efficiency_data': self.lot_efficiency_data,
                    'enhanced_features_used': True
                }
                
                self.persistence_manager.save_session_info(session_data)
                
                # บันทึก performance data
                if self.performance_tracker:
                    performance_data = self.performance_tracker.get_current_metrics()
                    
                    # เพิ่มข้อมูล lot efficiency
                    if self.position_monitor:
                        lot_report = self.position_monitor.get_lot_efficiency_report()
                        performance_data['final_lot_efficiency'] = lot_report
                    
                    self.persistence_manager.save_performance_data(performance_data)
                
                self.log("✅ Enhanced session data saved")
            
            # ตัดการเชื่อมต่อ
            if self.mt5_connector and self.mt5_connector.is_connected:
                self.disconnect_mt5()
            
            self.root.destroy()
            
        except Exception as e:
            print(f"Shutdown error: {e}")
            self.root.destroy()
    
    # ==========================================
    # 🆕 ENHANCED MENU & ANALYSIS METHODS
    # ==========================================
    
    def show_lot_efficiency_analysis(self):
        """📊 แสดง Lot Efficiency Analysis ใน popup window"""
        try:
            if not self.position_monitor:
                messagebox.showwarning("Warning", "Position Monitor not initialized")
                return
            
            # ดึงข้อมูล lot efficiency
            lot_report = self.position_monitor.get_lot_efficiency_report()
            lot_distribution = self.position_monitor.get_lot_distribution_analysis()
            
            # สร้าง analysis window
            analysis_window = tk.Toplevel(self.root)
            analysis_window.title("📊 Lot Efficiency Analysis")
            analysis_window.geometry("700x500")
            analysis_window.configure(bg="#2a2a2a")
            
            # แสดงข้อมูล
            analysis_text = scrolledtext.ScrolledText(
                analysis_window, font=("Consolas", 10),
                bg="#1a1a1a", fg="#00aaff", wrap="word"
            )
            analysis_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # เขียนรายงาน
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            report_text = f"""📊 LOT EFFICIENCY ANALYSIS REPORT
Generated: {timestamp}
{'='*50}

🔢 EFFICIENCY BREAKDOWN:
"""
            
            if 'efficiency_breakdown' in lot_report:
                for category, data in lot_report['efficiency_breakdown'].items():
                    report_text += f"\n{category.upper()}:\n"
                    report_text += f"   Positions: {data.get('count', 0)}\n"
                    report_text += f"   Volume: {data.get('total_volume', 0):.2f} lots\n"
                    report_text += f"   Avg Efficiency: ${data.get('avg_efficiency', 0):.1f}/lot\n"
                    report_text += f"   Portfolio %: {data.get('volume_percentage', 0):.1f}%\n"
            
            report_text += f"\n\n📏 LOT SIZE DISTRIBUTION:\n"
            
            if 'message' not in lot_distribution:
                for size_range, data in lot_distribution.items():
                    report_text += f"\n{size_range.upper()} LOTS:\n"
                    report_text += f"   Count: {data.get('count', 0)}\n"
                    report_text += f"   Volume: {data.get('total_volume', 0):.2f} lots\n"
                    report_text += f"   Profit: ${data.get('total_profit', 0):.2f}\n"
                    report_text += f"   Avg $/Lot: ${data.get('avg_profit_per_lot', 0):.1f}\n"
            
            report_text += f"\n\n💡 RECOMMENDATIONS:\n"
            
            if 'recommendations' in lot_report:
                for rec in lot_report['recommendations']:
                    report_text += f"   • {rec}\n"
            
            analysis_text.insert("end", report_text)
            analysis_text.config(state="disabled")
            
        except Exception as e:
            self.log(f"❌ Show lot analysis error: {e}")
    
    def show_margin_optimization_suggestions(self):
        """🔧 แสดง Margin Optimization Suggestions"""
        try:
            if not self.position_monitor:
                messagebox.showwarning("Warning", "Position Monitor not initialized")
                return
            
            # ดึงข้อเสนะแนะ
            suggestions = self.position_monitor.get_margin_optimization_suggestions()
            
            if not suggestions:
                messagebox.showinfo("Info", "No margin optimization suggestions available")
                return
            
            # สร้าง suggestions window
            suggestions_window = tk.Toplevel(self.root)
            suggestions_window.title("🔧 Margin Optimization Suggestions")
            suggestions_window.geometry("600x400")
            suggestions_window.configure(bg="#2a2a2a")
            
            suggestions_text = scrolledtext.ScrolledText(
                suggestions_window, font=("Consolas", 10),
                bg="#1a1a1a", fg="#ffaa00", wrap="word"
            )
            suggestions_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # เขียนข้อเสนอแนะ
            report_text = f"🔧 MARGIN OPTIMIZATION SUGGESTIONS\n"
            report_text += f"Generated: {datetime.now().strftime('%H:%M:%S')}\n"
            report_text += "="*40 + "\n\n"
            
            for i, suggestion in enumerate(suggestions, 1):
                urgency = suggestion.get('urgency', 'medium')
                message = suggestion.get('message', '')
                
                # Icon ตาม urgency
                if urgency == 'high':
                    icon = "🚨"
                elif urgency == 'medium':
                    icon = "⚠️"
                else:
                    icon = "💡"
                
                report_text += f"{i}. {icon} {message}\n"
                
                # รายละเอียดเพิ่มเติม
                if 'estimated_margin_freed' in suggestion:
                    report_text += f"   Margin to free: ${suggestion['estimated_margin_freed']:.0f}\n"
                if 'affected_positions' in suggestion:
                    report_text += f"   Affected positions: {suggestion['affected_positions']}\n"
                if 'current_imbalance' in suggestion:
                    report_text += f"   Current imbalance: {suggestion['current_imbalance']:.1%}\n"
                
                report_text += "\n"
            
            suggestions_text.insert("end", report_text)
            suggestions_text.config(state="disabled")
            
        except Exception as e:
            self.log(f"❌ Show margin suggestions error: {e}")
    
    # ==========================================
    # 🔧 MENU BAR (เพิ่มใหม่)
    # ==========================================
    
    def setup_menu_bar(self):
        """📋 Setup Enhanced Menu Bar"""
        try:
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)
            
            # 📊 Analysis Menu
            analysis_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="📊 Analysis", menu=analysis_menu)
            
            analysis_menu.add_command(
                label="📊 Lot Efficiency Report", 
                command=self.show_lot_efficiency_analysis
            )
            analysis_menu.add_command(
                label="🔧 Margin Optimization", 
                command=self.show_margin_optimization_suggestions
            )
            analysis_menu.add_separator()
            analysis_menu.add_command(
                label="🔄 Force Refresh Analysis", 
                command=self.refresh_lot_analysis
            )
            
            # 🎮 Actions Menu
            actions_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="🎮 Actions", menu=actions_menu)
            
            actions_menu.add_command(
                label="🔧 Auto Margin Optimization", 
                command=self.execute_margin_optimization
            )
            actions_menu.add_command(
                label="⚖️ Auto Volume Balance", 
                command=self.execute_volume_balance
            )
            actions_menu.add_command(
                label="🎯 Auto Smart Recovery", 
                command=self.execute_smart_recovery
            )
            
        except Exception as e:
            self.log(f"❌ Menu setup error: {e}")

# ==========================================
# 🚀 APPLICATION ENTRY POINT
# ==========================================

def main():
    """🚀 เริ่มต้น Enhanced Pure Candlestick Trading System"""
    
    print("🕯️ Enhanced Pure Candlestick Trading System (Lot-Aware)")
    print("=" * 60)
    print("🚀 Starting enhanced application...")
    
    # Create enhanced GUI
    root = tk.Tk()
    app = EnhancedPureCandlestickGUI(root)
    
    # Setup menu bar
    app.setup_menu_bar()
    
    # Handle window close
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start GUI
    try:
        print("✅ Enhanced GUI started successfully")
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        app.on_closing()
    except Exception as e:
        print(f"❌ Enhanced GUI error: {e}")

if __name__ == "__main__":
    main()