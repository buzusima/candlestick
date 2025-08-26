"""
📈 Pure Candlestick Performance Tracker
performance_tracker.py

🚀 Features:
✅ Signal Accuracy Tracking
✅ Candlestick Pattern Performance
✅ Order Execution Statistics  
✅ Portfolio Performance Metrics
✅ Real-time Performance Analytics
✅ Daily/Weekly/Monthly Summaries

🎯 ติดตามผลงานของระบบ Pure Candlestick Trading
เน้นการวัดประสิทธิภาพของ signals และ patterns
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics
import json

class PerformanceTracker:
    """
    📈 Pure Candlestick Performance Tracker
    
    ติดตามและวิเคราะห์ผลงานของระบบเทรด
    เน้นประสิทธิภาพของ candlestick signals และ patterns
    """
    
    def __init__(self, config: Dict):
        """
        🔧 เริ่มต้น Performance Tracker
        
        Args:
            config: การตั้งค่าระบบ
        """
        self.config = config
        self.symbol = config.get("trading", {}).get("symbol", "XAUUSD.v")
        
        # Performance tracking data structures
        self.signal_history = []  # ประวัติ signals ทั้งหมด
        self.execution_history = []  # ประวัติการส่งออเดอร์
        self.pattern_performance = {}  # ผลงานของแต่ละ pattern
        self.daily_performance = {}  # ผลงานรายวัน
        
        # Current session metrics
        self.session_start_time = datetime.now()
        self.session_stats = {
            'signals_generated': 0,
            'orders_executed': 0,
            'total_profit': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'break_even_trades': 0
        }
        
        # Performance thresholds
        self.profit_threshold = 1.0   # ถือว่า winning trade
        self.loss_threshold = -1.0    # ถือว่า losing trade
        
        print(f"📈 Performance Tracker initialized for {self.symbol}")
        print(f"   Session started: {self.session_start_time.strftime('%H:%M:%S')}")
        print(f"   Profit threshold: ${self.profit_threshold}")
        print(f"   Loss threshold: ${self.loss_threshold}")
    
    # ==========================================
    # 📝 PERFORMANCE RECORDING
    # ==========================================
    
    def record_signal(self, signal_data: Dict):
        """
        📝 บันทึก Signal ที่สร้างขึ้น
        
        Args:
            signal_data: ข้อมูล signal จาก SignalGenerator
        """
        try:
            if not signal_data:
                return
            
            # เตรียมข้อมูลสำหรับบันทึก
            signal_record = {
                'timestamp': datetime.now(),
                'action': signal_data.get('action', 'WAIT'),
                'strength': signal_data.get('strength', 0),
                'confidence': signal_data.get('confidence', 0),
                'signal_id': signal_data.get('signal_id', ''),
                
                # ข้อมูล candlestick
                'candle_color': signal_data.get('candle_color', ''),
                'body_ratio': signal_data.get('body_ratio', 0),
                'price_direction': signal_data.get('price_direction', ''),
                'pattern_name': signal_data.get('pattern_name', ''),
                'volume_factor': signal_data.get('volume_factor', 1.0),
                
                # เก็บเพื่อติดตามผลลัพธ์ภายหลัง
                'open_price': signal_data.get('close', 0),  # ราคาที่ signal เกิดขึ้น
                'execution_status': 'pending',  # จะอัพเดทเมื่อส่งออเดอร์
                'final_result': None  # จะอัพเดทเมื่อปิดออเดอร์
            }
            
            # บันทึกลง history
            self.signal_history.append(signal_record)
            
            # อัพเดทสถิติ session
            if signal_data.get('action') in ['BUY', 'SELL']:
                self.session_stats['signals_generated'] += 1
                
                # อัพเดทผลงาน pattern
                pattern_name = signal_data.get('pattern_name', 'standard')
                self._update_pattern_stats(pattern_name, 'signal_generated')
            
            # เก็บแค่ 1000 signals ล่าสุด
            if len(self.signal_history) > 1000:
                self.signal_history = self.signal_history[-1000:]
            
            print(f"📝 Signal recorded: {signal_data.get('action')} (Strength: {signal_data.get('strength', 0):.2f})")
            
        except Exception as e:
            print(f"❌ Signal recording error: {e}")
    
    def record_execution(self, execution_result: Dict, signal_data: Dict):
        """
        📝 บันทึกผลการส่งออเดอร์
        
        Args:
            execution_result: ผลการส่งออเดอร์
            signal_data: ข้อมูล signal ต้นตอ
        """
        try:
            if not execution_result or not signal_data:
                return
            
            # เตรียมข้อมูลการส่งออเดอร์
            execution_record = {
                'timestamp': datetime.now(),
                'signal_id': signal_data.get('signal_id', ''),
                'success': execution_result.get('success', False),
                'order_id': execution_result.get('order_id'),
                'deal_id': execution_result.get('deal_id'),
                'volume': execution_result.get('volume', 0),
                'execution_price': execution_result.get('price', 0),
                'execution_time_ms': execution_result.get('execution_time_ms', 0),
                'slippage_points': execution_result.get('slippage_points', 0),
                'error': execution_result.get('error', ''),
                
                # ข้อมูลจาก signal
                'signal_action': signal_data.get('action'),
                'signal_strength': signal_data.get('strength', 0),
                'signal_price': signal_data.get('close', 0),
                'pattern_name': signal_data.get('pattern_name', ''),
                
                # สำหรับติดตามผลลัพธ์
                'position_status': 'open',  # จะอัพเดทเมื่อปิด
                'final_profit': None
            }
            
            # บันทึกลง history
            self.execution_history.append(execution_record)
            
            # อัพเดทสถิติ session
            if execution_result.get('success'):
                self.session_stats['orders_executed'] += 1
                
                # อัพเดท signal history ด้วย
                self._update_signal_execution_status(
                    signal_data.get('signal_id', ''), 
                    'executed',
                    execution_result
                )
                
                # อัพเดทผลงาน pattern
                pattern_name = signal_data.get('pattern_name', 'standard')
                self._update_pattern_stats(pattern_name, 'order_executed')
            
            # เก็บแค่ 1000 executions ล่าสุด
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
            
            status = "✅ Success" if execution_result.get('success') else "❌ Failed"
            print(f"📝 Execution recorded: {status}")
            
        except Exception as e:
            print(f"❌ Execution recording error: {e}")
    
    def record_position_close(self, position_data: Dict, close_reason: str, final_profit: float):
        """
        📝 บันทึกการปิด Position
        
        Args:
            position_data: ข้อมูล position ที่ปิด
            close_reason: เหตุผลการปิด
            final_profit: กำไรขาดทุนสุดท้าย
        """
        try:
            position_id = position_data.get('id')
            magic_number = position_data.get('magic', 0)
            
            # อัพเดท execution history
            for execution in self.execution_history:
                if (execution.get('order_id') == position_id or
                    (execution.get('signal_id') and str(magic_number).endswith(execution.get('signal_id', '')))):
                    
                    execution['position_status'] = 'closed'
                    execution['final_profit'] = final_profit
                    execution['close_reason'] = close_reason
                    execution['close_time'] = datetime.now()
                    break
            
            # อัพเดทสถิติ session
            self.session_stats['total_profit'] += final_profit
            
            if final_profit > self.profit_threshold:
                self.session_stats['winning_trades'] += 1
                trade_result = 'win'
            elif final_profit < self.loss_threshold:
                self.session_stats['losing_trades'] += 1
                trade_result = 'loss'
            else:
                self.session_stats['break_even_trades'] += 1
                trade_result = 'break_even'
            
            # อัพเดทผลงาน pattern
            pattern_name = position_data.get('pattern', 'standard')  # จะต้องเก็บไว้ใน magic number หรือ comment
            self._update_pattern_final_result(pattern_name, trade_result, final_profit)
            
            # บันทึก daily performance
            self._update_daily_performance(final_profit, trade_result)
            
            print(f"📝 Position close recorded: {position_id} → ${final_profit:.2f} ({trade_result})")
            
        except Exception as e:
            print(f"❌ Position close recording error: {e}")
    
    # ==========================================
    # 📊 PATTERN PERFORMANCE TRACKING
    # ==========================================
    
    def _update_pattern_stats(self, pattern_name: str, event_type: str):
        """📊 อัพเดทสถิติ Pattern"""
        try:
            if pattern_name not in self.pattern_performance:
                self.pattern_performance[pattern_name] = {
                    'signals_generated': 0,
                    'orders_executed': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'break_even_trades': 0,
                    'total_profit': 0.0,
                    'execution_rate': 0.0,
                    'win_rate': 0.0,
                    'avg_profit_per_trade': 0.0
                }
            
            if event_type == 'signal_generated':
                self.pattern_performance[pattern_name]['signals_generated'] += 1
            elif event_type == 'order_executed':
                self.pattern_performance[pattern_name]['orders_executed'] += 1
            
            # คำนวณ execution rate
            pattern_stats = self.pattern_performance[pattern_name]
            signals = pattern_stats['signals_generated']
            executions = pattern_stats['orders_executed']
            
            pattern_stats['execution_rate'] = executions / signals if signals > 0 else 0
            
        except Exception as e:
            print(f"❌ Pattern stats update error: {e}")
    
    def _update_pattern_final_result(self, pattern_name: str, result: str, profit: float):
        """🎯 อัพเดทผลลัพธ์สุดท้ายของ Pattern"""
        try:
            if pattern_name not in self.pattern_performance:
                return
            
            pattern_stats = self.pattern_performance[pattern_name]
            
            # อัพเดทผลลัพธ์
            if result == 'win':
                pattern_stats['winning_trades'] += 1
            elif result == 'loss':
                pattern_stats['losing_trades'] += 1
            else:
                pattern_stats['break_even_trades'] += 1
            
            pattern_stats['total_profit'] += profit
            
            # คำนวณ metrics
            total_trades = (pattern_stats['winning_trades'] + 
                          pattern_stats['losing_trades'] + 
                          pattern_stats['break_even_trades'])
            
            if total_trades > 0:
                pattern_stats['win_rate'] = pattern_stats['winning_trades'] / total_trades
                pattern_stats['avg_profit_per_trade'] = pattern_stats['total_profit'] / total_trades
            
        except Exception as e:
            print(f"❌ Pattern final result update error: {e}")
    
    def _update_daily_performance(self, profit: float, result: str):
        """📅 อัพเดทผลงานรายวัน"""
        try:
            today = datetime.now().date().isoformat()
            
            if today not in self.daily_performance:
                self.daily_performance[today] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'break_even_trades': 0,
                    'total_profit': 0.0,
                    'win_rate': 0.0,
                    'avg_profit_per_trade': 0.0
                }
            
            daily_stats = self.daily_performance[today]
            daily_stats['total_trades'] += 1
            daily_stats['total_profit'] += profit
            
            if result == 'win':
                daily_stats['winning_trades'] += 1
            elif result == 'loss':
                daily_stats['losing_trades'] += 1
            else:
                daily_stats['break_even_trades'] += 1
            
            # คำนวณ metrics
            total_trades = daily_stats['total_trades']
            if total_trades > 0:
                daily_stats['win_rate'] = daily_stats['winning_trades'] / total_trades
                daily_stats['avg_profit_per_trade'] = daily_stats['total_profit'] / total_trades
            
        except Exception as e:
            print(f"❌ Daily performance update error: {e}")
    
    # ==========================================
    # 📊 REAL-TIME METRICS
    # ==========================================
    
    def get_current_metrics(self) -> Dict:
        """
        📊 ดึง Performance Metrics ปัจจุบัน
        
        Returns:
            Dict: รวม metrics ทั้งหมด
        """
        try:
            # คำนวณ metrics จาก session
            session_metrics = self._calculate_session_metrics()
            
            # คำนวณ signal metrics
            signal_metrics = self._calculate_signal_metrics()
            
            # คำนวณ pattern metrics  
            pattern_metrics = self._calculate_pattern_metrics()
            
            # รวม metrics ทั้งหมด
            current_metrics = {
                # Session metrics
                'session_duration_hours': (datetime.now() - self.session_start_time).total_seconds() / 3600,
                'total_signals': self.session_stats['signals_generated'],
                'total_orders': self.session_stats['orders_executed'], 
                'total_profit': self.session_stats['total_profit'],
                'winning_trades': self.session_stats['winning_trades'],
                'losing_trades': self.session_stats['losing_trades'],
                'break_even_trades': self.session_stats['break_even_trades'],
                
                # Calculated metrics
                'win_rate': session_metrics.get('win_rate', 0),
                'avg_profit_per_trade': session_metrics.get('avg_profit_per_trade', 0),
                'profit_factor': session_metrics.get('profit_factor', 0),
                'execution_rate': signal_metrics.get('execution_rate', 0),
                'signal_accuracy': signal_metrics.get('signal_accuracy', 0),
                
                # Pattern performance
                'best_pattern': pattern_metrics.get('best_pattern', 'standard'),
                'worst_pattern': pattern_metrics.get('worst_pattern', 'standard'),
                'pattern_count': len(self.pattern_performance),
                
                # Timing metrics
                'avg_execution_time_ms': signal_metrics.get('avg_execution_time_ms', 0),
                'signals_per_hour': signal_metrics.get('signals_per_hour', 0),
                
                # Additional info
                'symbol': self.symbol,
                'last_update': datetime.now()
            }
            
            return current_metrics
            
        except Exception as e:
            print(f"❌ Current metrics calculation error: {e}")
            return {'error': str(e)}
    
    def _calculate_session_metrics(self) -> Dict:
        """📊 คำนวณ Session Metrics"""
        try:
            total_trades = (self.session_stats['winning_trades'] + 
                          self.session_stats['losing_trades'] + 
                          self.session_stats['break_even_trades'])
            
            if total_trades == 0:
                return {
                    'win_rate': 0.0,
                    'avg_profit_per_trade': 0.0,
                    'profit_factor': 0.0
                }
            
            # Win rate
            win_rate = self.session_stats['winning_trades'] / total_trades
            
            # Average profit per trade
            avg_profit = self.session_stats['total_profit'] / total_trades
            
            # Profit factor (รวมกำไร / รวมขาดทุน)
            winning_profit = sum(
                exec_rec.get('final_profit', 0) 
                for exec_rec in self.execution_history 
                if exec_rec.get('final_profit', 0) > 0
            )
            
            losing_profit = abs(sum(
                exec_rec.get('final_profit', 0) 
                for exec_rec in self.execution_history 
                if exec_rec.get('final_profit', 0) < 0
            ))
            
            profit_factor = winning_profit / losing_profit if losing_profit > 0 else float('inf')
            
            return {
                'win_rate': win_rate,
                'avg_profit_per_trade': avg_profit,
                'profit_factor': profit_factor,
                'total_trades': total_trades
            }
            
        except Exception as e:
            print(f"❌ Session metrics calculation error: {e}")
            return {}
    
    def _calculate_signal_metrics(self) -> Dict:
        """🎯 คำนวณ Signal Metrics"""
        try:
            if not self.signal_history:
                return {
                    'execution_rate': 0.0,
                    'signal_accuracy': 0.0,
                    'avg_execution_time_ms': 0.0,
                    'signals_per_hour': 0.0
                }
            
            # Execution rate (signals ที่กลายเป็นออเดอร์จริง)
            tradeable_signals = [s for s in self.signal_history if s.get('action') in ['BUY', 'SELL']]
            executed_signals = [s for s in tradeable_signals if s.get('execution_status') == 'executed']
            
            execution_rate = len(executed_signals) / len(tradeable_signals) if tradeable_signals else 0
            
            # Signal accuracy (signals ที่ให้ผลกำไร)
            completed_signals = [s for s in executed_signals if s.get('final_result') is not None]
            profitable_signals = [s for s in completed_signals if s.get('final_result', 0) > 0]
            
            signal_accuracy = len(profitable_signals) / len(completed_signals) if completed_signals else 0
            
            # Average execution time
            execution_times = [
                exec_rec.get('execution_time_ms', 0) 
                for exec_rec in self.execution_history 
                if exec_rec.get('success')
            ]
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0
            
            # Signals per hour
            session_hours = (datetime.now() - self.session_start_time).total_seconds() / 3600
            signals_per_hour = len(tradeable_signals) / session_hours if session_hours > 0 else 0
            
            return {
                'execution_rate': execution_rate,
                'signal_accuracy': signal_accuracy,
                'avg_execution_time_ms': avg_execution_time,
                'signals_per_hour': signals_per_hour,
                'total_tradeable_signals': len(tradeable_signals),
                'executed_signals': len(executed_signals),
                'completed_signals': len(completed_signals)
            }
            
        except Exception as e:
            print(f"❌ Signal metrics calculation error: {e}")
            return {}
    
    def _calculate_pattern_metrics(self) -> Dict:
        """🔍 คำนวณ Pattern Performance Metrics"""
        try:
            if not self.pattern_performance:
                return {
                    'best_pattern': 'standard',
                    'worst_pattern': 'standard',
                    'avg_pattern_performance': 0.0
                }
            
            # หา pattern ที่ดีที่สุด และ แย่ที่สุด
            pattern_scores = {}
            
            for pattern, stats in self.pattern_performance.items():
                # คำนวณคะแนน pattern (รวม win rate + avg profit)
                total_trades = (stats.get('winning_trades', 0) + 
                              stats.get('losing_trades', 0) + 
                              stats.get('break_even_trades', 0))
                
                if total_trades >= 3:  # มีข้อมูลเพียงพอ
                    win_rate = stats.get('win_rate', 0)
                    avg_profit = stats.get('avg_profit_per_trade', 0)
                    
                    # คะแนน pattern = (win_rate * 0.6) + (normalized_avg_profit * 0.4)
                    normalized_profit = max(-1, min(1, avg_profit / 10))  # normalize เป็น -1 ถึง 1
                    pattern_score = (win_rate * 0.6) + ((normalized_profit + 1) / 2 * 0.4)
                    
                    pattern_scores[pattern] = pattern_score
            
            if pattern_scores:
                best_pattern = max(pattern_scores.keys(), key=lambda x: pattern_scores[x])
                worst_pattern = min(pattern_scores.keys(), key=lambda x: pattern_scores[x])
                avg_score = statistics.mean(pattern_scores.values())
            else:
                best_pattern = worst_pattern = 'standard'
                avg_score = 0.5
            
            return {
                'best_pattern': best_pattern,
                'worst_pattern': worst_pattern,
                'avg_pattern_performance': avg_score,
                'pattern_scores': pattern_scores
            }
            
        except Exception as e:
            print(f"❌ Pattern metrics calculation error: {e}")
            return {}
    
    # ==========================================
    # 🔧 HELPER METHODS
    # ==========================================
    
    def _update_signal_execution_status(self, signal_id: str, status: str, execution_data: Dict = None):
        """🔄 อัพเดทสถานะการส่งออเดอร์ของ Signal"""
        try:
            for signal in self.signal_history:
                if signal.get('signal_id') == signal_id:
                    signal['execution_status'] = status
                    if execution_data:
                        signal['execution_price'] = execution_data.get('price', 0)
                        signal['execution_time'] = datetime.now()
                    break
                    
        except Exception as e:
            print(f"❌ Signal status update error: {e}")
    
    def get_pattern_performance_summary(self) -> Dict:
        """🔍 สรุปผลงาน Patterns ทั้งหมด"""
        try:
            summary = {}
            
            for pattern, stats in self.pattern_performance.items():
                total_trades = (stats.get('winning_trades', 0) + 
                              stats.get('losing_trades', 0) + 
                              stats.get('break_even_trades', 0))
                
                if total_trades > 0:
                    summary[pattern] = {
                        'signals': stats.get('signals_generated', 0),
                        'executions': stats.get('orders_executed', 0),
                        'trades': total_trades,
                        'win_rate': stats.get('win_rate', 0),
                        'avg_profit': stats.get('avg_profit_per_trade', 0),
                        'total_profit': stats.get('total_profit', 0),
                        'execution_rate': stats.get('execution_rate', 0)
                    }
            
            return summary
            
        except Exception as e:
            print(f"❌ Pattern summary error: {e}")
            return {}
    
    def get_daily_performance_summary(self) -> Dict:
        """📅 สรุปผลงานรายวัน"""
        return self.daily_performance.copy()
    
    def reset_session_stats(self):
        """🔄 รีเซ็ตสถิติ Session"""
        try:
            self.session_start_time = datetime.now()
            self.session_stats = {
                'signals_generated': 0,
                'orders_executed': 0,
                'total_profit': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
                'break_even_trades': 0
            }
            print(f"🔄 Session stats reset")
            
        except Exception as e:
            print(f"❌ Session reset error: {e}")
    
    def export_performance_data(self, filename: str = None) -> bool:
        """💾 Export ข้อมูล Performance"""
        try:
            if not filename:
                filename = f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            export_data = {
                'session_info': {
                    'start_time': self.session_start_time.isoformat(),
                    'export_time': datetime.now().isoformat(),
                    'symbol': self.symbol
                },
                'session_stats': self.session_stats,
                'pattern_performance': self.pattern_performance,
                'daily_performance': self.daily_performance,
                'current_metrics': self.get_current_metrics()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"💾 Performance data exported to: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Performance export error: {e}")
            return False
    
    def is_ready(self) -> bool:
        """✅ ตรวจสอบความพร้อม"""
        return self.config is not None
    
    def get_tracker_info(self) -> Dict:
        """ℹ️ ข้อมูล Performance Tracker"""
        return {
            'name': 'Pure Candlestick Performance Tracker',
            'version': '1.0.0',
            'symbol': self.symbol,
            'session_start': self.session_start_time,
            'signal_history_count': len(self.signal_history),
            'execution_history_count': len(self.execution_history),
            'pattern_count': len(self.pattern_performance),
            'daily_records_count': len(self.daily_performance),
            'profit_threshold': self.profit_threshold,
            'loss_threshold': self.loss_threshold
        }