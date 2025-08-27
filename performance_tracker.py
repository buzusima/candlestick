"""
📈 Pure Candlestick Performance Tracker (COMPLETE VERSION)
performance_tracker.py

🚀 Features:
✅ Signal Accuracy Tracking
✅ Candlestick Pattern Performance
✅ Order Execution Statistics  
✅ Portfolio Performance Metrics
✅ Real-time Performance Analytics
✅ Daily/Weekly/Monthly Summaries
✅ Lot-Aware Performance Analysis
✅ ROI & Risk-Adjusted Returns
✅ Performance Persistence Integration

🎯 ติดตามผลงานของระบบ Pure Candlestick Trading
เน้นการวัดประสิทธิภาพของ signals และ patterns
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import statistics
import json
import math

class PerformanceTracker:
    """
    📈 Pure Candlestick Performance Tracker (COMPLETE)
    
    ติดตามและวิเคราะห์ผลงานของระบบเทรด
    เน้นประสิทธิภาพของ candlestick signals และ patterns
    """
    
    def __init__(self, config: Dict):
        """
        🔧 เริ่มต้น Performance Tracker (COMPLETE)
        
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
        self.hourly_performance = {}  # ผลงานรายชั่วโมง
        self.position_history = []  # ประวัติการปิดออเดอร์
        
        # Current session metrics
        self.session_start_time = datetime.now()
        self.session_stats = {
            'signals_generated': 0,
            'signals_buy': 0,
            'signals_sell': 0,
            'signals_wait': 0,
            'orders_executed': 0,
            'orders_successful': 0,
            'orders_failed': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'gross_profit': 0.0,
            'gross_loss': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'break_even_trades': 0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0
        }
        
        # Lot-aware performance metrics
        self.lot_performance = {
            'total_volume_traded': 0.0,
            'avg_profit_per_lot': 0.0,
            'best_lot_efficiency': 0.0,
            'worst_lot_efficiency': 0.0,
            'volume_weighted_return': 0.0,
            'lot_size_distribution': {},
            'profit_by_lot_size': {}
        }
        
        # Risk metrics
        self.risk_metrics = {
            'max_drawdown': 0.0,
            'max_drawdown_percent': 0.0,
            'sharpe_ratio': 0.0,
            'profit_factor': 0.0,
            'recovery_factor': 0.0,
            'calmar_ratio': 0.0,
            'var_95': 0.0,  # Value at Risk 95%
            'expected_shortfall': 0.0
        }
        
        # Performance thresholds
        self.profit_threshold = config.get("performance", {}).get("profit_threshold", 1.0)
        self.loss_threshold = config.get("performance", {}).get("loss_threshold", -1.0)
        self.min_trades_for_stats = config.get("performance", {}).get("min_trades_for_stats", 10)
        
        # Tracking flags
        self.last_trade_result = None  # 'win', 'loss', 'break_even'
        self.current_streak = 0
        self.streak_type = None  # 'win' or 'loss'
        
        # Persistence integration
        self.persistence_manager = None
        self.auto_save_enabled = True
        self.save_interval_minutes = 5
        self.last_save_time = datetime.now()
        
        print(f"📈 Performance Tracker initialized (COMPLETE) for {self.symbol}")
        print(f"   Session started: {self.session_start_time.strftime('%H:%M:%S')}")
        print(f"   Profit threshold: ${self.profit_threshold}")
        print(f"   Loss threshold: ${self.loss_threshold}")
        print(f"   Min trades for statistics: {self.min_trades_for_stats}")
    
    # ==========================================
    # 📝 PERFORMANCE RECORDING - COMPLETE
    # ==========================================
    
    def record_signal(self, signal_data: Dict):
        """
        📝 บันทึก Signal ที่สร้างขึ้น (COMPLETE)
        
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
                'pattern_type': signal_data.get('pattern_type', 'unknown'),
                'candle_color': signal_data.get('candle_color', 'unknown'),
                'body_ratio': signal_data.get('body_ratio', 0),
                'price_direction': signal_data.get('price_direction', 'unknown'),
                'volume_confirmed': signal_data.get('volume_confirmed', False),
                'signal_id': signal_data.get('signal_id', ''),
                'market_session': self._detect_market_session(),
                'price_level': signal_data.get('close', 0),
                'signal_quality_score': signal_data.get('quality_score', 0)
            }
            
            # บันทึกใน history
            self.signal_history.append(signal_record)
            
            # อัพเดท session stats
            self.session_stats['signals_generated'] += 1
            action = signal_record['action']
            
            if action == 'BUY':
                self.session_stats['signals_buy'] += 1
            elif action == 'SELL':
                self.session_stats['signals_sell'] += 1
            else:
                self.session_stats['signals_wait'] += 1
            
            # อัพเดท pattern performance
            pattern = signal_record['pattern_type']
            if pattern not in self.pattern_performance:
                self.pattern_performance[pattern] = {
                    'total_signals': 0,
                    'buy_signals': 0,
                    'sell_signals': 0,
                    'avg_strength': 0.0,
                    'success_rate': 0.0,
                    'total_profit': 0.0
                }
            
            pattern_stats = self.pattern_performance[pattern]
            pattern_stats['total_signals'] += 1
            
            if action == 'BUY':
                pattern_stats['buy_signals'] += 1
            elif action == 'SELL':
                pattern_stats['sell_signals'] += 1
            
            # คำนวณ average strength
            current_avg = pattern_stats['avg_strength']
            total_signals = pattern_stats['total_signals']
            new_strength = signal_record['strength']
            pattern_stats['avg_strength'] = ((current_avg * (total_signals - 1)) + new_strength) / total_signals
            
            # บันทึกประวัติรายชั่วโมง
            self._update_hourly_performance('signal', signal_record)
            
            # Auto-save ถ้าถึงเวลา
            self._auto_save_if_needed()
            
            print(f"📝 Signal recorded: {action} (Strength: {new_strength:.2f})")
            
        except Exception as e:
            print(f"❌ Signal recording error: {e}")
    
    def record_execution(self, execution_result: Dict, signal_data: Dict = None):
        """
        📝 บันทึกผลการส่งออเดอร์ (COMPLETE)
        
        Args:
            execution_result: ผลการส่งออเดอร์จาก OrderExecutor
            signal_data: ข้อมูล signal ที่เกี่ยวข้อง
        """
        try:
            if not execution_result:
                return
            
            # เตรียมข้อมูล execution record
            execution_record = {
                'timestamp': datetime.now(),
                'success': execution_result.get('success', False),
                'order_type': execution_result.get('order_type', 'unknown'),
                'lot_size': execution_result.get('lot_size', 0.0),
                'execution_price': execution_result.get('execution_price', 0.0),
                'slippage': execution_result.get('slippage', 0.0),
                'execution_time_ms': execution_result.get('execution_time_ms', 0.0),
                'order_id': execution_result.get('order_id', None),
                'error_code': execution_result.get('error_code', None),
                'error_message': execution_result.get('error_message', ''),
                'signal_strength': signal_data.get('strength', 0) if signal_data else 0,
                'signal_id': signal_data.get('signal_id', '') if signal_data else '',
                'market_session': self._detect_market_session()
            }
            
            # บันทึกใน history
            self.execution_history.append(execution_record)
            
            # อัพเดท session stats
            self.session_stats['orders_executed'] += 1
            
            if execution_record['success']:
                self.session_stats['orders_successful'] += 1
                
                # อัพเดท lot performance
                lot_size = execution_record['lot_size']
                if lot_size > 0:
                    self.lot_performance['total_volume_traded'] += lot_size
                    
                    # นับการกระจายของ lot size
                    lot_key = f"{lot_size:.2f}"
                    self.lot_performance['lot_size_distribution'][lot_key] = \
                        self.lot_performance['lot_size_distribution'].get(lot_key, 0) + 1
            else:
                self.session_stats['orders_failed'] += 1
            
            # อัพเดทประวัติรายชั่วโมง
            self._update_hourly_performance('execution', execution_record)
            
            # Auto-save
            self._auto_save_if_needed()
            
            status = "✅ SUCCESS" if execution_record['success'] else "❌ FAILED"
            lot_size = execution_record['lot_size']
            print(f"📝 Execution recorded: {status} ({lot_size:.2f} lots)")
            
        except Exception as e:
            print(f"❌ Execution recording error: {e}")
    
    def record_position_close(self, close_result: Dict):
        """
        📝 บันทึกการปิดออเดอร์ (COMPLETE)
        
        Args:
            close_result: ผลการปิดออเดอร์จาก PositionMonitor
        """
        try:
            if not close_result:
                return
            
            # เตรียมข้อมูล position close record
            close_record = {
                'timestamp': datetime.now(),
                'position_id': close_result.get('position_id', 0),
                'position_type': close_result.get('position_type', 'unknown'),
                'lot_size': close_result.get('lot_size', 0.0),
                'open_price': close_result.get('open_price', 0.0),
                'close_price': close_result.get('close_price', 0.0),
                'profit': close_result.get('profit', 0.0),
                'profit_per_lot': close_result.get('profit_per_lot', 0.0),
                'hold_time_minutes': close_result.get('hold_time_minutes', 0),
                'close_reason': close_result.get('close_reason', 'unknown'),
                'market_session': self._detect_market_session(),
                'swap': close_result.get('swap', 0.0),
                'commission': close_result.get('commission', 0.0)
            }
            
            # บันทึกใน history
            self.position_history.append(close_record)
            
            # วิเคราะห์ผลการเทรด
            profit = close_record['profit']
            lot_size = close_record['lot_size']
            profit_per_lot = close_record['profit_per_lot']
            
            # อัพเดท session stats
            if profit > self.profit_threshold:
                self.session_stats['winning_trades'] += 1
                self.session_stats['gross_profit'] += profit
                self.last_trade_result = 'win'
                
                if profit > self.session_stats['largest_win']:
                    self.session_stats['largest_win'] = profit
                    
            elif profit < self.loss_threshold:
                self.session_stats['losing_trades'] += 1
                self.session_stats['gross_loss'] += abs(profit)
                self.last_trade_result = 'loss'
                
                if profit < self.session_stats['largest_loss']:
                    self.session_stats['largest_loss'] = profit
                    
            else:
                self.session_stats['break_even_trades'] += 1
                self.last_trade_result = 'break_even'
            
            # อัพเดท total profit/loss
            self.session_stats['total_profit'] += profit
            if profit > 0:
                self.session_stats['total_profit'] += profit
            else:
                self.session_stats['total_loss'] += abs(profit)
            
            # อัพเดท lot performance
            if lot_size > 0:
                # อัพเดท profit by lot size
                lot_key = f"{lot_size:.2f}"
                if lot_key not in self.lot_performance['profit_by_lot_size']:
                    self.lot_performance['profit_by_lot_size'][lot_key] = {
                        'total_profit': 0.0,
                        'total_trades': 0,
                        'avg_profit_per_lot': 0.0
                    }
                
                lot_stats = self.lot_performance['profit_by_lot_size'][lot_key]
                lot_stats['total_profit'] += profit
                lot_stats['total_trades'] += 1
                lot_stats['avg_profit_per_lot'] = lot_stats['total_profit'] / lot_stats['total_trades']
                
                # อัพเดท best/worst efficiency
                if profit_per_lot > self.lot_performance['best_lot_efficiency']:
                    self.lot_performance['best_lot_efficiency'] = profit_per_lot
                if profit_per_lot < self.lot_performance['worst_lot_efficiency']:
                    self.lot_performance['worst_lot_efficiency'] = profit_per_lot
            
            # อัพเดท streak tracking
            self._update_streak_tracking()
            
            # คำนวณ risk metrics
            self._update_risk_metrics()
            
            # อัพเดทประวัติรายชั่วโมง
            self._update_hourly_performance('position_close', close_record)
            
            # Auto-save
            self._auto_save_if_needed()
            
            result_text = "WIN" if profit > 0 else "LOSS" if profit < 0 else "B/E"
            print(f"📝 Position close recorded: {result_text} ${profit:.2f} ({lot_size:.2f} lots, ${profit_per_lot:.0f}/lot)")
            
        except Exception as e:
            print(f"❌ Position close recording error: {e}")
    
    # ==========================================
    # 📊 PERFORMANCE CALCULATION - COMPLETE
    # ==========================================
    
    def calculate_performance_metrics(self) -> Dict:
        """
        📊 คำนวณ performance metrics ทั้งหมด (COMPLETE)
        
        Returns:
            Dict: metrics ทั้งหมด
        """
        try:
            total_trades = len(self.position_history)
            
            if total_trades < self.min_trades_for_stats:
                return {
                    'status': 'insufficient_data',
                    'message': f'Need at least {self.min_trades_for_stats} trades for statistics',
                    'current_trades': total_trades,
                    'basic_stats': self._get_basic_session_stats()
                }
            
            # คำนวณ metrics ต่างๆ
            basic_metrics = self._calculate_basic_metrics()
            profitability_metrics = self._calculate_profitability_metrics()
            risk_metrics = self._calculate_risk_metrics()
            lot_metrics = self._calculate_lot_aware_metrics()
            time_metrics = self._calculate_time_based_metrics()
            pattern_metrics = self._calculate_pattern_metrics()
            
            # รวม metrics ทั้งหมด
            complete_metrics = {
                'calculation_time': datetime.now(),
                'total_trades': total_trades,
                'data_period': {
                    'start': self.session_start_time,
                    'end': datetime.now(),
                    'duration_hours': (datetime.now() - self.session_start_time).total_seconds() / 3600
                },
                'basic_metrics': basic_metrics,
                'profitability_metrics': profitability_metrics,
                'risk_metrics': risk_metrics,
                'lot_aware_metrics': lot_metrics,
                'time_based_metrics': time_metrics,
                'pattern_metrics': pattern_metrics,
                'session_stats': self.session_stats.copy(),
                'lot_performance': self.lot_performance.copy()
            }
            
            return complete_metrics
            
        except Exception as e:
            print(f"❌ Performance calculation error: {e}")
            return {'error': str(e)}
    
    def _calculate_basic_metrics(self) -> Dict:
        """คำนวณ basic metrics"""
        try:
            total_trades = len(self.position_history)
            winning_trades = self.session_stats['winning_trades']
            losing_trades = self.session_stats['losing_trades']
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            loss_rate = (losing_trades / total_trades * 100) if total_trades > 0 else 0
            
            avg_win = (self.session_stats['gross_profit'] / winning_trades) if winning_trades > 0 else 0
            avg_loss = (self.session_stats['gross_loss'] / losing_trades) if losing_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'break_even_trades': self.session_stats['break_even_trades'],
                'win_rate_percent': round(win_rate, 2),
                'loss_rate_percent': round(loss_rate, 2),
                'average_win': round(avg_win, 2),
                'average_loss': round(avg_loss, 2),
                'largest_win': self.session_stats['largest_win'],
                'largest_loss': self.session_stats['largest_loss'],
                'avg_win_loss_ratio': round(avg_win / avg_loss, 2) if avg_loss != 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Basic metrics calculation error: {e}")
            return {}
    
    def _calculate_profitability_metrics(self) -> Dict:
        """คำนวณ profitability metrics"""
        try:
            net_profit = self.session_stats['total_profit']
            gross_profit = self.session_stats['gross_profit']
            gross_loss = self.session_stats['gross_loss']
            
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
            
            total_trades = len(self.position_history)
            avg_trade = (net_profit / total_trades) if total_trades > 0 else 0
            
            # คำนวณ ROI (Return on Investment)
            # สมมติ initial capital จาก config หรือใช้ค่าเริ่มต้น
            initial_capital = self.config.get("account", {}).get("initial_capital", 10000)
            roi_percent = (net_profit / initial_capital * 100) if initial_capital > 0 else 0
            
            return {
                'net_profit': round(net_profit, 2),
                'gross_profit': round(gross_profit, 2),
                'gross_loss': round(gross_loss, 2),
                'profit_factor': round(profit_factor, 2),
                'average_trade': round(avg_trade, 2),
                'roi_percent': round(roi_percent, 2),
                'total_return_percent': round(roi_percent, 2),
                'profitable_trade_percent': round((self.session_stats['winning_trades'] / total_trades * 100) if total_trades > 0 else 0, 2)
            }
            
        except Exception as e:
            print(f"❌ Profitability metrics calculation error: {e}")
            return {}
    
    def _calculate_risk_metrics(self) -> Dict:
        """คำนวณ risk metrics"""
        try:
            if not self.position_history:
                return {}
            
            # คำนวณ drawdown
            running_balance = []
            current_balance = 0
            
            for position in self.position_history:
                current_balance += position['profit']
                running_balance.append(current_balance)
            
            # หา maximum drawdown
            peak = running_balance[0]
            max_drawdown = 0
            
            for balance in running_balance:
                if balance > peak:
                    peak = balance
                
                drawdown = peak - balance
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # คำนวณ Sharpe ratio (simplified)
            profits = [p['profit'] for p in self.position_history]
            avg_return = statistics.mean(profits) if profits else 0
            return_std = statistics.stdev(profits) if len(profits) > 1 else 0
            
            # สมมติ risk-free rate = 0 สำหรับ simplicity
            sharpe_ratio = (avg_return / return_std) if return_std > 0 else 0
            
            # Value at Risk (95% confidence)
            var_95 = statistics.quantiles(profits, n=20)[1] if len(profits) >= 20 else min(profits) if profits else 0
            
            return {
                'max_drawdown': round(max_drawdown, 2),
                'max_drawdown_percent': round((max_drawdown / abs(peak) * 100) if peak != 0 else 0, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'profit_factor': round(self.session_stats['gross_profit'] / self.session_stats['gross_loss'], 2) if self.session_stats['gross_loss'] > 0 else 0,
                'recovery_factor': round(self.session_stats['total_profit'] / max_drawdown, 2) if max_drawdown > 0 else 0,
                'var_95_percent': round(var_95, 2),
                'expected_shortfall': round(statistics.mean([p for p in profits if p < var_95]), 2) if profits and var_95 > min(profits) else 0,
                'volatility': round(return_std, 2),
                'max_consecutive_wins': self.session_stats['max_consecutive_wins'],
                'max_consecutive_losses': self.session_stats['max_consecutive_losses']
            }
            
        except Exception as e:
            print(f"❌ Risk metrics calculation error: {e}")
            return {}
    
    def _calculate_lot_aware_metrics(self) -> Dict:
        """คำนวณ lot-aware metrics"""
        try:
            if not self.position_history:
                return {}
            
            total_volume = sum(p['lot_size'] for p in self.position_history)
            total_profit = sum(p['profit'] for p in self.position_history)
            
            avg_profit_per_lot = (total_profit / total_volume) if total_volume > 0 else 0
            
            # Volume-weighted return
            volume_weighted_return = sum(
                p['profit_per_lot'] * p['lot_size'] for p in self.position_history
            ) / total_volume if total_volume > 0 else 0
            
            # Efficiency distribution
            efficiency_data = [p['profit_per_lot'] for p in self.position_history]
            
            return {
                'total_volume_traded': round(total_volume, 2),
                'average_profit_per_lot': round(avg_profit_per_lot, 2),
                'volume_weighted_return': round(volume_weighted_return, 2),
                'best_lot_efficiency': self.lot_performance['best_lot_efficiency'],
                'worst_lot_efficiency': self.lot_performance['worst_lot_efficiency'],
                'lot_efficiency_std': round(statistics.stdev(efficiency_data), 2) if len(efficiency_data) > 1 else 0,
                'lot_efficiency_median': round(statistics.median(efficiency_data), 2) if efficiency_data else 0,
                'lot_size_distribution': self.lot_performance['lot_size_distribution'].copy(),
                'profit_by_lot_size': self.lot_performance['profit_by_lot_size'].copy()
            }
            
        except Exception as e:
            print(f"❌ Lot-aware metrics calculation error: {e}")
            return {}
    
    def _calculate_time_based_metrics(self) -> Dict:
        """คำนวณ time-based metrics"""
        try:
            if not self.position_history:
                return {}
            
            hold_times = [p['hold_time_minutes'] for p in self.position_history]
            avg_hold_time = statistics.mean(hold_times) if hold_times else 0
            
            # แยกตาม market session
            session_performance = {'Asian': [], 'London': [], 'NY': [], 'Other': []}
            
            for position in self.position_history:
                session = position.get('market_session', 'Other')
                if session in session_performance:
                    session_performance[session].append(position['profit'])
            
            session_stats = {}
            for session, profits in session_performance.items():
                if profits:
                    session_stats[f'{session.lower()}_trades'] = len(profits)
                    session_stats[f'{session.lower()}_profit'] = round(sum(profits), 2)
                    session_stats[f'{session.lower()}_avg_profit'] = round(statistics.mean(profits), 2)
                    session_stats[f'{session.lower()}_win_rate'] = round(
                        len([p for p in profits if p > 0]) / len(profits) * 100, 2
                    )
            
            return {
                'average_hold_time_minutes': round(avg_hold_time, 2),
                'shortest_trade_minutes': min(hold_times) if hold_times else 0,
                'longest_trade_minutes': max(hold_times) if hold_times else 0,
                'session_performance': session_stats,
                'hourly_performance': self.hourly_performance.copy()
            }
            
        except Exception as e:
            print(f"❌ Time-based metrics calculation error: {e}")
            return {}
    
    def _calculate_pattern_metrics(self) -> Dict:
        """คำนวณ pattern performance metrics"""
        try:
            if not self.signal_history:
                return {}
            
            pattern_summary = {}
            
            for pattern, stats in self.pattern_performance.items():
                if stats['total_signals'] > 0:
                    pattern_summary[pattern] = {
                        'total_signals': stats['total_signals'],
                        'buy_signals': stats['buy_signals'],
                        'sell_signals': stats['sell_signals'],
                        'avg_strength': round(stats['avg_strength'], 2),
                        'success_rate': round(stats['success_rate'], 2),
                        'total_profit': round(stats['total_profit'], 2),
                        'signals_per_hour': round(
                            stats['total_signals'] / ((datetime.now() - self.session_start_time).total_seconds() / 3600), 2
                        ) if (datetime.now() - self.session_start_time).total_seconds() > 0 else 0
                    }
            
            return {
                'pattern_performance': pattern_summary,
                'most_frequent_pattern': max(self.pattern_performance.keys(), 
                                           key=lambda k: self.pattern_performance[k]['total_signals']) if self.pattern_performance else None,
                'best_performing_pattern': max(self.pattern_performance.keys(),
                                             key=lambda k: self.pattern_performance[k]['total_profit']) if self.pattern_performance else None
            }
            
        except Exception as e:
            print(f"❌ Pattern metrics calculation error: {e}")
            return {}
    
    # ==========================================
    # 🔧 HELPER METHODS - COMPLETE
    # ==========================================
    
    def _detect_market_session(self) -> str:
        """ตรวจจับ market session ปัจจุบัน"""
        try:
            now = datetime.now()
            hour = now.hour
            
            # เวลาไทย (UTC+7) แปลงเป็น UTC
            # Asian: 00:00-09:00 UTC (07:00-16:00 GMT+7)
            # London: 08:00-17:00 UTC (15:00-00:00 GMT+7)
            # NY: 13:00-22:00 UTC (20:00-05:00 GMT+7)
            
            if 0 <= hour < 9:
                return 'Asian'
            elif 8 <= hour < 17:
                return 'London'  
            elif 13 <= hour < 22:
                return 'NY'
            else:
                return 'Other'
                
        except Exception as e:
            print(f"❌ Market session detection error: {e}")
            return 'Unknown'
    
    def _update_hourly_performance(self, event_type: str, event_data: Dict):
        """อัพเดทประวัติรายชั่วโมง"""
        try:
            hour_key = datetime.now().strftime('%Y-%m-%d_%H')
            
            if hour_key not in self.hourly_performance:
                self.hourly_performance[hour_key] = {
                    'signals': 0,
                    'executions': 0,
                    'position_closes': 0,
                    'profit': 0.0,
                    'volume': 0.0
                }
            
            hour_stats = self.hourly_performance[hour_key]
            
            if event_type == 'signal':
                hour_stats['signals'] += 1
            elif event_type == 'execution':
                hour_stats['executions'] += 1
                if event_data.get('success'):
                    hour_stats['volume'] += event_data.get('lot_size', 0)
            elif event_type == 'position_close':
                hour_stats['position_closes'] += 1
                hour_stats['profit'] += event_data.get('profit', 0)
                hour_stats['volume'] += event_data.get('lot_size', 0)
            
        except Exception as e:
            print(f"❌ Hourly performance update error: {e}")
    
    def _update_streak_tracking(self):
        """อัพเดท streak tracking"""
        try:
            if self.last_trade_result is None:
                return
            
            if self.streak_type == self.last_trade_result:
                # เพิ่ม streak เดิม
                self.current_streak += 1
            else:
                # เริ่ม streak ใหม่
                self.streak_type = self.last_trade_result
                self.current_streak = 1
            
            # อัพเดท max streaks
            if self.last_trade_result == 'win':
                self.session_stats['consecutive_wins'] = self.current_streak
                if self.current_streak > self.session_stats['max_consecutive_wins']:
                    self.session_stats['max_consecutive_wins'] = self.current_streak
            elif self.last_trade_result == 'loss':
                self.session_stats['consecutive_losses'] = self.current_streak
                if self.current_streak > self.session_stats['max_consecutive_losses']:
                    self.session_stats['max_consecutive_losses'] = self.current_streak
            
        except Exception as e:
            print(f"❌ Streak tracking update error: {e}")
    
    def _update_risk_metrics(self):
        """อัพเดท risk metrics real-time"""
        try:
            if len(self.position_history) < 2:
                return
            
            profits = [p['profit'] for p in self.position_history]
            
            # คำนวณ running drawdown
            running_balance = 0
            peak = 0
            max_dd = 0
            
            for profit in profits:
                running_balance += profit
                if running_balance > peak:
                    peak = running_balance
                
                drawdown = peak - running_balance
                if drawdown > max_dd:
                    max_dd = drawdown
            
            self.risk_metrics['max_drawdown'] = max_dd
            self.risk_metrics['max_drawdown_percent'] = (max_dd / abs(peak) * 100) if peak != 0 else 0
            
            # อัพเดท profit factor
            gross_profit = sum(p for p in profits if p > 0)
            gross_loss = abs(sum(p for p in profits if p < 0))
            self.risk_metrics['profit_factor'] = (gross_profit / gross_loss) if gross_loss > 0 else 0
            
        except Exception as e:
            print(f"❌ Risk metrics update error: {e}")
    
    def _auto_save_if_needed(self):
        """Auto-save ข้อมูลถ้าถึงเวลา"""
        try:
            if not self.auto_save_enabled or not self.persistence_manager:
                return
            
            time_since_save = (datetime.now() - self.last_save_time).total_seconds() / 60
            
            if time_since_save >= self.save_interval_minutes:
                self.save_to_persistence()
                self.last_save_time = datetime.now()
                
        except Exception as e:
            print(f"❌ Auto-save error: {e}")
    
    def _get_basic_session_stats(self) -> Dict:
        """ดึง basic session stats"""
        try:
            session_duration = (datetime.now() - self.session_start_time).total_seconds() / 3600
            
            return {
                'session_duration_hours': round(session_duration, 2),
                'signals_generated': self.session_stats['signals_generated'],
                'signals_per_hour': round(self.session_stats['signals_generated'] / session_duration, 2) if session_duration > 0 else 0,
                'orders_executed': self.session_stats['orders_executed'],
                'execution_success_rate': round(
                    (self.session_stats['orders_successful'] / self.session_stats['orders_executed'] * 100) 
                    if self.session_stats['orders_executed'] > 0 else 0, 2
                ),
                'current_profit': round(self.session_stats['total_profit'], 2),
                'total_volume_traded': round(self.lot_performance['total_volume_traded'], 2)
            }
            
        except Exception as e:
            print(f"❌ Basic session stats error: {e}")
            return {}
    
    # ==========================================
    # 📊 REPORTING & ANALYSIS - COMPLETE
    # ==========================================
    
    def generate_performance_report(self, report_type: str = 'complete') -> Dict:
        """
        📊 สร้างรายงานผลงาน (COMPLETE)
        
        Args:
            report_type: 'basic', 'detailed', 'complete'
            
        Returns:
            Dict: รายงานผลงาน
        """
        try:
            report = {
                'report_type': report_type,
                'generated_at': datetime.now().isoformat(),
                'system_info': {
                    'symbol': self.symbol,
                    'session_start': self.session_start_time.isoformat(),
                    'session_duration_hours': round((datetime.now() - self.session_start_time).total_seconds() / 3600, 2)
                }
            }
            
            if report_type in ['basic', 'detailed', 'complete']:
                metrics = self.calculate_performance_metrics()
                
                if 'error' in metrics:
                    report['error'] = metrics['error']
                    return report
                
                # Basic metrics for all report types
                report['basic_performance'] = {
                    'total_trades': metrics['total_trades'],
                    'net_profit': metrics.get('profitability_metrics', {}).get('net_profit', 0),
                    'win_rate': metrics.get('basic_metrics', {}).get('win_rate_percent', 0),
                    'profit_factor': metrics.get('profitability_metrics', {}).get('profit_factor', 0),
                    'max_drawdown': metrics.get('risk_metrics', {}).get('max_drawdown', 0),
                    'avg_profit_per_lot': metrics.get('lot_aware_metrics', {}).get('average_profit_per_lot', 0)
                }
                
            if report_type in ['detailed', 'complete']:
                report['detailed_metrics'] = {
                    'profitability': metrics.get('profitability_metrics', {}),
                    'risk_analysis': metrics.get('risk_metrics', {}),
                    'lot_analysis': metrics.get('lot_aware_metrics', {}),
                    'time_analysis': metrics.get('time_based_metrics', {})
                }
                
                # Top patterns
                pattern_metrics = metrics.get('pattern_metrics', {})
                report['pattern_analysis'] = pattern_metrics.get('pattern_performance', {})
                
            if report_type == 'complete':
                # Complete data for full analysis
                report['complete_data'] = {
                    'all_metrics': metrics,
                    'signal_history': self.signal_history[-50:],  # Last 50 signals
                    'execution_history': self.execution_history[-50:],  # Last 50 executions
                    'position_history': self.position_history[-50:],  # Last 50 positions
                    'session_stats': self.session_stats.copy(),
                    'lot_performance': self.lot_performance.copy(),
                    'risk_metrics': self.risk_metrics.copy()
                }
                
                # Performance recommendations
                report['recommendations'] = self._generate_performance_recommendations(metrics)
            
            return report
            
        except Exception as e:
            print(f"❌ Performance report generation error: {e}")
            return {'error': str(e)}
    
    def _generate_performance_recommendations(self, metrics: Dict) -> List[str]:
        """สร้างคำแนะนำจากผลงาน"""
        try:
            recommendations = []
            
            basic_metrics = metrics.get('basic_metrics', {})
            risk_metrics = metrics.get('risk_metrics', {})
            lot_metrics = metrics.get('lot_aware_metrics', {})
            
            # Win rate analysis
            win_rate = basic_metrics.get('win_rate_percent', 0)
            if win_rate < 40:
                recommendations.append("🔴 Win rate ต่ำ (<40%) - พิจารณาปรับ signal criteria")
            elif win_rate > 70:
                recommendations.append("🟢 Win rate สูง (>70%) - ผลงานดีมาก")
            
            # Profit factor analysis
            profit_factor = risk_metrics.get('profit_factor', 0)
            if profit_factor < 1.2:
                recommendations.append("🟡 Profit factor ต่ำ - ควรลด loss size หรือเพิ่ม profit target")
            elif profit_factor > 2.0:
                recommendations.append("🟢 Profit factor สูง - ระบบมีประสิทธิภาพดี")
            
            # Drawdown analysis
            max_dd_percent = risk_metrics.get('max_drawdown_percent', 0)
            if max_dd_percent > 20:
                recommendations.append("🔴 Max drawdown สูง (>20%) - ควรลดขนาดการเทรด")
            elif max_dd_percent < 10:
                recommendations.append("🟢 Max drawdown ควบคุมได้ดี (<10%)")
            
            # Lot efficiency analysis
            avg_profit_per_lot = lot_metrics.get('average_profit_per_lot', 0)
            if avg_profit_per_lot < 10:
                recommendations.append("🟡 Profit per lot ต่ำ - พิจารณาปรับ lot sizing strategy")
            elif avg_profit_per_lot > 50:
                recommendations.append("🟢 Profit per lot สูง - lot efficiency ดีมาก")
            
            # Volume analysis
            total_volume = lot_metrics.get('total_volume_traded', 0)
            if total_volume > 10:
                recommendations.append("⚠️ Volume การเทรดสูง - ควรติดตาม margin usage")
            
            # Consecutive losses
            max_consecutive_losses = risk_metrics.get('max_consecutive_losses', 0)
            if max_consecutive_losses > 5:
                recommendations.append("🔴 Consecutive losses สูง - ควรมี circuit breaker")
            
            # General recommendations
            if len(recommendations) == 0:
                recommendations.append("✅ ผลงานอยู่ในเกณฑ์ดี - คงทิศทางการเทรดเดิม")
            
            return recommendations[:10]  # จำกัดไว้ 10 ข้อ
            
        except Exception as e:
            print(f"❌ Recommendations generation error: {e}")
            return ["❌ Unable to generate recommendations due to calculation error"]
    
    # ==========================================
    # 💾 PERSISTENCE INTEGRATION - COMPLETE
    # ==========================================
    
    def save_to_persistence(self) -> bool:
        """💾 บันทึกข้อมูลผลงานลง persistence"""
        try:
            if not self.persistence_manager:
                print("❌ No persistence manager available")
                return False
            
            # เตรียมข้อมูลสำหรับบันทึก
            performance_data = {
                'session_start': self.session_start_time.isoformat(),
                'last_updated': datetime.now().isoformat(),
                'session_stats': self.session_stats.copy(),
                'lot_performance': self.lot_performance.copy(),
                'risk_metrics': self.risk_metrics.copy(),
                'pattern_performance': self.pattern_performance.copy(),
                'total_signals': len(self.signal_history),
                'total_executions': len(self.execution_history),
                'total_positions': len(self.position_history)
            }
            
            # บันทึกข้อมูลหลัก
            success = self.persistence_manager.save_performance_data(performance_data)
            
            if success:
                # บันทึก signal history
                if self.signal_history:
                    signal_records = [
                        {**record, 'timestamp': record['timestamp'].isoformat() if isinstance(record['timestamp'], datetime) else record['timestamp']}
                        for record in self.signal_history[-1000:]  # เก็บ 1000 รายการล่าสุด
                    ]
                    self.persistence_manager.save_signal_history(signal_records)
                
                print(f"💾 Performance data saved to persistence")
                return True
            else:
                print(f"❌ Failed to save performance data")
                return False
                
        except Exception as e:
            print(f"❌ Save to persistence error: {e}")
            return False
    
    def load_from_persistence(self, performance_data: Dict = None) -> bool:
        """📂 โหลดข้อมูลผลงานจาก persistence"""
        try:
            if not self.persistence_manager and not performance_data:
                print("❌ No persistence manager or data available")
                return False
            
            # โหลดข้อมูลจาก persistence manager หรือใช้ข้อมูลที่ส่งมา
            if performance_data is None:
                performance_data = self.persistence_manager.load_performance_data()
            
            if not performance_data:
                print("📂 No previous performance data found")
                return False
            
            # กู้คืนข้อมูล session stats
            if 'session_stats' in performance_data:
                self.session_stats.update(performance_data['session_stats'])
            
            # กู้คืนข้อมูล lot performance
            if 'lot_performance' in performance_data:
                self.lot_performance.update(performance_data['lot_performance'])
            
            # กู้คืนข้อมูล risk metrics
            if 'risk_metrics' in performance_data:
                self.risk_metrics.update(performance_data['risk_metrics'])
            
            # กู้คืนข้อมูล pattern performance
            if 'pattern_performance' in performance_data:
                self.pattern_performance.update(performance_data['pattern_performance'])
            
            # โหลด signal history ถ้ามี persistence manager
            if self.persistence_manager:
                signal_history = self.persistence_manager.load_signal_history()
                if signal_history:
                    # แปลง timestamp string กลับเป็น datetime
                    for record in signal_history:
                        if isinstance(record.get('timestamp'), str):
                            try:
                                record['timestamp'] = datetime.fromisoformat(record['timestamp'])
                            except:
                                record['timestamp'] = datetime.now()
                    
                    self.signal_history = signal_history
            
            print(f"📂 Performance data loaded from persistence")
            print(f"   Signals: {performance_data.get('total_signals', 0)}")
            print(f"   Total profit: ${self.session_stats.get('total_profit', 0):.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Load from persistence error: {e}")
            return False
    
    # ==========================================
    # 🔧 UTILITY METHODS - COMPLETE
    # ==========================================
    
    def reset_session_stats(self):
        """🔄 รีเซ็ต session statistics"""
        try:
            self.session_start_time = datetime.now()
            self.session_stats = {
                'signals_generated': 0,
                'signals_buy': 0,
                'signals_sell': 0,
                'signals_wait': 0,
                'orders_executed': 0,
                'orders_successful': 0,
                'orders_failed': 0,
                'total_profit': 0.0,
                'total_loss': 0.0,
                'gross_profit': 0.0,
                'gross_loss': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
                'break_even_trades': 0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'consecutive_wins': 0,
                'consecutive_losses': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0
            }
            
            self.lot_performance = {
                'total_volume_traded': 0.0,
                'avg_profit_per_lot': 0.0,
                'best_lot_efficiency': 0.0,
                'worst_lot_efficiency': 0.0,
                'volume_weighted_return': 0.0,
                'lot_size_distribution': {},
                'profit_by_lot_size': {}
            }
            
            self.risk_metrics = {
                'max_drawdown': 0.0,
                'max_drawdown_percent': 0.0,
                'sharpe_ratio': 0.0,
                'profit_factor': 0.0,
                'recovery_factor': 0.0,
                'calmar_ratio': 0.0,
                'var_95': 0.0,
                'expected_shortfall': 0.0
            }
            
            # ล้าง history (เก็บแค่ 100 รายการล่าสุด)
            self.signal_history = self.signal_history[-100:] if len(self.signal_history) > 100 else []
            self.execution_history = self.execution_history[-100:] if len(self.execution_history) > 100 else []
            self.position_history = self.position_history[-100:] if len(self.position_history) > 100 else []
            
            self.last_trade_result = None
            self.current_streak = 0
            self.streak_type = None
            
            print(f"🔄 Session statistics reset")
            
        except Exception as e:
            print(f"❌ Reset session stats error: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """🧹 ลบข้อมูลเก่า"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # ลบ signals เก่า
            self.signal_history = [
                record for record in self.signal_history
                if record.get('timestamp', datetime.now()) > cutoff_date
            ]
            
            # ลบ executions เก่า
            self.execution_history = [
                record for record in self.execution_history
                if record.get('timestamp', datetime.now()) > cutoff_date
            ]
            
            # ลบ positions เก่า
            self.position_history = [
                record for record in self.position_history
                if record.get('timestamp', datetime.now()) > cutoff_date
            ]
            
            # ลบ hourly performance เก่า
            old_hours = [
                hour_key for hour_key in self.hourly_performance.keys()
                if datetime.strptime(hour_key.split('_')[0], '%Y-%m-%d') < cutoff_date
            ]
            
            for hour_key in old_hours:
                del self.hourly_performance[hour_key]
            
            print(f"🧹 Cleaned data older than {days_to_keep} days")
            
        except Exception as e:
            print(f"❌ Cleanup old data error: {e}")
    
    def get_performance_summary(self) -> str:
        """📋 สรุปผลงานแบบ text"""
        try:
            metrics = self.calculate_performance_metrics()
            
            if 'error' in metrics:
                return f"❌ Error calculating performance: {metrics['error']}"
            
            if metrics.get('status') == 'insufficient_data':
                basic_stats = metrics.get('basic_stats', {})
                return f"""
📈 Performance Summary (Limited Data)
═══════════════════════════════════════
⏰ Session Duration: {basic_stats.get('session_duration_hours', 0):.1f} hours
📊 Signals Generated: {basic_stats.get('signals_generated', 0)}
📈 Signals/Hour: {basic_stats.get('signals_per_hour', 0):.1f}
⚡ Orders Executed: {basic_stats.get('orders_executed', 0)}
✅ Execution Rate: {basic_stats.get('execution_success_rate', 0):.1f}%
💰 Current Profit: ${basic_stats.get('current_profit', 0):.2f}
📦 Volume Traded: {basic_stats.get('total_volume_traded', 0):.2f} lots

ℹ️  Need at least {self.min_trades_for_stats} completed trades for full statistics
"""
            
            basic = metrics.get('basic_metrics', {})
            profit = metrics.get('profitability_metrics', {})
            risk = metrics.get('risk_metrics', {})
            lot = metrics.get('lot_aware_metrics', {})
            
            return f"""
📈 Performance Summary
═══════════════════════════════════════
📊 Basic Metrics:
   • Total Trades: {basic.get('total_trades', 0)}
   • Win Rate: {basic.get('win_rate_percent', 0):.1f}%
   • Avg Win: ${basic.get('average_win', 0):.2f}
   • Avg Loss: ${basic.get('average_loss', 0):.2f}
   • Win/Loss Ratio: {basic.get('avg_win_loss_ratio', 0):.2f}

💰 Profitability:
   • Net Profit: ${profit.get('net_profit', 0):.2f}
   • Profit Factor: {profit.get('profit_factor', 0):.2f}
   • ROI: {profit.get('roi_percent', 0):.1f}%
   • Avg Trade: ${profit.get('average_trade', 0):.2f}

🛡️ Risk Analysis:
   • Max Drawdown: ${risk.get('max_drawdown', 0):.2f} ({risk.get('max_drawdown_percent', 0):.1f}%)
   • Sharpe Ratio: {risk.get('sharpe_ratio', 0):.2f}
   • Max Consecutive Losses: {risk.get('max_consecutive_losses', 0)}

📦 Lot Analysis:
   • Total Volume: {lot.get('total_volume_traded', 0):.2f} lots
   • Profit/Lot: ${lot.get('average_profit_per_lot', 0):.0f}
   • Best Efficiency: ${lot.get('best_lot_efficiency', 0):.0f}/lot
   • Worst Efficiency: ${lot.get('worst_lot_efficiency', 0):.0f}/lot
"""
            
        except Exception as e:
            return f"❌ Error generating summary: {e}"
    
    def is_ready(self) -> bool:
        """✅ ตรวจสอบความพร้อม"""
        return True
    
    def get_current_metrics(self) -> Dict:
        """
        📊 ดึง performance metrics ปัจจุบัน - MAIN METHOD
        
        Returns:
            Dict: performance metrics ปัจจุบัน
        """
        try:
            # ใช้ method ที่มีอยู่แล้ว
            complete_metrics = self.calculate_performance_metrics()
            
            if 'error' in complete_metrics:
                # ส่งข้อมูลพื้นฐานถ้า error
                return self._get_basic_session_stats()
            
            if complete_metrics.get('status') == 'insufficient_data':
                # ส่งข้อมูลพื้นฐานถ้าข้อมูลไม่พอ
                return complete_metrics.get('basic_stats', {})
            
            # Extract key metrics สำหรับ display
            basic_metrics = complete_metrics.get('basic_metrics', {})
            profitability_metrics = complete_metrics.get('profitability_metrics', {})
            lot_metrics = complete_metrics.get('lot_aware_metrics', {})
            
            return {
                'total_trades': basic_metrics.get('total_trades', 0),
                'win_rate_percent': basic_metrics.get('win_rate_percent', 0),
                'net_profit': profitability_metrics.get('net_profit', 0),
                'profit_factor': profitability_metrics.get('profit_factor', 0),
                'avg_profit_per_lot': lot_metrics.get('average_profit_per_lot', 0),
                'total_volume_traded': lot_metrics.get('total_volume_traded', 0),
                'total_signals': self.session_stats.get('signals_generated', 0),
                'successful_executions': self.session_stats.get('orders_successful', 0),
                'session_duration_hours': (datetime.now() - self.session_start_time).total_seconds() / 3600,
                'largest_win': self.session_stats.get('largest_win', 0),
                'largest_loss': self.session_stats.get('largest_loss', 0),
                'current_streak': getattr(self, 'current_streak', 0),
                'streak_type': getattr(self, 'streak_type', 'none')
            }
            
        except Exception as e:
            print(f"❌ Get current metrics error: {e}")
            return {
                'total_trades': 0,
                'win_rate_percent': 0,
                'net_profit': 0,
                'profit_factor': 0,
                'error': str(e)
            }
        """ℹ️ ข้อมูล Performance Tracker"""
        return {
            'name': 'Pure Candlestick Performance Tracker',
            'version': '2.0.0',
            'symbol': self.symbol,
            'session_start': self.session_start_time.isoformat(),
            'tracking_enabled': True,
            'persistence_enabled': self.persistence_manager is not None,
            'auto_save_enabled': self.auto_save_enabled,
            'data_counts': {
                'signals': len(self.signal_history),
                'executions': len(self.execution_history),
                'positions': len(self.position_history),
                'patterns_tracked': len(self.pattern_performance)
            },
            'thresholds': {
                'profit_threshold': self.profit_threshold,
                'loss_threshold': self.loss_threshold,
                'min_trades_for_stats': self.min_trades_for_stats
            }
        }