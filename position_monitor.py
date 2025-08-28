"""
💰 Smart Position Monitor & Manager - LOT-AWARE VERSION
position_monitor.py (ENHANCED)

🔧 MAJOR IMPROVEMENTS:
✅ Lot-Aware Analysis (profit per lot, volume efficiency)
✅ Margin Impact Optimization 
✅ Volume-Weighted Portfolio Balance
✅ Partial Position Closing
✅ Dynamic Efficiency Thresholds

🚀 Features:
✅ Real-time Position Monitoring
✅ Smart Recovery (lot-balanced combinations)
✅ Margin Optimization (ลดการใช้ margin)
✅ Volume-Weighted Portfolio Balance
✅ Intelligent Close Combinations
✅ Efficiency-Based Decision Making
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import statistics
import time

class PositionMonitor:
    """
    💰 Enhanced Position Monitor - Lot-Aware Version
    
    🎯 เน้น Margin Optimization + Volume Balance
    ติดตามออเดอร์และหาโอกาสปิดออเดอร์อัจฉริยะแบบ lot-aware
    """
    
    def __init__(self, mt5_connector, config: Dict):
        """
        🔧 เริ่มต้น Enhanced Position Monitor
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # การตั้งค่า position management
        self.position_config = config.get("position_management", {})
        self.symbol = config.get("trading", {}).get("symbol", "XAUUSD.v")
        
        # 🆕 LOT-AWARE SETTINGS
        self.min_efficiency_threshold = self.position_config.get("min_efficiency_per_lot", 50.0)  # $/lot
        self.volume_balance_tolerance = self.position_config.get("volume_balance_tolerance", 0.3)  # 30%
        self.partial_close_enabled = self.position_config.get("partial_close_enabled", True)
        self.min_partial_volume = self.position_config.get("min_partial_volume", 0.01)
        
        # 🆕 MARGIN OPTIMIZATION SETTINGS
        self.margin_efficiency_weight = 0.4  # น้ำหนัก margin efficiency
        self.profit_efficiency_weight = 0.6  # น้ำหนัก profit efficiency
        self.high_margin_usage_threshold = 70.0  # % เมื่อ margin usage สูง
        
        # Smart close settings (ปรับใหม่)
        self.max_losing_age_hours = self.position_config.get("max_losing_age_hours", 8)
        self.min_net_profit_to_close = self.position_config.get("min_net_profit_to_close", 2.0)  # ลดเหลือ $2
        self.portfolio_balance_threshold = self.position_config.get("portfolio_balance_threshold", 0.65)  # ปรับเป็น 65%
        
        # Emergency settings
        self.max_total_loss = self.position_config.get("max_total_loss", -500.0)
        self.critical_margin_level = self.position_config.get("critical_margin_level", 150.0)
        
        # Tracking
        self.position_cache = {}
        self.last_update_time = datetime.min
        self.cache_duration_seconds = 3
        
        # 🆕 LOT TRACKING STATISTICS
        self.lot_stats = {
            'total_buy_volume': 0.0,
            'total_sell_volume': 0.0,
            'avg_profit_per_lot_buy': 0.0,
            'avg_profit_per_lot_sell': 0.0,
            'volume_imbalance_ratio': 0.0,
            'margin_efficiency_score': 0.0
        }
        
        # Statistics
        self.close_stats = {
            'lot_aware_closes': 0,
            'margin_optimization_closes': 0,
            'volume_balance_closes': 0,
            'partial_closes': 0,
            'total_margin_freed': 0.0,
            'total_efficiency_improved': 0.0
        }
        
        print(f"💰 Enhanced Position Monitor initialized for {self.symbol}")
        print(f"   🔢 Min efficiency: ${self.min_efficiency_threshold}/lot")
        print(f"   ⚖️ Volume balance tolerance: {self.volume_balance_tolerance:.1%}")
        print(f"   🔄 Partial close enabled: {self.partial_close_enabled}")
        print(f"   📊 Margin efficiency weight: {self.margin_efficiency_weight:.1%}")
    
    # ==========================================
    # 📊 ENHANCED POSITION RETRIEVAL & ANALYSIS
    # ==========================================
    
    def get_all_positions(self) -> List[Dict]:
        """
        📊 ดึงออเดอร์พร้อมการวิเคราะห์ lot-aware - ENHANCED
        """
        try:
            if not self.mt5_connector.is_connected:
                return []
            
            # ตรวจสอบ cache
            if self._is_cache_valid():
                return list(self.position_cache.values())
            
            # ดึงข้อมูล positions + account info
            raw_positions = mt5.positions_get(symbol=self.symbol)
            account_info = self.mt5_connector.get_account_info()
            
            if raw_positions is None:
                raw_positions = []
            
            # แสดง log แค่เมื่อมี positions หรือทุกๆ 20 ครั้ง
            if not hasattr(self, '_position_check_count'):
                self._position_check_count = 0
                
            if len(raw_positions) > 0:
                print(f"📊 มี {len(raw_positions)} positions")
            else:
                self._position_check_count += 1
                if self._position_check_count % 20 == 0:
                    print(f"📊 ไม่มี positions (check #{self._position_check_count})")
            
            if len(raw_positions) == 0:
                self.position_cache = {}
                return []
            
            # แปลงและเพิ่มการวิเคราะห์ lot-aware
            processed_positions = []
            current_time = datetime.now()
            
            for pos in raw_positions:
                try:
                    # ข้อมูลพื้นฐาน
                    commission = getattr(pos, 'commission', 0.0)
                    swap = getattr(pos, 'swap', 0.0)
                    comment = getattr(pos, 'comment', '')
                    magic = getattr(pos, 'magic', 0)
                    
                    position_data = {
                        'id': pos.ticket,
                        'symbol': pos.symbol,
                        'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                        'volume': float(pos.volume),
                        'price_open': float(pos.price_open),
                        'price_current': float(pos.price_current),
                        'profit': float(pos.profit),
                        'swap': float(swap),
                        'commission': float(commission),
                        'magic': magic,
                        'comment': comment,
                        'time_open': datetime.fromtimestamp(pos.time),
                    }
                    
                    # คำนวณข้อมูลพื้นฐาน
                    open_time = position_data['time_open']
                    age_timedelta = current_time - open_time
                    total_pnl = position_data['profit'] + position_data['swap'] + position_data['commission']
                    
                    position_data['age'] = self._format_position_age(age_timedelta)
                    position_data['age_hours'] = age_timedelta.total_seconds() / 3600
                    position_data['total_pnl'] = round(total_pnl, 2)
                    
                    # LOT-AWARE ANALYSIS
                    volume = position_data['volume']
                    position_data['profit_per_lot'] = round(total_pnl / volume, 2) if volume > 0 else 0
                    position_data['absolute_efficiency'] = abs(position_data['profit_per_lot'])
                    
                    # MARGIN ANALYSIS
                    if account_info and account_info.get('margin', 0) > 0:
                        position_value = position_data['price_current'] * volume
                        leverage = account_info.get('leverage', 100)
                        estimated_margin = position_value / leverage
                        
                        position_data['estimated_margin'] = round(estimated_margin, 2)
                        position_data['margin_efficiency'] = round(total_pnl / estimated_margin, 4) if estimated_margin > 0 else 0
                        position_data['margin_per_lot'] = round(estimated_margin / volume, 2) if volume > 0 else 0
                    else:
                        position_data['estimated_margin'] = 0
                        position_data['margin_efficiency'] = 0
                        position_data['margin_per_lot'] = 0
                    
                    # ENHANCED STATUS CLASSIFICATION
                    position_data['status'] = self._classify_position_status_enhanced(position_data)
                    position_data['efficiency_category'] = self._classify_efficiency_category(position_data)
                    position_data['close_priority'] = self._calculate_close_priority(position_data)
                    
                    processed_positions.append(position_data)
                    
                except Exception as e:
                    ticket = getattr(pos, 'ticket', 'unknown')
                    continue
            
            # UPDATE LOT STATISTICS
            self._update_portfolio_lot_stats(processed_positions)
            
            # อัพเดท cache
            self.position_cache = {pos['id']: pos for pos in processed_positions}
            self.last_update_time = current_time
            
            return processed_positions
            
        except Exception as e:
            return []
       
    def _classify_position_status_enhanced(self, position: Dict) -> str:
        """🏷️ จำแนกสถานะ Position แบบ Lot-Aware"""
        try:
            total_pnl = position.get('total_pnl', 0)
            profit_per_lot = position.get('profit_per_lot', 0)
            age_hours = position.get('age_hours', 0)
            volume = position.get('volume', 0)
            
            # 🆕 EFFICIENCY-BASED CLASSIFICATION
            if profit_per_lot >= self.min_efficiency_threshold:
                return 'high_efficiency'
            elif profit_per_lot >= self.min_efficiency_threshold * 0.5:
                return 'medium_efficiency'
            elif total_pnl > self.min_net_profit_to_close and volume >= 0.05:  # กำไรสุทธิ + volume พอสมควร
                return 'profitable'
            elif profit_per_lot < -self.min_efficiency_threshold:
                if age_hours > self.max_losing_age_hours:
                    return 'high_risk_old'
                else:
                    return 'high_risk'
            elif total_pnl < -50.0:  # ขาดทุนมาก
                return 'heavy_loss'
            elif age_hours > self.max_losing_age_hours and total_pnl < 0:
                return 'old_losing'
            elif total_pnl < 0:
                return 'losing'
            else:
                return 'neutral'
                
        except Exception as e:
            print(f"❌ Enhanced position classification error: {e}")
            return 'unknown'
    
    def _classify_efficiency_category(self, position: Dict) -> str:
        """📊 จำแนกหมวดหมู่ Efficiency"""
        try:
            profit_per_lot = position.get('profit_per_lot', 0)
            margin_efficiency = position.get('margin_efficiency', 0)
            
            # รวม efficiency score
            overall_efficiency = (profit_per_lot * 0.7) + (margin_efficiency * 100 * 0.3)
            
            if overall_efficiency >= 100:
                return 'excellent'
            elif overall_efficiency >= 50:
                return 'good'
            elif overall_efficiency >= 0:
                return 'fair'
            elif overall_efficiency >= -50:
                return 'poor'
            else:
                return 'terrible'
                
        except Exception as e:
            return 'unknown'
    
    def _calculate_close_priority(self, position: Dict) -> float:
        """🎯 คำนวณ Priority การปิด (0-1, สูง = ปิดก่อน)"""
        try:
            profit_per_lot = position.get('profit_per_lot', 0)
            age_hours = position.get('age_hours', 0)
            margin_efficiency = position.get('margin_efficiency', 0)
            volume = position.get('volume', 0)
            
            # Component scores
            profit_score = max(0, min(1, (profit_per_lot + 100) / 200))  # normalize -100 to +100 → 0 to 1
            age_score = min(1, age_hours / 48)  # normalize 0-48h → 0-1
            margin_score = max(0, min(1, (margin_efficiency + 0.5) / 1.0))  # normalize margin efficiency
            volume_score = min(1, volume / 1.0)  # larger positions = higher priority
            
            # Weighted priority
            priority = (
                profit_score * 0.4 +      # กำไร per lot
                age_score * 0.3 +         # อายุ
                margin_score * 0.2 +      # margin efficiency  
                volume_score * 0.1        # ขนาด volume
            )
            
            return round(priority, 3)
            
        except Exception as e:
            return 0.5
    
    def _update_portfolio_lot_stats(self, positions: List[Dict]):
        """อัพเดทสถิติ portfolio - แก้ zero division และ inf values"""
        try:
            if not positions:
                # รีเซ็ตค่าเมื่อไม่มี positions
                self.lot_stats = {
                    'total_buy_volume': 0.0,
                    'total_sell_volume': 0.0, 
                    'avg_profit_per_lot_buy': 0.0,
                    'avg_profit_per_lot_sell': 0.0,
                    'volume_imbalance_ratio': 0.0,
                    'margin_efficiency_score': 0.0
                }
                return
            
            # คำนวณ volume และ profit โดยแยก type
            buy_positions = [p for p in positions if p.get('type') == 'BUY']
            sell_positions = [p for p in positions if p.get('type') == 'SELL']
            
            total_buy_volume = sum(p.get('volume', 0) for p in buy_positions)
            total_sell_volume = sum(p.get('volume', 0) for p in sell_positions)
            
            # คำนวณ average profit per lot - แก้ zero division
            if total_buy_volume > 0:
                total_buy_profit = sum(p.get('total_pnl', 0) for p in buy_positions)
                avg_profit_buy = total_buy_profit / total_buy_volume
            else:
                avg_profit_buy = 0.0
            
            if total_sell_volume > 0:
                total_sell_profit = sum(p.get('total_pnl', 0) for p in sell_positions)
                avg_profit_sell = total_sell_profit / total_sell_volume
            else:
                avg_profit_sell = 0.0
            
            # คำนวณ volume imbalance - แก้ zero division
            total_volume = total_buy_volume + total_sell_volume
            if total_volume > 0:
                imbalance = abs(total_buy_volume - total_sell_volume) / total_volume
            else:
                imbalance = 0.0
            
            # คำนวณ margin efficiency - แก้ inf values
            total_estimated_margin = sum(p.get('estimated_margin', 0) for p in positions)
            total_profit = sum(p.get('total_pnl', 0) for p in positions)
            
            if total_estimated_margin > 0:
                margin_efficiency = total_profit / total_estimated_margin
            else:
                margin_efficiency = 0.0
            
            # อัพเดทสถิติ
            self.lot_stats = {
                'total_buy_volume': round(total_buy_volume, 2),
                'total_sell_volume': round(total_sell_volume, 2),
                'avg_profit_per_lot_buy': round(avg_profit_buy, 1),
                'avg_profit_per_lot_sell': round(avg_profit_sell, 1),
                'volume_imbalance_ratio': round(imbalance, 3),
                'margin_efficiency_score': round(margin_efficiency, 4)
            }
            
            # แสดง log แบบสั้นๆ ทุกๆ 10 ครั้ง
            if not hasattr(self, '_stats_log_count'):
                self._stats_log_count = 0
                
            self._stats_log_count += 1
            if self._stats_log_count % 10 == 0:
                print(f"Portfolio: {total_buy_volume:.2f} BUY, {total_sell_volume:.2f} SELL lots")
                print(f"Efficiency: ${avg_profit_buy:.1f}/lot BUY, ${avg_profit_sell:.1f}/lot SELL") 
                print(f"Imbalance: {imbalance:.1%}")
            
        except Exception as e:
            print(f"Portfolio stats error: {e}")
            self.lot_stats = {
                'total_buy_volume': 0.0,
                'total_sell_volume': 0.0,
                'avg_profit_per_lot_buy': 0.0,
                'avg_profit_per_lot_sell': 0.0,
                'volume_imbalance_ratio': 0.0,
                'margin_efficiency_score': 0.0
            }
    
    # ==========================================
    # 🧠 ENHANCED SMART CLOSE ANALYSIS
    # ==========================================
    
    def check_smart_close_opportunities(self) -> List[Dict]:
        """
        🧠 หาโอกาสปิดออเดอร์ - ENHANCED LOT-AWARE VERSION
        
        Returns:
            List[Dict]: รายการ close actions ที่แนะนำ (เรียงตาม priority)
        """
        try:
            positions = self.get_all_positions()
            
            if not positions:
                return []
            
            close_opportunities = []
            
            # 🆕 1. Margin Optimization Analysis (สำคัญสุด)
            margin_actions = self._find_margin_optimization_opportunities(positions)
            close_opportunities.extend(margin_actions)
            
            # 🆕 2. Volume Balance Analysis (สำคัญรอง)
            balance_actions = self._find_volume_balance_opportunities(positions)
            close_opportunities.extend(balance_actions)
            
            # 🆕 3. Lot-Aware Recovery Analysis
            recovery_actions = self._find_lot_aware_recovery_opportunities(positions)
            close_opportunities.extend(recovery_actions)
            
            # 4. Enhanced Profit Analysis
            profit_actions = self._find_enhanced_profit_opportunities(positions)
            close_opportunities.extend(profit_actions)
            
            # เรียงตาม priority (ต่ำ = สำคัญกว่า)
            close_opportunities.sort(key=lambda x: x.get('priority', 10))
            
            if close_opportunities:
                print(f"🧠 Found {len(close_opportunities)} enhanced close opportunities")
                for i, action in enumerate(close_opportunities[:3]):  # แสดง 3 อันดับแรก
                    print(f"   {i+1}. {action.get('action_type')} (Priority: {action.get('priority')})")
            
            return close_opportunities
            
        except Exception as e:
            print(f"❌ Enhanced smart close analysis error: {e}")
            return []
    
    def _find_margin_optimization_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """หาโอกาส Margin Optimization - แก้ปัญหา inf% และ logic"""
        try:
            margin_actions = []
            
            # เช็ค positions ก่อน - ถ้าไม่มี positions จริงๆ
            if not positions or len(positions) == 0:
                return margin_actions
            
            # ตรวจสอบ margin usage ปัจจุบัน
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                return margin_actions
            
            margin_level = account_info.get('margin_level', 1000)
            margin_used = account_info.get('margin', 0)
            
            # แสดง margin level ที่อ่านง่าย
            if margin_level == float('inf') or margin_used == 0:
                print(f"Margin analysis (No Margin Used) - {len(positions)} positions")
            elif margin_level > 10000:
                print(f"Margin analysis (Very High) - {len(positions)} positions")
            else:
                print(f"Margin analysis ({margin_level:.1f}%) - {len(positions)} positions")
            
            # เช็ค margin pressure จริงๆ - ใช้ margin ที่ใช้จริงเป็นเกณฑ์
            has_margin_pressure = False
            
            if margin_used > 0:  # มี margin ที่ใช้จริง
                if margin_level < 300 and margin_level != float('inf'):
                    has_margin_pressure = True
                    print("   ⚠️ มี margin pressure - กำลังหา optimization")
            
            # ถ้ามี margin pressure หาวิธี optimization
            if has_margin_pressure:
                
                # หา positions ที่มี margin efficiency ต่ำ
                low_efficiency_positions = [
                    p for p in positions 
                    if p.get('margin_efficiency', 0) < 0.001
                    and p.get('estimated_margin', 0) > 50
                ]
                
                if low_efficiency_positions:
                    print(f"   พบ {len(low_efficiency_positions)} positions ที่ไม่คุ้ม margin")
                
                # เรียงตาม margin usage (มากไปน้อย)
                low_efficiency_positions.sort(key=lambda x: x.get('estimated_margin', 0), reverse=True)
                
                for pos in low_efficiency_positions[:5]:
                    
                    # หา hedge partner สำหรับ position นี้
                    hedge_partners = self._find_hedge_partners_for_position(pos, positions)
                    
                    if hedge_partners:
                        total_margin_freed = pos.get('estimated_margin', 0) + sum(p.get('estimated_margin', 0) for p in hedge_partners)
                        total_profit = pos.get('total_pnl', 0) + sum(p.get('total_pnl', 0) for p in hedge_partners)
                        
                        if total_profit >= -5.0:  # ยอมขาดทุนเล็กน้อย
                            margin_action = {
                                'action_type': 'margin_optimization',
                                'primary_position': pos['id'],
                                'hedge_positions': [p['id'] for p in hedge_partners],
                                'margin_freed': total_margin_freed,
                                'net_profit': total_profit,
                                'efficiency_gain': total_margin_freed / max(abs(total_profit), 1),
                                'priority': 1,
                                'reason': f"Free ${total_margin_freed:.0f} margin, Net: ${total_profit:.2f}"
                            }
                            margin_actions.append(margin_action)
            else:
                # ไม่มี margin pressure - ไม่ต้องทำอะไร
                if len(positions) > 0:
                    print("   ไม่จำเป็นต้อง optimize margin")
            
            return margin_actions
            
        except Exception as e:
            print(f"Margin optimization error: {e}")
            return []
    
    def _find_volume_balance_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """⚖️ หาโอกาส Volume Balance - ENHANCED"""
        try:
            balance_actions = []
            
            # คำนวณ volume imbalance
            buy_positions = [p for p in positions if p.get('type') == 'BUY']
            sell_positions = [p for p in positions if p.get('type') == 'SELL']
            
            total_buy_volume = sum(p.get('volume', 0) for p in buy_positions)
            total_sell_volume = sum(p.get('volume', 0) for p in sell_positions)
            total_volume = total_buy_volume + total_sell_volume
            
            if total_volume < 0.1:  # volume น้อยเกินไป
                return balance_actions
            
            buy_ratio = total_buy_volume / total_volume
            sell_ratio = total_sell_volume / total_volume
            imbalance = abs(buy_ratio - sell_ratio)
            
            print(f"⚖️ Volume balance analysis:")
            print(f"   📊 BUY: {total_buy_volume:.2f} lots ({buy_ratio:.1%})")
            print(f"   📊 SELL: {total_sell_volume:.2f} lots ({sell_ratio:.1%})")
            print(f"   📊 Imbalance: {imbalance:.1%}")
            
            # ถ้า imbalance เกิน tolerance
            if imbalance > self.volume_balance_tolerance:
                
                if buy_ratio > sell_ratio:
                    # BUY เยอะเกินไป - หาโอกาสปิด BUY
                    target_close_volume = (total_buy_volume - total_sell_volume) / 2
                    close_candidates = self._find_optimal_volume_close_set(buy_positions, target_close_volume, 'reduce_buy')
                    
                else:
                    # SELL เยอะเกินไป - หาโอกาสปิด SELL  
                    target_close_volume = (total_sell_volume - total_buy_volume) / 2
                    close_candidates = self._find_optimal_volume_close_set(sell_positions, target_close_volume, 'reduce_sell')
                
                if close_candidates:
                    total_net_profit = sum(p.get('total_pnl', 0) for p in close_candidates)
                    total_close_volume = sum(p.get('volume', 0) for p in close_candidates)
                    
                    if total_net_profit >= -10.0:  # ยอมขาดทุนเล็กน้อยเพื่อ balance
                        balance_action = {
                            'action_type': 'volume_balance',
                            'positions_to_close': [p['id'] for p in close_candidates],
                            'volume_to_close': total_close_volume,
                            'net_profit': total_net_profit,
                            'balance_improvement': target_close_volume,
                            'priority': 2,
                            'reason': f"Balance portfolio: close {total_close_volume:.2f} lots for ${total_net_profit:.2f}"
                        }
                        balance_actions.append(balance_action)
            
            return balance_actions
            
        except Exception as e:
            print(f"❌ Volume balance opportunities error: {e}")
            return []
    
    def _find_lot_aware_recovery_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """🎯 หาโอกาส Recovery แบบ Lot-Aware - COMPLETELY NEW"""
        try:
            recovery_actions = []
            
            # แยก efficient vs inefficient positions
            high_efficiency = [p for p in positions if p.get('efficiency_category') in ['excellent', 'good']]
            low_efficiency = [p for p in positions if p.get('efficiency_category') in ['poor', 'terrible']]
            
            if not high_efficiency or not low_efficiency:
                return recovery_actions
            
            print(f"🎯 Lot-aware recovery: {len(high_efficiency)} efficient vs {len(low_efficiency)} inefficient")
            
            # หาการจับคู่ที่ optimal
            for inefficient_pos in low_efficiency:
                
                inefficient_volume = inefficient_pos.get('volume', 0)
                inefficient_pnl = inefficient_pos.get('total_pnl', 0)
                inefficient_margin = inefficient_pos.get('estimated_margin', 0)
                
                # หา efficient positions ที่สามารถชดเชย
                recovery_combination = self._find_optimal_recovery_combination(
                    inefficient_pos, high_efficiency, positions
                )
                
                if recovery_combination:
                    total_volume_match = recovery_combination['volume_match_ratio']
                    net_result = recovery_combination['net_profit']
                    margin_freed = recovery_combination['margin_freed']
                    
                    # ต้องมี net positive และ volume match ดี
                    if net_result >= 0 and total_volume_match >= 0.8:  # 80% volume match
                        
                        recovery_action = {
                            'action_type': 'lot_aware_recovery',
                            'target_position': inefficient_pos['id'],
                            'recovery_positions': recovery_combination['position_ids'],
                            'volume_match_ratio': total_volume_match,
                            'net_profit': net_result,
                            'margin_freed': margin_freed,
                            'inefficient_volume': inefficient_volume,
                            'recovery_volume': recovery_combination['total_volume'],
                            'priority': 3,
                            'reason': f"Lot-aware recovery: ${net_result:.2f} profit, {total_volume_match:.1%} volume match"
                        }
                        recovery_actions.append(recovery_action)
            
            return recovery_actions
            
        except Exception as e:
            print(f"❌ Lot-aware recovery error: {e}")
            return []
    
    def _find_optimal_recovery_combination(self, target_pos: Dict, candidate_positions: List[Dict], all_positions: List[Dict]) -> Optional[Dict]:
        """🔍 หา Recovery Combination ที่ Optimal สำหรับ Position หนึ่ง"""
        try:
            target_volume = target_pos.get('volume', 0)
            target_pnl = target_pos.get('total_pnl', 0)
            target_margin = target_pos.get('estimated_margin', 0)
            
            # ลองหา combinations ต่างๆ (1-4 positions)
            best_combination = None
            best_score = -999999
            
            # Single position recovery
            for candidate in candidate_positions:
                if candidate['id'] == target_pos['id']:
                    continue
                    
                combination_score = self._evaluate_recovery_combination([candidate], target_pos)
                if combination_score['score'] > best_score:
                    best_combination = combination_score
                    best_score = combination_score['score']
            
            # Pair recovery
            for i, pos1 in enumerate(candidate_positions):
                for j, pos2 in enumerate(candidate_positions[i+1:], i+1):
                    if pos1['id'] == target_pos['id'] or pos2['id'] == target_pos['id']:
                        continue
                        
                    combination_score = self._evaluate_recovery_combination([pos1, pos2], target_pos)
                    if combination_score['score'] > best_score:
                        best_combination = combination_score
                        best_score = combination_score['score']
            
            # Triple recovery (เฉพาะกรณีจำเป็น)
            if best_score < 0.5 and len(candidate_positions) >= 3:
                for i, pos1 in enumerate(candidate_positions[:3]):
                    for j, pos2 in enumerate(candidate_positions[i+1:4], i+1):
                        for k, pos3 in enumerate(candidate_positions[j+1:5], j+1):
                            if any(p['id'] == target_pos['id'] for p in [pos1, pos2, pos3]):
                                continue
                                
                            combination_score = self._evaluate_recovery_combination([pos1, pos2, pos3], target_pos)
                            if combination_score['score'] > best_score:
                                best_combination = combination_score
                                best_score = combination_score['score']
            
            return best_combination if best_score > 0.3 else None
            
        except Exception as e:
            print(f"❌ Optimal recovery combination error: {e}")
            return None
    
    def _evaluate_recovery_combination(self, recovery_positions: List[Dict], target_pos: Dict) -> Dict:
        """📊 ประเมิน Recovery Combination"""
        try:
            # คำนวณผลรวม
            recovery_volume = sum(p.get('volume', 0) for p in recovery_positions)
            recovery_profit = sum(p.get('total_pnl', 0) for p in recovery_positions)
            recovery_margin = sum(p.get('estimated_margin', 0) for p in recovery_positions)
            
            target_volume = target_pos.get('volume', 0)
            target_profit = target_pos.get('total_pnl', 0)
            target_margin = target_pos.get('estimated_margin', 0)
            
            # คำนวณผลลัพธ์
            net_profit = recovery_profit + target_profit
            total_margin_freed = recovery_margin + target_margin
            volume_match_ratio = min(recovery_volume, target_volume) / max(recovery_volume, target_volume) if max(recovery_volume, target_volume) > 0 else 0
            
            # คำนวณคะแนนรวม
            profit_score = max(0, (net_profit + 20) / 40)  # normalize -20 to +20 → 0 to 1
            volume_score = volume_match_ratio
            margin_score = min(1, total_margin_freed / 100)  # margin ที่ freed
            
            total_score = (profit_score * 0.5) + (volume_score * 0.3) + (margin_score * 0.2)
            
            return {
                'position_ids': [p['id'] for p in recovery_positions],
                'total_volume': recovery_volume,
                'net_profit': net_profit,
                'margin_freed': total_margin_freed,
                'volume_match_ratio': volume_match_ratio,
                'score': total_score
            }
            
        except Exception as e:
            print(f"❌ Evaluate recovery combination error: {e}")
            return {'score': 0}
    
    def _find_optimal_volume_close_set(self, positions: List[Dict], target_volume: float, direction: str) -> List[Dict]:
        """📊 หาชุด Positions ที่เหมาะสมสำหรับปิดเพื่อ Volume Balance"""
        try:
            # เรียง positions ตาม close priority
            sorted_positions = sorted(positions, key=lambda x: x.get('close_priority', 0), reverse=True)
            
            selected_positions = []
            accumulated_volume = 0.0
            accumulated_profit = 0.0
            
            for pos in sorted_positions:
                pos_volume = pos.get('volume', 0)
                pos_profit = pos.get('total_pnl', 0)
                
                # เช็คว่าการเพิ่ม position นี้คุ้มค่าหรือไม่
                if accumulated_volume + pos_volume <= target_volume * 1.2:  # ไม่เกิน 120% ของเป้าหมาย
                    
                    projected_profit = accumulated_profit + pos_profit
                    
                    # เพิ่มเข้าไปถ้าไม่ทำให้ขาดทุนมากเกินไป
                    if projected_profit >= accumulated_profit - 10.0:  # ไม่ให้แย่ลงเกิน $10
                        selected_positions.append(pos)
                        accumulated_volume += pos_volume
                        accumulated_profit += pos_profit
                        
                        # ถ้าถึงเป้าหมายแล้ว หยุด
                        if accumulated_volume >= target_volume * 0.8:  # 80% ของเป้าหมาย
                            break
            
            print(f"📊 Volume close set: {len(selected_positions)} positions, {accumulated_volume:.2f} lots, ${accumulated_profit:.2f} profit")
            return selected_positions
            
        except Exception as e:
            print(f"❌ Volume close set error: {e}")
            return []
    
    def _find_hedge_partners_for_position(self, target_pos: Dict, all_positions: List[Dict]) -> List[Dict]:
        """🔍 หา Hedge Partners สำหรับ Position หนึ่ง"""
        try:
            target_type = target_pos.get('type')
            target_volume = target_pos.get('volume', 0)
            target_pnl = target_pos.get('total_pnl', 0)
            
            # หา positions ประเภทตรงข้าม
            opposite_type = 'SELL' if target_type == 'BUY' else 'BUY'
            candidates = [p for p in all_positions if p.get('type') == opposite_type]
            
            # เรียงตาม efficiency
            candidates.sort(key=lambda x: x.get('profit_per_lot', 0), reverse=True)
            
            # หาชุดที่เหมาะสมสำหรับ hedge
            hedge_partners = []
            accumulated_volume = 0.0
            accumulated_profit = 0.0
            
            for candidate in candidates:
                cand_volume = candidate.get('volume', 0)
                cand_profit = candidate.get('total_pnl', 0)
                
                # เช็คว่าการรวม candidate นี้คุ้มค่าหรือไม่
                if accumulated_volume + cand_volume <= target_volume * 1.5:  # ไม่เกิน 150% ของ target
                    
                    projected_total = accumulated_profit + cand_profit + target_pnl
                    
                    # เพิ่มเข้าไปถ้ายังเป็นบวกหรือขาดทุนไม่มาก
                    if projected_total >= -5.0:
                        hedge_partners.append(candidate)
                        accumulated_volume += cand_volume
                        accumulated_profit += cand_profit
                        
                        # ถ้า volume match ดีพอแล้ว หยุด
                        volume_match = min(accumulated_volume, target_volume) / max(accumulated_volume, target_volume)
                        if volume_match >= 0.7:  # 70% match
                            break
            
            return hedge_partners
            
        except Exception as e:
            print(f"❌ Hedge partners error: {e}")
            return []
    
    def _find_enhanced_profit_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """💰 หาโอกาสปิดเพื่อกำไร - ENHANCED WITH DYNAMIC LOT EFFICIENCY"""
        try:
            profit_actions = []
            
            # วนตรวจสอบทุก position (ไม่ filter ก่อน)
            for pos in positions:
                volume = pos.get('volume', 0)
                total_profit = pos.get('total_pnl', 0)
                profit_per_lot = pos.get('profit_per_lot', 0)
                age_hours = pos.get('age_hours', 0)
                
                # คำนวณ dynamic threshold สำหรับ position นี้
                volume_threshold = self.calculate_volume_adjusted_threshold(volume)
                
                close_profit = False
                priority = 5
                reason = ""
                
                # เกณฑ์การปิดแบบ volume-adjusted
                if total_profit >= volume_threshold * 2:  # efficiency สูงมาก
                    close_profit = True
                    priority = 1
                    reason = f"Very high efficiency: ${total_profit:.1f} vs ${volume_threshold * 2:.1f} target ({volume:.2f}L)"
                    
                elif total_profit >= volume_threshold:  # efficiency ดี
                    close_profit = True  
                    priority = 2
                    reason = f"Good efficiency: ${total_profit:.1f} vs ${volume_threshold:.1f} target ({volume:.2f}L)"
                    
                elif total_profit >= volume_threshold * 0.8 and age_hours >= 12:  # efficiency พอได้ + เก่า
                    close_profit = True
                    priority = 3
                    reason = f"OK efficiency + old: ${total_profit:.1f} vs ${volume_threshold * 0.8:.1f} target ({age_hours:.1f}h)"
                
                elif total_profit >= volume_threshold * 0.6 and volume >= 0.1:  # volume ใหญ่ + กำไรพอสมควร
                    close_profit = True
                    priority = 4  
                    reason = f"Large volume + decent profit: ${total_profit:.1f} ({volume:.2f}L)"
                
                if close_profit:
                    profit_action = {
                        'action_type': 'enhanced_profit_target',
                        'position_id': pos['id'],
                        'profit_per_lot': profit_per_lot,
                        'total_profit': total_profit,
                        'volume': volume,
                        'volume_threshold': volume_threshold,  # เพิ่มไว้ดู
                        'efficiency_category': pos.get('efficiency_category'),
                        'priority': priority,
                        'reason': reason
                    }
                    profit_actions.append(profit_action)
            
            return profit_actions
            
        except Exception as e:
            print(f"❌ Enhanced profit opportunities error: {e}")
            return []
        
    # เพิ่ม method ใหม่ก่อน
    def calculate_volume_adjusted_threshold(self, volume: float, position_type: str = 'profit') -> float:
        """🧮 คำนวณ threshold แบบ volume-adjusted + real spread"""
        try:
            base_threshold = volume * 100.0
            current_spread = self.mt5_connector.get_current_spread(self.symbol)
            spread_buffer = current_spread * 2.0
            final_threshold = base_threshold + spread_buffer
            return max(final_threshold, 1.0)
        except:
            return volume * 100.0 + 2.0
        
    # ==========================================
    # ⚡ ENHANCED EXECUTION METHODS  
    # ==========================================
    
    def execute_close_action(self, close_action: Dict) -> bool:
        """
        ⚡ ดำเนินการปิดออเดอร์ - ENHANCED VERSION
        
        Args:
            close_action: ข้อมูล close action
            
        Returns:
            bool: สำเร็จหรือไม่
        """
        try:
            action_type = close_action.get('action_type')
            priority = close_action.get('priority', 5)
            reason = close_action.get('reason', '')
            
            print(f"⚡ Executing enhanced close action: {action_type}")
            print(f"   Priority: {priority}")  
            print(f"   Reason: {reason}")
            
            success = False
            
            if action_type == 'margin_optimization':
                success = self._execute_margin_optimization_close(close_action)
                
            elif action_type == 'volume_balance':
                success = self._execute_volume_balance_close(close_action)
                
            elif action_type == 'lot_aware_recovery':
                success = self._execute_lot_aware_recovery_close(close_action)
                
            elif action_type == 'enhanced_profit_target':
                success = self._execute_enhanced_profit_close(close_action)
                
            else:
                print(f"❌ Unknown enhanced action type: {action_type}")
                return False
            
            # บันทึกสถิติ
            if success:
                self._record_enhanced_close_stats(action_type, close_action)
                self.position_cache = {}  # Clear cache
            
            return success
            
        except Exception as e:
            print(f"❌ Enhanced close action execution error: {e}")
            return False
    
    def _execute_margin_optimization_close(self, action: Dict) -> bool:
        """🔧 ดำเนินการ Margin Optimization"""
        try:
            primary_id = action.get('primary_position')
            hedge_ids = action.get('hedge_positions', [])
            margin_freed = action.get('margin_freed', 0)
            net_profit = action.get('net_profit', 0)
            
            all_positions_to_close = [primary_id] + hedge_ids
            
            print(f"🔧 Margin Optimization: Closing {len(all_positions_to_close)} positions")
            print(f"   Margin to free: ${margin_freed:.0f}")
            print(f"   Net result: ${net_profit:.2f}")
            
            return self._close_multiple_positions(all_positions_to_close, "Margin Optimization")
            
        except Exception as e:
            print(f"❌ Margin optimization close error: {e}")
            return False
    
    def _execute_volume_balance_close(self, action: Dict) -> bool:
        """⚖️ ดำเนินการ Volume Balance"""
        try:
            positions_to_close = action.get('positions_to_close', [])
            volume_to_close = action.get('volume_to_close', 0)
            net_profit = action.get('net_profit', 0)
            
            print(f"⚖️ Volume Balance: Closing {len(positions_to_close)} positions")
            print(f"   Volume to close: {volume_to_close:.2f} lots")
            print(f"   Net result: ${net_profit:.2f}")
            
            return self._close_multiple_positions(positions_to_close, "Volume Balance")
            
        except Exception as e:
            print(f"❌ Volume balance close error: {e}")
            return False
    
    def _execute_lot_aware_recovery_close(self, action: Dict) -> bool:
        """🎯 ดำเนินการ Lot-Aware Recovery"""
        try:
            target_id = action.get('target_position')
            recovery_ids = action.get('recovery_positions', [])
            volume_match = action.get('volume_match_ratio', 0)
            net_profit = action.get('net_profit', 0)
            
            all_positions_to_close = [target_id] + recovery_ids
            
            print(f"🎯 Lot-Aware Recovery: Closing {len(all_positions_to_close)} positions")
            print(f"   Volume match: {volume_match:.1%}")
            print(f"   Net result: ${net_profit:.2f}")
            
            return self._close_multiple_positions(all_positions_to_close, "Lot-Aware Recovery")
            
        except Exception as e:
            print(f"❌ Lot-aware recovery close error: {e}")
            return False
    
    def _execute_enhanced_profit_close(self, action: Dict) -> bool:
        """💰 ดำเนินการปิดเพื่อกำไร - Enhanced"""
        try:
            position_id = action.get('position_id')
            profit_per_lot = action.get('profit_per_lot', 0)
            total_profit = action.get('total_profit', 0)
            volume = action.get('volume', 0)
            
            print(f"💰 Enhanced Profit Close: Position {position_id}")
            print(f"   Efficiency: ${profit_per_lot:.0f}/lot")
            print(f"   Total: ${total_profit:.2f} ({volume:.2f} lots)")
            
            return self.close_position_by_id(position_id, "Enhanced Profit Target")
            
        except Exception as e:
            print(f"❌ Enhanced profit close error: {e}")
            return False
    
    def _record_enhanced_close_stats(self, action_type: str, action_data: Dict):
        """📝 บันทึกสถิติการปิดออเดอร์ - Enhanced"""
        try:
            if action_type == 'margin_optimization':
                self.close_stats['margin_optimization_closes'] += 1
                self.close_stats['total_margin_freed'] += action_data.get('margin_freed', 0)
                
            elif action_type == 'volume_balance':
                self.close_stats['volume_balance_closes'] += 1
                
            elif action_type == 'lot_aware_recovery':
                self.close_stats['lot_aware_closes'] += 1
                
            elif action_type == 'enhanced_profit_target':
                efficiency_gain = action_data.get('profit_per_lot', 0) / max(action_data.get('volume', 1), 0.01)
                self.close_stats['total_efficiency_improved'] += efficiency_gain
            
        except Exception as e:
            print(f"❌ Enhanced close stats error: {e}")
    
    # ==========================================
    # 📊 ENHANCED REPORTING & STATISTICS
    # ==========================================
    
    def get_enhanced_portfolio_summary(self) -> Dict:
        """📊 สรุป Portfolio แบบ Lot-Aware"""
        try:
            positions = self.get_all_positions()
            
            if not positions:
                return self._get_empty_portfolio_summary()
            
            # คำนวณ lot statistics
            lot_summary = self.lot_stats.copy()
            
            # เพิ่มข้อมูล efficiency distribution
            efficiency_distribution = {
                'excellent': len([p for p in positions if p.get('efficiency_category') == 'excellent']),
                'good': len([p for p in positions if p.get('efficiency_category') == 'good']),
                'fair': len([p for p in positions if p.get('efficiency_category') == 'fair']),
                'poor': len([p for p in positions if p.get('efficiency_category') == 'poor']),
                'terrible': len([p for p in positions if p.get('efficiency_category') == 'terrible'])
            }
            
            # คำนวณ margin statistics
            total_estimated_margin = sum(p.get('estimated_margin', 0) for p in positions)
            avg_margin_efficiency = sum(p.get('margin_efficiency', 0) for p in positions) / len(positions)
            
            # สถานะ portfolio health
            portfolio_health = self._calculate_portfolio_health_score(positions)
            
            return {
                **lot_summary,
                'efficiency_distribution': efficiency_distribution,
                'total_estimated_margin': round(total_estimated_margin, 2),
                'avg_margin_efficiency': round(avg_margin_efficiency, 4),
                'portfolio_health_score': portfolio_health,
                'close_opportunities_count': len(self.check_smart_close_opportunities()),
                'enhanced_stats': self.close_stats.copy()
            }
            
        except Exception as e:
            print(f"❌ Enhanced portfolio summary error: {e}")
            return {'error': str(e)}
    
    def _calculate_portfolio_health_score(self, positions: List[Dict]) -> float:
        """🏥 คำนวณคะแนนสุขภาพ Portfolio"""
        try:
            if not positions:
                return 1.0
            
            # 1. Volume Balance Score (0-1)
            volume_imbalance = self.lot_stats.get('volume_imbalance_ratio', 0)
            volume_score = max(0, 1 - (volume_imbalance / 0.5))  # imbalance > 50% = score 0
            
            # 2. Efficiency Score (0-1)
            excellent_count = len([p for p in positions if p.get('efficiency_category') == 'excellent'])
            total_count = len(positions)
            efficiency_score = excellent_count / total_count
            
            # 3. Age Score (0-1) 
            old_positions = len([p for p in positions if p.get('age_hours', 0) > self.max_losing_age_hours])
            age_score = max(0, 1 - (old_positions / total_count))
            
            # 4. Margin Score (0-1)
            margin_efficiency = self.lot_stats.get('margin_efficiency_score', 0)
            margin_score = max(0, min(1, (margin_efficiency + 0.1) / 0.2))
            
            # รวมคะแนน
            health_score = (
                volume_score * 0.3 +      # Volume balance สำคัญ
                efficiency_score * 0.3 +  # Efficiency สำคัญ
                age_score * 0.2 +         # Age management
                margin_score * 0.2        # Margin efficiency
            )
            
            return round(health_score, 3)
            
        except Exception as e:
            return 0.5
    
    def get_lot_efficiency_report(self) -> Dict:
        """📊 รายงาน Lot Efficiency Analysis"""
        try:
            positions = self.get_all_positions()
            
            if not positions:
                return {'message': 'No positions to analyze'}
            
            # แยกตาม efficiency category
            by_category = {}
            for category in ['excellent', 'good', 'fair', 'poor', 'terrible']:
                category_positions = [p for p in positions if p.get('efficiency_category') == category]
                
                if category_positions:
                    total_volume = sum(p.get('volume', 0) for p in category_positions)
                    total_profit = sum(p.get('total_pnl', 0) for p in category_positions)
                    avg_efficiency = sum(p.get('profit_per_lot', 0) for p in category_positions) / len(category_positions)
                    
                    by_category[category] = {
                        'count': len(category_positions),
                        'total_volume': round(total_volume, 2),
                        'total_profit': round(total_profit, 2),
                        'avg_efficiency': round(avg_efficiency, 1),
                        'volume_percentage': round((total_volume / self.lot_stats.get('total_volume', 1)) * 100, 1)
                    }
            
            return {
                'efficiency_breakdown': by_category,
                'portfolio_stats': self.lot_stats,
                'recommendations': self._get_efficiency_recommendations(by_category)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_efficiency_recommendations(self, category_breakdown: Dict) -> List[str]:
        """💡 แนะนำการปรับปรุงจาก Efficiency Analysis"""
        recommendations = []
        
        try:
            # เช็ค terrible positions
            terrible = category_breakdown.get('terrible', {})
            if terrible.get('count', 0) > 0:
                recommendations.append(f"🚨 มี {terrible['count']} positions efficiency แย่มาก - หา hedge partners")
            
            # เช็ค poor positions
            poor = category_breakdown.get('poor', {})
            if poor.get('volume_percentage', 0) > 30:
                recommendations.append(f"⚠️ {poor['volume_percentage']:.1f}% volume มี efficiency ต่ำ - ปรับ portfolio")
            
            # เช็ค excellent opportunities
            excellent = category_breakdown.get('excellent', {})
            if excellent.get('count', 0) > 2:
                recommendations.append(f"💰 มี {excellent['count']} high-efficiency positions - พิจารณาปิดเพื่อกำไร")
            
            # เช็ค volume imbalance
            volume_imbalance = self.lot_stats.get('volume_imbalance_ratio', 0)
            if volume_imbalance > 0.4:
                recommendations.append(f"⚖️ Volume imbalance {volume_imbalance:.1%} - ควร rebalance")
            
            return recommendations
            
        except Exception as e:
            return [f"Error generating recommendations: {e}"]
    
    def _get_empty_portfolio_summary(self) -> Dict:
        """📊 Portfolio summary เมื่อไม่มี positions"""
        return {
            'total_positions': 0,
            'total_volume': 0.0,
            'total_pnl': 0.0,
            'total_buy_volume': 0.0,
            'total_sell_volume': 0.0,
            'volume_imbalance_ratio': 0.0,
            'portfolio_health_score': 1.0,
            'efficiency_distribution': {},
            'enhanced_stats': self.close_stats.copy()
        }
    
    # ==========================================
    # 🔧 EXISTING METHODS (เก็บไว้เดิม)
    # ==========================================
    
    def close_position_by_id(self, position_id: int, reason: str = "Manual") -> bool:
        """❌ ปิด Position ตาม ID - เก็บเดิม"""
        try:
            if not self.mt5_connector.is_connected:
                print(f"❌ MT5 not connected - cannot close position")
                return False
            
            position = mt5.positions_get(ticket=position_id)
            
            if not position:
                print(f"❌ Position {position_id} not found")
                return False
            
            pos = position[0]
            
            print(f"❌ Closing position {position_id}...")
            print(f"   Type: {'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'}")
            print(f"   Volume: {pos.volume} lots")
            print(f"   Profit: ${pos.profit:.2f}")
            print(f"   Reason: {reason}")
            
            # เตรียม close request
            if pos.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(pos.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(pos.symbol).ask
            
            close_request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': pos.symbol,
                'volume': pos.volume,
                'type': order_type,
                'position': position_id,
                'price': price,
                'deviation': 10,
                'magic': pos.magic,
                'comment': f"Close_{reason}",
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_FOK
            }
            
            # ส่งคำสั่งปิด
            result = mt5.order_send(close_request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Position {position_id} closed successfully")
                return True
            else:
                error_msg = f"retcode: {result.retcode}, comment: {result.comment}" if result else "No result"
                print(f"❌ Failed to close position {position_id}: {error_msg}")
                return False
            
        except Exception as e:
            print(f"❌ Close position error: {e}")
            return False
    
    def _close_multiple_positions(self, position_ids: List[int], reason: str = "Batch") -> bool:
        """📦 ปิดหลาย Positions - เก็บเดิม"""
        try:
            if not position_ids:
                return True
            
            print(f"📦 Batch closing {len(position_ids)} positions...")
            print(f"   Reason: {reason}")
            
            success_count = 0
            total_count = len(position_ids)
            
            for position_id in position_ids:
                if self.close_position_by_id(position_id, reason):
                    success_count += 1
                    time.sleep(0.1)  # พัก 100ms ระหว่างการปิด
            
            success_rate = success_count / total_count
            print(f"📦 Batch result: {success_count}/{total_count} successful ({success_rate:.1%})")
            
            return success_rate >= 0.8
            
        except Exception as e:
            print(f"❌ Batch close error: {e}")
            return False
    
    def emergency_close_all(self) -> int:
        """🚨 ปิดออเดอร์ทั้งหมดฉุกเฉิน - เก็บเดิม"""
        try:
            print(f"🚨 EMERGENCY CLOSE ALL POSITIONS!")
            
            positions = self.get_all_positions()
            
            if not positions:
                return 0
            
            position_ids = [p['id'] for p in positions]
            closed_count = 0
            
            for position_id in position_ids:
                if self.close_position_by_id(position_id, "EMERGENCY STOP"):
                    closed_count += 1
                time.sleep(0.05)
            
            print(f"🚨 Emergency close completed: {closed_count}/{len(positions)} closed")
            self.close_stats['emergency_closes'] = self.close_stats.get('emergency_closes', 0) + closed_count
            
            return closed_count
            
        except Exception as e:
            print(f"❌ Emergency close all error: {e}")
            return 0
    
    # ==========================================
    # 🔧 UTILITY METHODS
    # ==========================================
    
    def _format_position_age(self, age_timedelta: timedelta) -> str:
        """⏱️ จัดรูปแบบอายุ Position - เก็บเดิม"""
        try:
            total_seconds = int(age_timedelta.total_seconds())
            
            if total_seconds < 60:
                return f"{total_seconds}s"
            elif total_seconds < 3600:
                minutes = total_seconds // 60
                return f"{minutes}m"
            elif total_seconds < 86400:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours}h{minutes}m"
            else:
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                return f"{days}d{hours}h"
                
        except Exception as e:
            print(f"❌ Age formatting error: {e}")
            return "unknown"
    
    def _is_cache_valid(self) -> bool:
        """🔧 ตรวจสอบ Cache - เก็บเดิม"""
        time_diff = (datetime.now() - self.last_update_time).total_seconds()
        return time_diff < self.cache_duration_seconds and bool(self.position_cache)
    
    # ==========================================
    # 🆕 NEW UTILITY METHODS - LOT ANALYSIS
    # ==========================================
    
    def get_lot_distribution_analysis(self) -> Dict:
        """📊 วิเคราะห์การกระจายตัวของ Lot Size"""
        try:
            positions = self.get_all_positions()
            
            if not positions:
                return {'message': 'No positions to analyze'}
            
            # จัดกลุ่มตาม lot size ranges
            lot_ranges = {
                'micro': [],    # 0.01-0.03
                'small': [],    # 0.04-0.10  
                'medium': [],   # 0.11-0.50
                'large': [],    # 0.51-1.00
                'huge': []      # > 1.00
            }
            
            for pos in positions:
                volume = pos.get('volume', 0)
                
                if volume <= 0.03:
                    lot_ranges['micro'].append(pos)
                elif volume <= 0.10:
                    lot_ranges['small'].append(pos)
                elif volume <= 0.50:
                    lot_ranges['medium'].append(pos)
                elif volume <= 1.00:
                    lot_ranges['large'].append(pos)
                else:
                    lot_ranges['huge'].append(pos)
            
            # สรุปแต่ละ range
            analysis = {}
            for range_name, range_positions in lot_ranges.items():
                if range_positions:
                    total_volume = sum(p.get('volume', 0) for p in range_positions)
                    total_profit = sum(p.get('total_pnl', 0) for p in range_positions)
                    avg_efficiency = sum(p.get('profit_per_lot', 0) for p in range_positions) / len(range_positions)
                    
                    analysis[range_name] = {
                        'count': len(range_positions),
                        'total_volume': round(total_volume, 2),
                        'total_profit': round(total_profit, 2),
                        'avg_profit_per_lot': round(avg_efficiency, 1),
                        'percentage_of_portfolio': round((len(range_positions) / len(positions)) * 100, 1)
                    }
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_margin_optimization_suggestions(self) -> List[Dict]:
        """🔧 ข้อเสนอแนะการปรับปรุง Margin Usage"""
        try:
            positions = self.get_all_positions()
            account_info = self.mt5_connector.get_account_info()
            
            suggestions = []
            
            if not positions or not account_info:
                return suggestions
            
            current_margin_level = account_info.get('margin_level', 1000)
            
            # ถ้า margin level ต่ำ
            if current_margin_level < 300:
                # หา positions ที่ใช้ margin มากแต่ไม่คุ้มค่า
                high_margin_positions = [
                    p for p in positions 
                    if p.get('estimated_margin', 0) > 100 
                    and p.get('margin_efficiency', 0) < 0.005
                ]
                
                if high_margin_positions:
                    suggestions.append({
                        'type': 'margin_reduction',
                        'urgency': 'high',
                        'message': f'ปิด {len(high_margin_positions)} positions ที่ใช้ margin มากแต่ไม่คุ้ม',
                        'affected_positions': len(high_margin_positions),
                        'estimated_margin_freed': sum(p.get('estimated_margin', 0) for p in high_margin_positions)
                    })
            
            # ถ้ามี volume imbalance มาก
            volume_imbalance = self.lot_stats.get('volume_imbalance_ratio', 0)
            if volume_imbalance > 0.5:
                suggestions.append({
                    'type': 'volume_rebalance',
                    'urgency': 'medium', 
                    'message': f'Volume imbalance {volume_imbalance:.1%} - ควร rebalance portfolio',
                    'current_imbalance': volume_imbalance
                })
            
            # ถ้ามี positions efficiency ต่ำเยอะ
            poor_efficiency_count = len([p for p in positions if p.get('efficiency_category') in ['poor', 'terrible']])
            if poor_efficiency_count > len(positions) * 0.3:  # มากกว่า 30%
                suggestions.append({
                    'type': 'efficiency_improvement',
                    'urgency': 'medium',
                    'message': f'{poor_efficiency_count} positions มี efficiency ต่ำ - หา recovery opportunities',
                    'affected_count': poor_efficiency_count
                })
            
            return suggestions
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def force_lot_aware_analysis(self) -> Dict:
        """🔧 บังคับทำ Lot-Aware Analysis ทันที (สำหรับ debug)"""
        try:
            print(f"🔧 FORCE LOT-AWARE ANALYSIS...")
            
            # Clear cache ก่อน
            self.position_cache = {}
            self.last_update_time = datetime.min
            
            # ดึงข้อมูลใหม่
            positions = self.get_all_positions()
            
            # วิเคราะห์ close opportunities
            opportunities = self.check_smart_close_opportunities()
            
            # สรุปผล
            analysis_result = {
                'total_positions': len(positions),
                'lot_stats': self.lot_stats.copy(),
                'close_opportunities': len(opportunities),
                'top_opportunities': [
                    {
                        'type': opp.get('action_type'),
                        'priority': opp.get('priority'),
                        'reason': opp.get('reason', '')[:50]  # แสดงแค่ 50 ตัวอักษรแรก
                    }
                    for opp in opportunities[:3]
                ],
                'portfolio_health': self._calculate_portfolio_health_score(positions),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Force analysis completed")
            print(f"   Portfolio health: {analysis_result['portfolio_health']:.2f}")
            print(f"   Close opportunities: {len(opportunities)}")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Force lot-aware analysis error: {e}")
            return {'error': str(e)}
    
    def is_ready(self) -> bool:
        """✅ ตรวจสอบความพร้อม - เก็บเดิม"""
        return (
            self.mt5_connector is not None and
            self.mt5_connector.is_connected
        )
    
    def get_monitor_info(self) -> Dict:
        """ℹ️ ข้อมูล Enhanced Position Monitor"""
        return {
            'name': 'Enhanced Lot-Aware Position Monitor',
            'version': '2.0.0',
            'symbol': self.symbol,
            'features': [
                'Lot-Aware Analysis',
                'Margin Optimization', 
                'Volume Balance',
                'Efficiency Tracking',
                'Smart Recovery'
            ],
            'settings': {
                'min_efficiency_threshold': self.min_efficiency_threshold,
                'volume_balance_tolerance': self.volume_balance_tolerance,
                'partial_close_enabled': self.partial_close_enabled,
                'margin_efficiency_weight': self.margin_efficiency_weight
            },
            'stats': self.close_stats.copy()
        }
    
    def calculate_volume_adjusted_threshold(self, volume: float, position_type: str = 'profit') -> float:
        """
        🧮 คำนวณ threshold แบบ volume-adjusted + real spread
        Formula: (volume * 100) + (current_spread * buffer_multiplier)
        """
        try:
            # Base: 0.01 lot ต่อ $1 → 1.0 lot ต่อ $100
            base_threshold = volume * 100.0
            
            # ดึง spread จริงจาก MT5
            current_spread = self.mt5_connector.get_current_spread(self.symbol)
            
            # Spread buffer = 2x current spread (เผื่อ spread เปลี่ยน)
            spread_buffer = current_spread * 2.0
            
            # รวมกัน
            final_threshold = base_threshold + spread_buffer
            
            # print(f"💰 Volume-adjusted: {volume:.2f}L → ${base_threshold:.1f} + ${spread_buffer:.1f}sp = ${final_threshold:.1f}")
            
            return max(final_threshold, 1.0)  # อย่างต่ำ $1
            
        except Exception as e:
            print(f"❌ Volume threshold calculation error: {e}")
            return volume * 100.0 + 2.0  # fallback