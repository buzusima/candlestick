"""
💾 Data Persistence Manager
data_persistence.py

จัดการการบันทึกและกู้คืนข้อมูลข้าม session restart
ป้องกันการสูญหายข้อมูลเมื่อรีสตาร์ทระบบ
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Set, List, Any, Optional

class DataPersistenceManager:
    """
    💾 ระบบจัดการข้อมูลถาวร
    
    Features:
    - บันทึก/กู้คืน processed signatures
    - บันทึก/กู้คืน signal history  
    - บันทึก/กู้คืน performance data
    - ลบข้อมูลเก่าอัตโนมัติ
    """
    
    def __init__(self, data_directory: str = "trading_data"):
        """
        เริ่มต้น Data Persistence Manager
        
        Args:
            data_directory: โฟลเดอร์สำหรับเก็บข้อมูล
        """
        self.data_dir = Path(data_directory)
        self.data_dir.mkdir(exist_ok=True)
        
        # ไฟล์สำหรับเก็บข้อมูลต่างๆ
        self.files = {
            'signatures': self.data_dir / "processed_signatures.json",
            'signals': self.data_dir / "signal_history.json", 
            'performance': self.data_dir / "performance_data.json",
            'session': self.data_dir / "session_info.json"
        }
        
        print(f"💾 DataPersistenceManager initialized")
        print(f"   Data directory: {self.data_dir}")
        self._cleanup_old_files()

    def _cleanup_old_files(self):
        """🧹 ลบไฟล์เก่าเกิน 7 วัน"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            cutoff_timestamp = cutoff_date.timestamp()
            
            for file_path in self.data_dir.glob("*.json"):
                try:
                    if file_path.stat().st_mtime < cutoff_timestamp:
                        backup_name = f"{file_path.stem}_old_{datetime.now().strftime('%Y%m%d')}.json"
                        backup_path = self.data_dir / backup_name
                        file_path.rename(backup_path)
                        print(f"🗂️ Moved old file: {file_path.name} -> {backup_name}")
                except Exception as e:
                    print(f"❌ Cleanup file {file_path.name} error: {e}")
                    
        except Exception as e:
            print(f"❌ Cleanup old files error: {e}")

    # ========================================
    # CANDLESTICK SIGNATURES PERSISTENCE
    # ========================================

    def load_processed_signatures(self) -> Set[str]:
        """
        💾 โหลดลายเซ็นแท่งเทียนที่ประมวลผลแล้ว
        
        Returns:
            Set[str]: ชุดลายเซ็นที่ประมวลผลแล้ว
        """
        try:
            if not self.files['signatures'].exists():
                print(f"📁 No signatures file found, starting fresh")
                return set()
            
            with open(self.files['signatures'], 'r') as f:
                data = json.load(f)
            
            signatures_list = data.get('signatures', [])
            
            # กรองข้อมูลเก่าเกิน 24 ชั่วโมง
            cutoff_time = datetime.now().timestamp() - (24 * 3600)
            valid_signatures = [
                sig for sig in signatures_list
                if self._extract_timestamp_from_signature(sig) > cutoff_time
            ]
            
            removed_count = len(signatures_list) - len(valid_signatures)
            if removed_count > 0:
                print(f"🧹 Removed {removed_count} old signatures (>24h)")
            
            print(f"💾 Loaded {len(valid_signatures)} processed signatures")
            return set(valid_signatures)
            
        except Exception as e:
            print(f"❌ Load signatures error: {e}")
            return set()

    def save_processed_signatures(self, signatures: Set[str]):
        """
        💾 บันทึกลายเซ็นแท่งเทียนที่ประมวลผลแล้ว
        
        Args:
            signatures: ชุดลายเซ็นที่จะบันทึก
        """
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_signatures': len(signatures),
                'signatures': list(signatures)
            }
            
            with open(self.files['signatures'], 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"💾 Saved {len(signatures)} processed signatures")
            
        except Exception as e:
            print(f"❌ Save signatures error: {e}")

    # ========================================
    # SIGNAL HISTORY PERSISTENCE  
    # ========================================

    def load_signal_history(self) -> Set[str]:
        """
        💾 โหลดประวัติ signal ที่ส่งแล้ว
        
        Returns:
            Set[str]: ชุดลายเซ็นที่ส่ง signal แล้ว
        """
        try:
            if not self.files['signals'].exists():
                print(f"📁 No signal history found, starting fresh")
                return set()
                
            with open(self.files['signals'], 'r') as f:
                data = json.load(f)
            
            signal_signatures = data.get('signal_signatures', [])
            
            # กรองข้อมูลเก่าเกิน 12 ชั่วโมง (signals ไม่ต้องเก็บนาน)
            cutoff_time = datetime.now().timestamp() - (12 * 3600)
            valid_signals = [
                sig for sig in signal_signatures
                if self._extract_timestamp_from_signature(sig) > cutoff_time
            ]
            
            removed_count = len(signal_signatures) - len(valid_signals)
            if removed_count > 0:
                print(f"🧹 Removed {removed_count} old signal signatures (>12h)")
            
            print(f"💾 Loaded {len(valid_signals)} signal signatures")
            return set(valid_signals)
            
        except Exception as e:
            print(f"❌ Load signal history error: {e}")
            return set()

    def save_signal_history(self, signal_signatures: Set[str]):
        """
        💾 บันทึกประวัติ signal ที่ส่งแล้ว
        
        Args:
            signal_signatures: ชุดลายเซ็นที่ส่ง signal แล้ว
        """
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_signals': len(signal_signatures),
                'signal_signatures': list(signal_signatures)
            }
            
            with open(self.files['signals'], 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"💾 Saved {len(signal_signatures)} signal signatures")
            
        except Exception as e:
            print(f"❌ Save signal history error: {e}")

    # ========================================
    # PERFORMANCE DATA PERSISTENCE
    # ========================================

    def load_performance_data(self) -> Dict:
        """
        💾 โหลดข้อมูลผลการดำเนินงาน
        
        Returns:
            Dict: ข้อมูล performance
        """
        try:
            if not self.files['performance'].exists():
                print(f"📁 No performance data found, starting fresh")
                return {}
                
            with open(self.files['performance'], 'r') as f:
                data = json.load(f)
                
            print(f"💾 Loaded performance data")
            print(f"   Total signals: {data.get('total_signals', 0)}")
            print(f"   Total orders: {data.get('total_orders', 0)}")
            
            return data
            
        except Exception as e:
            print(f"❌ Load performance data error: {e}")
            return {}

    def save_performance_data(self, performance_data: Dict):
        """
        💾 บันทึกข้อมูลผลการดำเนินงาน
        
        Args:
            performance_data: ข้อมูล performance ที่จะบันทึก
        """
        try:
            # เพิ่ม metadata
            data = performance_data.copy()
            data.update({
                'last_updated': datetime.now().isoformat(),
                'session_count': data.get('session_count', 0) + 1
            })
            
            with open(self.files['performance'], 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            print(f"💾 Saved performance data")
            
        except Exception as e:
            print(f"❌ Save performance data error: {e}")

    # ========================================
    # SESSION INFO PERSISTENCE
    # ========================================

    def save_session_info(self, session_data: Dict):
        """
        💾 บันทึกข้อมูล session
        
        Args:
            session_data: ข้อมูล session
        """
        try:
            data = {
                'last_session_end': datetime.now().isoformat(),
                'session_data': session_data,
                'clean_shutdown': True
            }
            
            with open(self.files['session'], 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"❌ Save session info error: {e}")

    def load_session_info(self) -> Dict:
        """
        💾 โหลดข้อมูล session ล่าสุด
        
        Returns:
            Dict: ข้อมูล session
        """
        try:
            if not self.files['session'].exists():
                return {}
                
            with open(self.files['session'], 'r') as f:
                data = json.load(f)
                
            last_end = data.get('last_session_end')
            clean_shutdown = data.get('clean_shutdown', False)
            
            if last_end:
                last_time = datetime.fromisoformat(last_end)
                print(f"💾 Last session: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Clean shutdown: {clean_shutdown}")
                
            return data.get('session_data', {})
            
        except Exception as e:
            print(f"❌ Load session info error: {e}")
            return {}

    # ========================================
    # UTILITY METHODS
    # ========================================

    def _extract_timestamp_from_signature(self, signature: str) -> float:
        """
        🔧 ดึง timestamp จากลายเซ็น
        
        Args:
            signature: ลายเซ็นในรูปแบบ "timestamp_ohlc"
            
        Returns:
            float: timestamp หรือ 0 ถ้าแปลงไม่ได้
        """
        try:
            return float(signature.split('_')[0])
        except:
            return 0.0

    def get_storage_stats(self) -> Dict:
        """
        📊 สถิติการใช้พื้นที่จัดเก็บ
        
        Returns:
            Dict: ข้อมูลสถิติ
        """
        stats = {
            'data_directory': str(self.data_dir),
            'files': {}
        }
        
        for name, file_path in self.files.items():
            if file_path.exists():
                size = file_path.stat().st_size
                modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                stats['files'][name] = {
                    'size_bytes': size,
                    'size_kb': round(size / 1024, 2),
                    'last_modified': modified.isoformat(),
                    'exists': True
                }
            else:
                stats['files'][name] = {'exists': False}
        
        return stats

    def export_all_data(self, export_path: str) -> bool:
        """
        📤 Export ข้อมูลทั้งหมดไปยังไฟล์เดียว
        
        Args:
            export_path: path สำหรับไฟล์ export
            
        Returns:
            bool: สำเร็จหรือไม่
        """
        try:
            all_data = {
                'export_time': datetime.now().isoformat(),
                'signatures': list(self.load_processed_signatures()),
                'signals': list(self.load_signal_history()),
                'performance': self.load_performance_data(),
                'session': self.load_session_info()
            }
            
            with open(export_path, 'w') as f:
                json.dump(all_data, f, indent=2, default=str)
                
            print(f"📤 Exported all data to: {export_path}")
            return True
            
        except Exception as e:
            print(f"❌ Export data error: {e}")
            return False

    def clear_all_data(self):
        """
        🗑️ ลบข้อมูลทั้งหมด (ใช้เมื่อต้องการเริ่มใหม่)
        """
        try:
            for name, file_path in self.files.items():
                if file_path.exists():
                    backup_name = f"{file_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    backup_path = self.data_dir / backup_name
                    file_path.rename(backup_path)
                    print(f"🗑️ Cleared {name} data (backed up as {backup_name})")
                    
        except Exception as e:
            print(f"❌ Clear data error: {e}")

# ========================================
# INTEGRATION HELPERS
# ========================================

def create_persistence_manager() -> DataPersistenceManager:
    """
    🏗️ สร้าง DataPersistenceManager instance
    
    Returns:
        DataPersistenceManager: instance ที่พร้อมใช้งาน
    """
    return DataPersistenceManager()

def integrate_with_analyzer(analyzer, persistence_manager: DataPersistenceManager):
    """
    🔗 ผูก persistence เข้ากับ CandlestickAnalyzer
    
    Args:
        analyzer: CandlestickAnalyzer instance
        persistence_manager: DataPersistenceManager instance
    """
    # โหลดข้อมูลเก่า
    analyzer.processed_signatures = persistence_manager.load_processed_signatures()
    analyzer.persistence_manager = persistence_manager
    
    # Override method เพื่อบันทึกอัตโนมัติ
    original_mark_processed = analyzer._mark_signature_processed
    
    def enhanced_mark_processed(signature: str):
        original_mark_processed(signature)
        # บันทึกทุกครั้งที่มีการเปลี่ยนแปลง
        analyzer.persistence_manager.save_processed_signatures(analyzer.processed_signatures)
    
    analyzer._mark_signature_processed = enhanced_mark_processed

def integrate_with_generator(generator, persistence_manager: DataPersistenceManager):
    """
    🔗 ผูก persistence เข้ากับ SignalGenerator
    
    Args:
        generator: SignalGenerator instance  
        persistence_manager: DataPersistenceManager instance
    """
    # โหลดข้อมูลเก่า
    generator.signal_signatures = persistence_manager.load_signal_history()
    generator.persistence_manager = persistence_manager
    
    # Override method เพื่อบันทึกอัตโนมัติ
    original_mark_signal = generator._mark_signal_sent_for_signature
    
    def enhanced_mark_signal(signature: str):
        original_mark_signal(signature)
        # บันทึกทุกครั้งที่ส่ง signal
        generator.persistence_manager.save_signal_history(generator.signal_signatures)
    
    generator._mark_signal_sent_for_signature = enhanced_mark_signal