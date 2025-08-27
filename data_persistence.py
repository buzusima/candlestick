"""
💾 Data Persistence Manager (COMPLETE VERSION)
data_persistence.py

🚀 Features:
✅ Session Data Persistence
✅ Signal History Management
✅ Performance Data Storage
✅ Processed Signatures Tracking
✅ Auto Cleanup Old Files
✅ Error Recovery & Validation
✅ Integration with All Components

🎯 จัدการการบันทึกและกู้คืนข้อมูลข้าม session restart
ป้องกันการสูญหายข้อมูลเมื่อรีสตาร์ทระบบ
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Set, List, Any, Optional
import shutil

class DataPersistenceManager:
    """
    💾 ระบบจัดการข้อมูลถาวร (COMPLETE)
    
    Features:
    - บันทึก/กู้คืน processed signatures
    - บันทึก/กู้คืน signal history  
    - บันทึก/กู้คืน performance data
    - บันทึก/กู้คืน session info
    - ลบข้อมูลเก่าอัตโนมัติ
    - Backup & Recovery
    """
    
    def __init__(self, data_directory: str = "trading_data"):
        """
        เริ่มต้น Data Persistence Manager
        
        Args:
            data_directory: โฟลเดอร์สำหรับเก็บข้อมูล
        """
        self.data_dir = Path(data_directory)
        self.data_dir.mkdir(exist_ok=True)
        
        # โฟลเดอร์ย่อยสำหรับจัดระบบ
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # ไฟล์สำหรับเก็บข้อมูลต่างๆ
        self.files = {
            'signatures': self.data_dir / "processed_signatures.json",
            'signals': self.data_dir / "signal_history.json", 
            'performance': self.data_dir / "performance_data.json",
            'session': self.data_dir / "session_info.json",
            'positions': self.data_dir / "position_history.json",
            'execution_stats': self.data_dir / "execution_stats.json",
            'lot_analysis': self.data_dir / "lot_analysis.json"
        }
        
        # การตั้งค่า
        self.max_history_days = 30  # เก็บข้อมูล 30 วัน
        self.max_signals_history = 1000  # เก็บ signal สูงสุด 1000 รายการ
        self.auto_backup_enabled = True
        self.compression_enabled = True
        
        print(f"💾 DataPersistenceManager initialized (COMPLETE)")
        print(f"   Data directory: {self.data_dir}")
        print(f"   Backup directory: {self.backup_dir}")
        print(f"   Max history: {self.max_history_days} days")
        
        self._initialize_data_files()
        self._cleanup_old_files()

    def _initialize_data_files(self):
        """🔧 เริ่มต้นไฟล์ข้อมูล"""
        try:
            # สร้างไฟล์เปล่าถ้ายังไม่มี
            default_data = {
                'signatures': [],
                'signals': [],
                'performance': {
                    'total_signals': 0,
                    'successful_executions': 0,
                    'total_profit': 0.0,
                    'session_start': datetime.now().isoformat()
                },
                'session': {
                    'last_session': datetime.now().isoformat(),
                    'session_count': 1,
                    'total_runtime_hours': 0.0
                },
                'positions': [],
                'execution_stats': {
                    'total_executions': 0,
                    'success_rate': 100.0,
                    'avg_execution_time_ms': 0.0
                },
                'lot_analysis': {
                    'total_volume_traded': 0.0,
                    'avg_profit_per_lot': 0.0,
                    'volume_efficiency_score': 0.0
                }
            }
            
            for file_type, file_path in self.files.items():
                if not file_path.exists():
                    self._save_json_safely(file_path, default_data.get(file_type, {}))
                    print(f"📁 Created {file_type} data file")
                    
        except Exception as e:
            print(f"❌ Initialize data files error: {e}")

    def _cleanup_old_files(self):
        """🧹 ลบไฟล์เก่าเกิน max_history_days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_history_days)
            cutoff_timestamp = cutoff_date.timestamp()
            
            cleanup_count = 0
            
            for file_path in self.data_dir.glob("*.json"):
                try:
                    if file_path.stat().st_mtime < cutoff_timestamp:
                        # สำรองก่อนลบ
                        if self.auto_backup_enabled:
                            backup_name = f"{file_path.stem}_backup_{datetime.now().strftime('%Y%m%d')}.json"
                            backup_path = self.backup_dir / backup_name
                            shutil.copy2(file_path, backup_path)
                        
                        # ย้ายไปที่ backup
                        old_backup_name = f"{file_path.stem}_old_{datetime.now().strftime('%Y%m%d')}.json"
                        old_backup_path = self.backup_dir / old_backup_name
                        file_path.rename(old_backup_path)
                        cleanup_count += 1
                        
                except Exception as e:
                    print(f"❌ Cleanup file {file_path.name} error: {e}")
                    
            if cleanup_count > 0:
                print(f"🧹 Cleaned up {cleanup_count} old files")
                    
        except Exception as e:
            print(f"❌ Cleanup old files error: {e}")

    def _save_json_safely(self, file_path: Path, data: Any) -> bool:
        """💾 บันทึก JSON อย่างปลอดภัย"""
        try:
            # บันทึกไฟล์ชั่วคราวก่อน
            temp_path = file_path.with_suffix('.tmp')
            
            with temp_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # ย้ายไฟล์ชั่วคราวไปแทนที่ไฟล์จริง
            temp_path.replace(file_path)
            return True
            
        except Exception as e:
            print(f"❌ Save JSON safely error for {file_path}: {e}")
            # ลบไฟล์ชั่วคราวถ้ามี
            if temp_path.exists():
                temp_path.unlink()
            return False

    def _load_json_safely(self, file_path: Path) -> Optional[Any]:
        """📂 โหลด JSON อย่างปลอดภัย"""
        try:
            if not file_path.exists():
                return None
                
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                return data
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error for {file_path}: {e}")
            # พยายามกู้คืนจาก backup
            return self._recover_from_backup(file_path)
            
        except Exception as e:
            print(f"❌ Load JSON error for {file_path}: {e}")
            return None

    def _recover_from_backup(self, file_path: Path) -> Optional[Any]:
        """🔄 กู้คืนข้อมูลจาก backup"""
        try:
            # หา backup ล่าสุด
            backup_pattern = f"{file_path.stem}_backup_*.json"
            backup_files = list(self.backup_dir.glob(backup_pattern))
            
            if not backup_files:
                return None
                
            # เรียงตามวันที่ (ใหม่สุดก่อน)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_backup = backup_files[0]
            
            print(f"🔄 Attempting recovery from: {latest_backup.name}")
            
            with latest_backup.open('r', encoding='utf-8') as f:
                data = json.load(f)
                
            # คัดลอก backup กลับมาที่ไฟล์เดิม
            shutil.copy2(latest_backup, file_path)
            print(f"✅ Recovery successful from {latest_backup.name}")
            
            return data
            
        except Exception as e:
            print(f"❌ Recovery from backup failed: {e}")
            return None

    # ==========================================
    # 📝 SIGNATURE PERSISTENCE
    # ==========================================

    def load_processed_signatures(self) -> Set[str]:
        """📂 โหลดลายเซ็นแท่งเทียนที่ประมวลผลแล้ว"""
        try:
            data = self._load_json_safely(self.files['signatures'])
            
            if data is None:
                print(f"📝 No previous signatures found, starting fresh")
                return set()
            
            if isinstance(data, list):
                signatures = set(data)
            elif isinstance(data, dict):
                signatures = set(data.get('signatures', []))
            else:
                signatures = set()
            
            # ลบรายการเก่าเกินไป
            if len(signatures) > 1000:  # เก็บแค่ 1000 ล่าสุด
                signatures = set(list(signatures)[-1000:])
                print(f"🧹 Trimmed signatures to 1000 most recent")
            
            print(f"📂 Loaded {len(signatures)} processed signatures")
            return signatures
            
        except Exception as e:
            print(f"❌ Load signatures error: {e}")
            return set()

    def save_processed_signatures(self, signatures: Set[str]) -> bool:
        """💾 บันทึกลายเซ็นที่ประมวลผลแล้ว"""
        try:
            # แปลง set เป็น list เพื่อบันทึก JSON
            signatures_list = list(signatures)
            
            data = {
                'signatures': signatures_list,
                'total_count': len(signatures_list),
                'last_updated': datetime.now().isoformat(),
                'created_by': 'CandlestickAnalyzer'
            }
            
            success = self._save_json_safely(self.files['signatures'], data)
            
            if success:
                print(f"💾 Saved {len(signatures_list)} processed signatures")
            
            return success
            
        except Exception as e:
            print(f"❌ Save signatures error: {e}")
            return False

    # ==========================================
    # 📊 SIGNAL HISTORY PERSISTENCE  
    # ==========================================

    def load_signal_history(self) -> List[Dict]:
        """📂 โหลดประวัติ signals"""
        try:
            data = self._load_json_safely(self.files['signals'])
            
            if data is None:
                return []
            
            if isinstance(data, list):
                signals = data
            elif isinstance(data, dict):
                signals = data.get('signals', [])
            else:
                signals = []
            
            # เรียงตามเวลา (ใหม่สุดก่อน) และจำกัดจำนวน
            signals.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            signals = signals[:self.max_signals_history]
            
            print(f"📂 Loaded {len(signals)} signal history records")
            return signals
            
        except Exception as e:
            print(f"❌ Load signal history error: {e}")
            return []

    def save_signal_history(self, signals: List[Dict]) -> bool:
        """💾 บันทึกประวัติ signals"""
        try:
            # จำกัดจำนวน signals ที่เก็บ
            if len(signals) > self.max_signals_history:
                signals = signals[-self.max_signals_history:]
            
            data = {
                'signals': signals,
                'total_count': len(signals),
                'last_updated': datetime.now().isoformat(),
                'created_by': 'SignalGenerator'
            }
            
            success = self._save_json_safely(self.files['signals'], data)
            
            if success:
                print(f"💾 Saved {len(signals)} signal history records")
            
            return success
            
        except Exception as e:
            print(f"❌ Save signal history error: {e}")
            return False

    def add_signal_record(self, signal_record: Dict) -> bool:
        """➕ เพิ่ม signal record ใหม่"""
        try:
            signals = self.load_signal_history()
            signals.append(signal_record)
            return self.save_signal_history(signals)
            
        except Exception as e:
            print(f"❌ Add signal record error: {e}")
            return False

    # ==========================================
    # 📈 PERFORMANCE DATA PERSISTENCE
    # ==========================================

    def load_performance_data(self) -> Dict:
        """📂 โหลดข้อมูลผลงาน"""
        try:
            data = self._load_json_safely(self.files['performance'])
            
            if data is None:
                return {
                    'total_signals': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'total_profit': 0.0,
                    'total_loss': 0.0,
                    'win_rate': 0.0,
                    'avg_profit_per_trade': 0.0,
                    'session_start': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
            
            print(f"📂 Loaded performance data: {data.get('total_signals', 0)} total signals")
            return data
            
        except Exception as e:
            print(f"❌ Load performance data error: {e}")
            return {}

    def save_performance_data(self, performance_data: Dict) -> bool:
        """💾 บันทึกข้อมูลผลงาน"""
        try:
            performance_data['last_updated'] = datetime.now().isoformat()
            
            success = self._save_json_safely(self.files['performance'], performance_data)
            
            if success:
                signals_count = performance_data.get('total_signals', 0)
                profit = performance_data.get('total_profit', 0.0)
                print(f"💾 Saved performance data: {signals_count} signals, ${profit:.2f} profit")
            
            return success
            
        except Exception as e:
            print(f"❌ Save performance data error: {e}")
            return False

    def update_performance_metrics(self, metrics_update: Dict) -> bool:
        """🔄 อัปเดตผลงาน"""
        try:
            current_data = self.load_performance_data()
            
            # รวมข้อมูลใหม่เข้ากับข้อมูลเดิม
            for key, value in metrics_update.items():
                if key in ['total_profit', 'total_loss', 'total_signals', 'successful_executions', 'failed_executions']:
                    current_data[key] = current_data.get(key, 0) + value
                else:
                    current_data[key] = value
            
            # คำนวณอัตราชนะใหม่
            total_trades = current_data.get('successful_executions', 0) + current_data.get('failed_executions', 0)
            if total_trades > 0:
                current_data['win_rate'] = (current_data.get('successful_executions', 0) / total_trades) * 100
                
                total_profit = current_data.get('total_profit', 0)
                current_data['avg_profit_per_trade'] = total_profit / total_trades
            
            return self.save_performance_data(current_data)
            
        except Exception as e:
            print(f"❌ Update performance metrics error: {e}")
            return False

    # ==========================================
    # 💺 SESSION INFO PERSISTENCE
    # ==========================================

    def load_session_info(self) -> Dict:
        """📂 โหลดข้อมูล session"""
        try:
            data = self._load_json_safely(self.files['session'])
            
            if data is None:
                return {
                    'session_count': 1,
                    'first_session': datetime.now().isoformat(),
                    'last_session': datetime.now().isoformat(),
                    'total_runtime_hours': 0.0,
                    'last_mt5_connection': None
                }
            
            print(f"📂 Loaded session info: Session #{data.get('session_count', 1)}")
            return data
            
        except Exception as e:
            print(f"❌ Load session info error: {e}")
            return {}

    def save_session_info(self, session_data: Dict) -> bool:
        """💾 บันทึกข้อมูล session"""
        try:
            session_data['last_updated'] = datetime.now().isoformat()
            
            success = self._save_json_safely(self.files['session'], session_data)
            
            if success:
                session_num = session_data.get('session_count', 1)
                runtime = session_data.get('total_runtime_hours', 0)
                print(f"💾 Saved session info: Session #{session_num}, {runtime:.1f}h total")
            
            return success
            
        except Exception as e:
            print(f"❌ Save session info error: {e}")
            return False

    def start_new_session(self) -> bool:
        """🚀 เริ่ม session ใหม่"""
        try:
            current_session = self.load_session_info()
            
            new_session = {
                'session_count': current_session.get('session_count', 0) + 1,
                'first_session': current_session.get('first_session', datetime.now().isoformat()),
                'last_session': datetime.now().isoformat(),
                'current_session_start': datetime.now().isoformat(),
                'total_runtime_hours': current_session.get('total_runtime_hours', 0.0),
                'last_mt5_connection': None
            }
            
            return self.save_session_info(new_session)
            
        except Exception as e:
            print(f"❌ Start new session error: {e}")
            return False

    # ==========================================
    # 🔧 UTILITY & MAINTENANCE METHODS
    # ==========================================

    def get_storage_stats(self) -> Dict:
        """📊 สถิติการใช้พื้นที่เก็บข้อมูล"""
        try:
            stats = {
                'total_files': 0,
                'total_size_mb': 0.0,
                'backup_files': 0,
                'backup_size_mb': 0.0,
                'oldest_file': None,
                'newest_file': None
            }
            
            # นับไฟล์ข้อมูลหลัก
            for file_path in self.data_dir.glob("*.json"):
                if file_path.is_file():
                    stats['total_files'] += 1
                    file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                    stats['total_size_mb'] += file_size
                    
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if stats['oldest_file'] is None or file_time < stats['oldest_file']:
                        stats['oldest_file'] = file_time
                    if stats['newest_file'] is None or file_time > stats['newest_file']:
                        stats['newest_file'] = file_time
            
            # นับไฟล์ backup
            for backup_file in self.backup_dir.glob("*.json"):
                if backup_file.is_file():
                    stats['backup_files'] += 1
                    backup_size = backup_file.stat().st_size / (1024 * 1024)  # MB
                    stats['backup_size_mb'] += backup_size
            
            # แปลงวันที่เป็น string
            if stats['oldest_file']:
                stats['oldest_file'] = stats['oldest_file'].isoformat()
            if stats['newest_file']:
                stats['newest_file'] = stats['newest_file'].isoformat()
            
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            stats['backup_size_mb'] = round(stats['backup_size_mb'], 2)
            
            return stats
            
        except Exception as e:
            print(f"❌ Get storage stats error: {e}")
            return {'error': str(e)}

    def cleanup_all_data(self, confirm: bool = False) -> bool:
        """🗑️ ลบข้อมูลทั้งหมด (ใช้ระวัง!)"""
        if not confirm:
            print("❌ Cleanup aborted: confirm=False")
            return False
            
        try:
            deleted_count = 0
            
            # ลบไฟล์ข้อมูลหลัก
            for file_path in self.data_dir.glob("*.json"):
                if file_path.is_file():
                    file_path.unlink()
                    deleted_count += 1
            
            # ลบไฟล์ backup
            for backup_file in self.backup_dir.glob("*.json"):
                if backup_file.is_file():
                    backup_file.unlink()
                    deleted_count += 1
            
            print(f"🗑️ Deleted {deleted_count} data files")
            
            # สร้างไฟล์เปล่าใหม่
            self._initialize_data_files()
            
            return True
            
        except Exception as e:
            print(f"❌ Cleanup all data error: {e}")
            return False

    def create_full_backup(self) -> bool:
        """💾 สร้าง backup เต็มรูปแบบ"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"full_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            # รวบรวมข้อมูลทั้งหมด
            full_backup = {
                'backup_timestamp': datetime.now().isoformat(),
                'backup_type': 'full_system_backup',
                'data': {}
            }
            
            for data_type, file_path in self.files.items():
                data = self._load_json_safely(file_path)
                if data is not None:
                    full_backup['data'][data_type] = data
            
            # บันทึก backup
            success = self._save_json_safely(backup_path, full_backup)
            
            if success:
                backup_size = backup_path.stat().st_size / 1024  # KB
                print(f"💾 Full backup created: {backup_filename} ({backup_size:.1f} KB)")
            
            return success
            
        except Exception as e:
            print(f"❌ Create full backup error: {e}")
            return False

    def get_persistence_info(self) -> Dict:
        """ℹ️ ข้อมูล Data Persistence Manager"""
        return {
            'name': 'Data Persistence Manager',
            'version': '2.0.0',
            'data_directory': str(self.data_dir),
            'backup_directory': str(self.backup_dir),
            'max_history_days': self.max_history_days,
            'max_signals_history': self.max_signals_history,
            'auto_backup_enabled': self.auto_backup_enabled,
            'compression_enabled': self.compression_enabled,
            'total_data_files': len(self.files),
            'storage_stats': self.get_storage_stats()
        }

# ==========================================
# 🔧 INTEGRATION FUNCTIONS
# ==========================================

def create_persistence_manager(data_directory: str = "trading_data") -> DataPersistenceManager:
    """🏗️ สร้าง Data Persistence Manager"""
    try:
        return DataPersistenceManager(data_directory)
    except Exception as e:
        print(f"❌ Failed to create persistence manager: {e}")
        return None

def integrate_with_analyzer(analyzer, persistence_manager):
    """🔗 เชื่อมต่อกับ CandlestickAnalyzer"""
    try:
        if analyzer and persistence_manager:
            analyzer.persistence_manager = persistence_manager
            
            # โหลดลายเซ็นที่ประมวลผลแล้ว
            processed_signatures = persistence_manager.load_processed_signatures()
            if hasattr(analyzer, 'processed_signatures'):
                analyzer.processed_signatures.update(processed_signatures)
            
            print(f"🔗 CandlestickAnalyzer integrated with persistence")
            return True
            
    except Exception as e:
        print(f"❌ Analyzer integration error: {e}")
        return False

def integrate_with_generator(generator, persistence_manager):
    """🔗 เชื่อมต่อกับ SignalGenerator"""
    try:
        if generator and persistence_manager:
            generator.persistence_manager = persistence_manager
            
            # โหลดประวัติ signals
            signal_history = persistence_manager.load_signal_history()
            if hasattr(generator, 'signal_history'):
                generator.signal_history.extend(signal_history)
            
            print(f"🔗 SignalGenerator integrated with persistence")
            return True
            
    except Exception as e:
        print(f"❌ Generator integration error: {e}")
        return False

def integrate_with_tracker(tracker, persistence_manager):
    """🔗 เชื่อมต่อกับ PerformanceTracker"""
    try:
        if tracker and persistence_manager:
            tracker.persistence_manager = persistence_manager
            
            # โหลดข้อมูลผลงาน
            performance_data = persistence_manager.load_performance_data()
            if performance_data and hasattr(tracker, 'load_from_persistence'):
                tracker.load_from_persistence(performance_data)
            
            print(f"🔗 PerformanceTracker integrated with persistence")
            return True
            
    except Exception as e:
        print(f"❌ Tracker integration error: {e}")
        return False