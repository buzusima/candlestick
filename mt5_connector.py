"""
🔍  MT5 Multi-Installation Detector
แค่หา MT5 ทุกตัว แล้วให้ลูกค้าเลือกเอง - เรียบง่าย ไม่ซับซ้อน
"""

import MetaTrader5 as mt5
import os
import time
import re
from datetime import datetime
import psutil
import winreg
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class MT5Installation:
    """ข้อมูล MT5 Installation แบบง่ายๆ"""
    path: str
    broker: str = "Unknown"
    executable_type: str = ""  # terminal64.exe or terminal.exe
    is_running: bool = False
    data_path: str = ""

class MT5Connector:
    """
    🔍  MT5 Multi-Installation Connector
    
    ฟีเจอร์:
    - หา MT5 ทุกตัวในเครื่อง
    - แสดงรายการให้เลือก
    - ไม่มีการให้คะแนน ไม่ซับซ้อน
    """
    
    def __init__(self):
        self.is_connected = False
        self.gold_symbol = None
        self.account_info = {}
        self.symbol_info = {}
        self.selected_mt5 = None
        
        # เก็บรายการ MT5 ทั้งหมดที่เจอ
        self.available_installations: List[MT5Installation] = []
        
        # Gold symbol variations
        self.gold_symbols = [
            "XAUUSD", "GOLD", "XAU/USD", "XAUUSD.cmd", "GOLD#", 
            "XAUUSD.", "XAUUSD-", "XAU-USD", "GOLD.", "GOLD_",
            "XAUUSD.raw", "XAUUSD.ecn", "GOLDmicro", "XAUUSD.m",
            "XAUUSD_", "XAUUSD#", "XAUUSDpro", "GOLD.std"
        ]
        
    def find_running_mt5_installations(self) -> List[MT5Installation]:
        """
        🔍 หา MT5 ที่กำลังรันอยู่เท่านั้น
        Returns: List ของ MT5Installation objects ที่กำลังทำงาน
        """
        installations = []
        found_processes = {}
        
        print("🔍 หา MT5 ที่กำลังทำงานอยู่...")
        
        try:
            # หาจาก running processes เท่านั้น
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                try:
                    proc_info = proc.info
                    if not proc_info['name']:
                        continue
                        
                    # เช็คว่าเป็น MT5 หรือไม่
                    if ('terminal64.exe' in proc_info['name'].lower() or 
                        'terminal.exe' in proc_info['name'].lower()):
                        
                        exe_path = proc_info['exe']
                        if exe_path and self._is_mt5_process(exe_path):
                            
                            # ป้องกัน duplicate processes
                            if exe_path not in found_processes:
                                
                                # ตรวจจับ broker จาก path และ process info
                                broker_name = self._detect_broker_from_process(proc_info)
                                
                                installation = MT5Installation(
                                    path=exe_path,
                                    broker=broker_name,
                                    executable_type=os.path.basename(exe_path),
                                    is_running=True
                                )
                                
                                installations.append(installation)
                                found_processes[exe_path] = installation
                                
                                print(f"   ✅ เจอ: {broker_name} ({installation.executable_type})")
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                    continue
                    
        except Exception as e:
            print(f"❌ Process scan error: {e}")
        
        self.available_installations = installations
        
        if installations:
            print(f"✅ เจอ MT5 ที่ทำงานอยู่ {len(installations)} ตัว")
        else:
            print("❌ ไม่เจอ MT5 ที่ทำงานอยู่")
            print("💡 กรุณาเปิด MT5 ก่อน แล้วลอง Scan อีกครั้ง")
            
        return installations
    
    def _is_mt5_process(self, exe_path: str) -> bool:
        """เช็คว่าเป็น MT5 process จริงหรือไม่"""
        try:
            if not exe_path:
                return False
                
            path_lower = exe_path.lower()
            
            # เช็คชื่อไฟล์
            if not ('terminal64.exe' in path_lower or 'terminal.exe' in path_lower):
                return False
                
            # เช็คว่ามีไฟล์ที่เกี่ยวข้องกับ MT5 หรือไม่
            exe_dir = os.path.dirname(exe_path)
            
            # ไฟล์ที่ MT5 ควรมี
            mt5_files = [
                'metatrader.exe', 'metaeditor64.exe', 'metaeditor.exe',
                'terminal.ini', 'config', 'profiles'
            ]
            
            has_mt5_files = any(
                os.path.exists(os.path.join(exe_dir, f)) or 
                os.path.exists(os.path.join(exe_dir, f.capitalize()))
                for f in mt5_files
            )
            
            return has_mt5_files
            
        except Exception:
            return False
    
    def _detect_broker_from_process(self, proc_info: Dict) -> str:
        """ตรวจจับ broker จาก process information"""
        try:
            exe_path = proc_info.get('exe', '')
            cmdline = proc_info.get('cmdline', [])
            
            # ตรวจจับจาก path
            path_lower = exe_path.lower() if exe_path else ''
            
            # รายชื่อ broker ที่รู้จัก
            known_brokers = {
                'exness': 'Exness',
                'icmarkets': 'IC Markets', 
                'ic markets': 'IC Markets',
                'ic_markets': 'IC Markets',
                'pepperstone': 'Pepperstone',
                'fxtm': 'FXTM',
                'forextime': 'FXTM',
                'xm': 'XM',
                'xmglobal': 'XM',
                'fxpro': 'FXPro',
                'avatrade': 'AvaTrade',
                'tickmill': 'Tickmill',
                'admiral': 'Admiral Markets',
                'admiralmarkets': 'Admiral Markets',
                'oanda': 'OANDA',
                'forex.com': 'Forex.com',
                'hotforex': 'HotForex',
                'roboforex': 'RoboForex',
                'alpari': 'Alpari',
                'instaforex': 'InstaForex',
                'fbs': 'FBS'
            }
            
            # เช็คจาก path
            for key, name in known_brokers.items():
                if key in path_lower:
                    return name
            
            # เช็คจาก command line arguments
            if cmdline:
                cmdline_str = ' '.join(cmdline).lower()
                for key, name in known_brokers.items():
                    if key in cmdline_str:
                        return f"{name} (cmdline)"
            
            # เช็คจาก folder structure
            if exe_path:
                path_parts = exe_path.replace('\\', '/').split('/')
                for part in path_parts:
                    part_lower = part.lower()
                    if part_lower and len(part_lower) > 3:  # ข้าม folder ชื่อสั้นๆ
                        for key, name in known_brokers.items():
                            if key in part_lower:
                                return f"{name}"
                
                # ถ้ายังหาไม่เจอ ใช้ parent folder name
                parent_folder = os.path.basename(os.path.dirname(exe_path))
                if parent_folder and parent_folder.lower() not in ['metatrader 5', 'metatrader5', 'mt5', 'program files', 'program files (x86)']:
                    return f"MT5 ({parent_folder})"
            
            return "MT5 (Unknown Broker)"
            
        except Exception as e:
            print(f"Broker detection error: {e}")
            return "MT5 (Detection Error)"
    
    def connect_to_installation(self, installation_index: int) -> bool:
        """
        เชื่อมต่อไปยัง MT5 installation ตัวที่เลือก
        
        Args:
            installation_index: index ใน available_installations list
            
        Returns:
            True ถ้าเชื่อมต่อสำเร็จ
        """
        if installation_index < 0 or installation_index >= len(self.available_installations):
            print("❌ เลือก installation ไม่ถูกต้อง")
            return False
            
        installation = self.available_installations[installation_index]
        self.selected_mt5 = installation
        
        return self._attempt_connection(installation)
    
    def auto_connect(self) -> bool:
        """
        Auto-connect แบบใหม่:
        - ถ้ามี MT5 ตัวเดียว -> เชื่อมต่อเลย
        - ถ้ามีหลายตัว -> ให้เลือก
        """
        print("🔗 เริ่มการเชื่อมต่อ MT5...")
        
        # หา MT5 ที่ทำงานอยู่
        installations = self.find_running_mt5_installations()
        
        if not installations:
            print("❌ ไม่เจอ MT5 ที่ทำงานอยู่")
            print("💡 กรุณาเปิด MT5 ก่อน")
            return False
            
        # ถ้ามีตัวเดียว -> เชื่อมต่อเลย
        if len(installations) == 1:
            print(f"📱 เจอ MT5 ตัวเดียว: {installations[0].broker}")
            return self.connect_to_installation(0)
            
        # ถ้ามีหลายตัว -> แสดงให้เลือก
        print(f"\n📋 เจอ MT5 ทั้งหมด {len(installations)} ตัว:")
        for i, inst in enumerate(installations):
            exe_type = "64-bit" if "64" in inst.executable_type else "32-bit"
            print(f"  {i+1}. {inst.broker} ({exe_type}) - 🟢 กำลังทำงาน")
            print(f"     📁 {inst.path}")
            
        print(f"\n❓ กรุณาเลือก MT5 ที่ต้องการใช้ (1-{len(installations)}):")
        print("   หรือใช้ connect_to_installation(index) ใน code")
        
        return False  # ให้ user เลือกเอง
    
    def _attempt_connection(self, installation: MT5Installation) -> bool:
        """ลองเชื่อมต่อกับ MT5 installation"""
        try:
            print(f"🔗 กำลังเชื่อมต่อ: {installation.broker}")
            print(f"📁 Path: {installation.path}")
            
            # MT5 กำลังรันอยู่แล้ว ไม่ต้องสตาร์ท
            if not installation.is_running:
                print(f"⚠️ MT5 ไม่ได้ทำงานอยู่ - ข้ามไป")
                return False
                
            # Initialize MT5
            if not mt5.initialize():
                print(f"❌ ไม่สามารถ initialize MT5 ได้")
                return False
                
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ ไม่มี account login")
                return False
                
            print(f"✅ เชื่อมต่อ account: {account_info.login}")
            print(f"💰 ยอดเงิน: ${account_info.balance:,.2f}")
            print(f"🏦 โบรกเกอร์: {account_info.company}")
            
            # Detect gold symbol
            gold_symbol = self.detect_gold_symbol()
            if not gold_symbol:
                print("⚠️ ไม่เจอสัญลักษณ์ทองคำ")
                # ไม่ return False เพราะอาจจะเทรดอย่างอื่น
                
            if gold_symbol:
                print(f"🥇 สัญลักษณ์ทองคำ: {gold_symbol}")
            
            # เก็บข้อมูลการเชื่อมต่อ
            self.is_connected = True
            self.account_info = {
                'login': account_info.login,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'leverage': account_info.leverage,
                'company': account_info.company,
                'currency': account_info.currency
            }
            
            self.gold_symbol = gold_symbol
            
            return True
            
        except Exception as e:
            print(f"❌ เชื่อมต่อไม่สำเร็จ: {e}")
            return False
    
    # === Gold Symbol Detection (ใช้โค้ดเดิม) ===
    
    def detect_gold_symbol(self):
        """ตรวจจับสัญลักษณ์ทองคำ"""
        try:
            all_symbols = mt5.symbols_get()
            if not all_symbols:
                return None
                
            symbol_names = [symbol.name for symbol in all_symbols]
            
            # Method 1: Exact match
            for gold_sym in self.gold_symbols:
                if gold_sym in symbol_names:
                    if self.verify_gold_symbol(gold_sym):
                        return gold_sym
                        
            # Method 2: Pattern matching
            gold_patterns = [
                r'^XAU.*USD.*$',
                r'^GOLD.*$',
                r'^.*GOLD.*$',
                r'^XAU.*$'
            ]
            
            for pattern in gold_patterns:
                for symbol_name in symbol_names:
                    if re.match(pattern, symbol_name, re.IGNORECASE):
                        if self.verify_gold_symbol(symbol_name):
                            return symbol_name
                            
            return None
            
        except Exception as e:
            print(f"Error detecting gold symbol: {e}")
            return None
    
    def verify_gold_symbol(self, symbol):
        """ตรวจสอบว่าเป็นสัญลักษณ์ทองคำจริง"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return False
                
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    return False
                    
            tick = mt5.symbol_info_tick(symbol)
            if tick and tick.bid:
                price = tick.bid
                if 1000 <= price <= 5000:  # Gold price range
                    return True
                    
            return True
            
        except Exception as e:
            print(f"Error verifying gold symbol {symbol}: {e}")
            return False
    
    # === Utility Methods ===
    
    def get_installation_list(self) -> List[Dict]:
        """ส่งออกรายการ installations สำหรับ GUI"""
        return [
            {
                'index': i,
                'broker': inst.broker,
                'path': inst.path,
                'executable_type': inst.executable_type,
                'is_running': inst.is_running,
                'display_name': f"{inst.broker} ({'64-bit' if '64' in inst.executable_type else '32-bit'})"
            }
            for i, inst in enumerate(self.available_installations)
        ]
    
    def get_account_info(self) -> Dict:
        """ดึงข้อมูล account ปัจจุบัน"""
        return self.account_info.copy()
    
    def get_gold_symbol(self) -> Optional[str]:
        """ดึงสัญลักษณ์ทองคำที่ตรวจจับได้"""
        return self.gold_symbol
    
    def disconnect(self):
        """ตัดการเชื่อมต่อ"""
        try:
            if self.is_connected:
                mt5.shutdown()
                self.is_connected = False
                self.gold_symbol = None
                self.account_info = {}
                self.symbol_info = {}
                print("✅ ตัดการเชื่อมต่อเรียบร้อย")
                return True
        except Exception as e:
            print(f"Error disconnecting: {e}")
            
        return False

    def get_current_price(self, symbol: str) -> float:
        """Get current market price for symbol"""
        try:
            if not self.is_connected:
                print(f"❌ MT5 not connected - cannot get price for {symbol}")
                return 0.0
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                print(f"❌ No tick data for symbol: {symbol}")
                return 0.0
            
            price = tick.bid if hasattr(tick, 'bid') else 0.0
            
            if price <= 0:
                print(f"❌ Invalid price for {symbol}: {price}")
                return 0.0
            
            return price
            
        except Exception as e:
            print(f"❌ Get current price error for {symbol}: {e}")
            return 0.0

# === Test Function ===

def test_connector():
    """ทดสอบ  Connector"""
    print("🧪 ทดสอบ  MT5 Connector...")
    print("=" * 50)
    
    connector = MT5Connector()
    
    # Test 1: หา installations ที่ทำงานอยู่
    installations = connector.find_running_mt5_installations()
    
    if not installations:
        print("❌ ไม่เจอ MT5 ที่ทำงานอยู่")
        print("💡 กรุณาเปิด MT5 ก่อน")
        return
        
    # Test 2: แสดงรายการ
    print(f"\n📊 รายการ MT5 ที่ทำงานอยู่:")
    for i, inst in enumerate(installations):
        exe_type = "64-bit" if "64" in inst.executable_type else "32-bit"
        print(f"  {i}: 🟢 {inst.broker} ({exe_type})")
        print(f"     {inst.path}")
    
    # Test 3: ทดสอบการเชื่อมต่อกับตัวแรก
    print(f"\n🔗 ทดสอบเชื่อมต่อกับตัวแรก...")
    if connector.connect_to_installation(0):
        print("🎉 เชื่อมต่อสำเร็จ!")
        print(f"   Account: {connector.account_info.get('login')}")
        print(f"   Broker: {connector.account_info.get('company')}")
        print(f"   Gold: {connector.gold_symbol}")
        
        # ทดสอบตัดการเชื่อมต่อ
        connector.disconnect()
    else:
        print("❌ เชื่อมต่อไม่สำเร็จ")

if __name__ == "__main__":
    test_connector()