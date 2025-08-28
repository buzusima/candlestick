"""
🧠 Smart Order Role Manager - ระบบจัดการหน้าที่ออเดอร์อัจฉริยะ
order_role_manager.py

🎯 CORE CONCEPT:
✅ จำแนกหน้าที่ออเดอร์อัตโนมัติ (MAIN/HG/SUPPORT/SACRIFICE)
✅ ปรับหน้าที่ตาม market condition แบบ dynamic
✅ ปิดออเดอร์แบบ intelligent pairing (กำไร + ขาดทุน = net positive)
✅ ระบบ sacrifice ออเดอร์เสียเพื่อช่วยพอร์ต (เมื่อจำเป็น)
✅ Flexible decision making - ไม่ติดกฎตายตัว

🚀 KEY FEATURES:
- Dynamic Role Assignment
- Smart Profit/Loss Pairing  
- Market Context Awareness
- Emergency Portfolio Protection
- Flexible Close Timing
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import statistics
import time

class SmartOrderRoleManager:
    """
    🧠 Smart Order Role Manager
    
    จัดการหน้าที่ของออเดอร์และตัดสินใจปิดออเดอร์อย่างฉลาด
    """
    
    def __init__(self, mt5_connector, config: Dict):
        """
        🔧 เริ่มต้น Smart Order Role Manager
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # การตั้งค่า role management
        self.role_config = config.get("role_management", {})
        self.symbol = config.get("trading", {}).get("symbol", "XAUUSD.v")
        
        # 🎯 ROLE DEFINITIONS
        self.roles = {
            'MAIN': 'ออเดอร์หลักที่ follow trend',
            'HG': 'ออเดอร์ป้องกัน (Hedge Guard)',
            'SUPPORT': 'ออเดอร์สำรองรอโอกาส',
            'SACRIFICE': 'ออเดอร์ที่พร้อมสละเพื่อพอร์ต'
        }
        
        # 🧠 SMART SETTINGS
        self.min_net_profit_to_close = self.role_config.get("min_net_profit_to_close", 5.0)  # $5 net กำไรขั้นต่ำ
        self.max_sacrifice_loss = self.role_config.get("max_sacrifice_loss", 30.0)  # ยอมเสีย $30 เพื่อช่วยพอร์ต
        self.hedge_distance_threshold = self.role_config.get("hedge_distance_threshold", 3.0)  # 3$ distance สำหรับ hedge
        self.emergency_portfolio_loss = self.role_config.get("emergency_portfolio_loss", 200.0)  # ขาดทุนรวม $200 = emergency
        
        # 📊 DYNAMIC THRESHOLDS
        self.profit_target_base = 100.0  # กำไรเป้าหมายพื้นฐาน $100/lot
        self.loss_tolerance_base = 50.0  # ขาดทุนที่ยอมรับได้ $50/lot
        
        # 🔄 ROLE TRACKING
        self.order_roles = {}  # {order_id: role}
        self.role_history = []  # บันทึกการเปลี่ยนหน้าที่
        self.last_role_assignment_time = datetime.now()
        
        # 📈 PERFORMANCE TRACKING
        self.role_performance = {
            'MAIN': {'closed_count': 0, 'total_profit': 0.0},
            'HG': {'closed_count': 0, 'total_profit': 0.0},
            'SUPPORT': {'closed_count': 0, 'total_profit': 0.0},
            'SACRIFICE': {'closed_count': 0, 'total_profit': 0.0}
        }
        
    # ==========================================
    # 🎯 CORE ROLE MANAGEMENT
    # ==========================================
    
    def _get_position_profit(self, pos) -> float:
        """
        💰 ดึง profit จาก position ไม่ว่าจะเป็น dict หรือ object
        
        Args:
            pos: Position data (Dict หรือ MT5 object)
            
        Returns:
            float: Total P&L ของ position
        """
        try:
            if isinstance(pos, dict):
                return pos.get('total_pnl', 0)
            else:
                return getattr(pos, 'profit', 0)
        except Exception as e:
            return 0.0

    def _get_position_attribute(self, pos, attr_name: str, default=None):
        """
        🔧 ดึง attribute จาก position ไม่ว่าจะเป็น dict หรือ object
        
        Args:
            pos: Position data
            attr_name: ชื่อ attribute 
            default: ค่า default
            
        Returns:
            attribute value หรือ default
        """
        try:
            if isinstance(pos, dict):
                return pos.get(attr_name, default)
            else:
                return getattr(pos, attr_name, default)
        except Exception as e:
            return default

    def analyze_and_assign_roles(self, positions: List[Dict]) -> Dict:
        """
        🧠 วิเคราะห์และจัดหน้าที่ออเดอร์อัจฉริยะ
        
        Returns:
            Dict: ผลการจัดหน้าที่ + คำแนะนำ
        """
        try:
            if not positions:
                return {'assignments': {}, 'recommendations': []}
            
            current_price = self._get_current_price()
            if not current_price:
                return {'assignments': {}, 'recommendations': [], 'error': 'Cannot get current price'}
            
            print(f"🧠 Smart Role Analysis - Current Price: ${current_price:.2f}")
            print(f"📊 Analyzing {len(positions)} positions...")
            
            # แยก BUY/SELL positions
            buy_positions = [p for p in positions if p.get('type') == 'buy']
            sell_positions = [p for p in positions if p.get('type') == 'sell']
            
            # จัดเรียงตามระยะห่างจากราคาปัจจุบัน
            buy_positions.sort(key=lambda x: abs(current_price - x.get('price_open', 0)))
            sell_positions.sort(key=lambda x: abs(current_price - x.get('price_open', 0)))
            
            # 🎯 ASSIGN ROLES
            role_assignments = {}
            
            # 1. MAIN ROLES - ออเดอร์ที่ใกล้กำไรที่สุด
            if buy_positions:
                closest_profitable_buy = self._find_closest_profitable_position(buy_positions, current_price, 'buy')
                if closest_profitable_buy:
                    role_assignments[closest_profitable_buy['id']] = 'MAIN'
            
            if sell_positions:
                closest_profitable_sell = self._find_closest_profitable_position(sell_positions, current_price, 'sell')
                if closest_profitable_sell:
                    role_assignments[closest_profitable_sell['id']] = 'MAIN'
            
            # 2. HEDGE GUARD ROLES - ออเดอร์ป้องกัน
            self._assign_hedge_roles(buy_positions, sell_positions, current_price, role_assignments)
            
            # 3. SACRIFICE ROLES - ออเดอร์ที่แย่ที่สุด
            self._assign_sacrifice_roles(positions, current_price, role_assignments)
            
            # 4. SUPPORT ROLES - ออเดอร์ที่เหลือ
            for pos in positions:
                if pos['id'] not in role_assignments:
                    role_assignments[pos['id']] = 'SUPPORT'
            
            # อัพเดท internal tracking
            self.order_roles = role_assignments.copy()
            self.last_role_assignment_time = datetime.now()
            
            # 🎯 GENERATE SMART RECOMMENDATIONS
            recommendations = self._generate_smart_recommendations(positions, role_assignments, current_price)
            
            print(f"✅ Role Assignment Complete:")
            for role in ['MAIN', 'HG', 'SUPPORT', 'SACRIFICE']:
                count = sum(1 for r in role_assignments.values() if r == role)
                if count > 0:
                    print(f"   {role}: {count} positions")
            
            return {
                'assignments': role_assignments,
                'recommendations': recommendations,
                'analysis_time': datetime.now(),
                'market_context': self._get_market_context(current_price, positions)
            }
            
        except Exception as e:
            print(f"❌ Role analysis error: {e}")
            return {'assignments': {}, 'recommendations': [], 'error': str(e)}
    
    def _find_closest_profitable_position(self, positions: List[Dict], current_price: float, position_type: str) -> Optional[Dict]:
        """หา position ที่ใกล้กำไรที่สุด"""
        try:
            profitable_positions = []
            
            for pos in positions:
                entry_price = pos.get('price_open', 0)
                current_pnl = pos.get('total_pnl', 0)
                
                # คำนวณระยะห่างจากกำไร
                if position_type == 'buy':
                    distance_to_profit = max(0, entry_price - current_price)  # ต้องการราคาขึ้น
                else:  # sell
                    distance_to_profit = max(0, current_price - entry_price)  # ต้องการราคาลง
                
                # ให้คะแนนตามโอกาสกำไร
                profit_score = current_pnl + (distance_to_profit * -10)  # ยิ่งไกลกำไร คะแนนยิ่งต่ำ
                
                profitable_positions.append({
                    'position': pos,
                    'profit_score': profit_score,
                    'distance_to_profit': distance_to_profit
                })
            
            if not profitable_positions:
                return None
            
            # เรียงตาม profit score (สูงสุดก่อน)
            profitable_positions.sort(key=lambda x: x['profit_score'], reverse=True)
            return profitable_positions[0]['position']
            
        except Exception as e:
            print(f"❌ Find closest profitable error: {e}")
            return None
    
    def _assign_hedge_roles(self, buy_positions: List[Dict], sell_positions: List[Dict], 
                           current_price: float, role_assignments: Dict):
        """จัดหน้าที่ HEDGE GUARD"""
        try:
            # หา BUY positions ที่ขาดทุนหนัก
            losing_buys = [p for p in buy_positions if p.get('total_pnl', 0) < -self.hedge_distance_threshold]
            
            # หา SELL positions ที่สามารถ hedge ได้
            for losing_buy in losing_buys:
                if losing_buy['id'] in role_assignments:
                    continue  # ถูก assign แล้ว
                
                # หา SELL ที่อยู่ใกล้ๆ เพื่อ hedge
                suitable_hedges = [
                    s for s in sell_positions 
                    if s['id'] not in role_assignments 
                    and abs(s.get('price_open', 0) - losing_buy.get('price_open', 0)) <= 10.0
                    and s.get('total_pnl', 0) > -self.hedge_distance_threshold
                ]
                
                if suitable_hedges:
                    # เลือก SELL ที่เหมาะสมที่สุด
                    best_hedge = min(suitable_hedges, key=lambda x: abs(x.get('total_pnl', 0)))
                    role_assignments[best_hedge['id']] = 'HG'
            
            # ทำเช่นเดียวกันสำหรับ SELL positions ที่ขาดทุน
            losing_sells = [p for p in sell_positions if p.get('total_pnl', 0) < -self.hedge_distance_threshold]
            
            for losing_sell in losing_sells:
                if losing_sell['id'] in role_assignments:
                    continue
                
                suitable_hedges = [
                    b for b in buy_positions 
                    if b['id'] not in role_assignments
                    and abs(b.get('price_open', 0) - losing_sell.get('price_open', 0)) <= 10.0
                    and b.get('total_pnl', 0) > -self.hedge_distance_threshold
                ]
                
                if suitable_hedges:
                    best_hedge = min(suitable_hedges, key=lambda x: abs(x.get('total_pnl', 0)))
                    role_assignments[best_hedge['id']] = 'HG'
                    
        except Exception as e:
            print(f"❌ Hedge role assignment error: {e}")
    
    def _assign_sacrifice_roles(self, positions: List[Dict], current_price: float, role_assignments: Dict):
        """🎭 มอบหมาย SACRIFICE roles - FIXED"""
        try:
            sacrifice_candidates = []
            
            for pos in positions:
                if pos['id'] in role_assignments:
                    continue  # ถูก assign แล้ว
                
                # ✅ ใช้ helper function
                pnl = self._get_position_profit(pos)
                entry_price = self._get_position_attribute(pos, 'price_open', 0)
                pos_type = self._get_position_attribute(pos, 'type', 'unknown')
                open_time = self._get_position_attribute(pos, 'time_open', datetime.now())
                
                if isinstance(open_time, str):
                    continue  # ข้ามถ้าไม่ใช่ datetime
                
                age_hours = (datetime.now() - open_time).total_seconds() / 3600
                
                # คำนวณ "hopeless score"
                if pos_type == 'BUY':
                    price_distance = max(0, entry_price - current_price)
                else:
                    price_distance = max(0, current_price - entry_price)
                
                hopeless_score = (abs(pnl) * 2) + (age_hours * 0.5) + (price_distance * 5)
                
                # เฉพาะ positions ที่ขาดทุนมาก + เก่า + ไกลจากกำไร
                if pnl < -self.max_sacrifice_loss * 0.6 and (age_hours > 12 or price_distance > 5):
                    sacrifice_candidates.append({
                        'position': pos,
                        'hopeless_score': hopeless_score,
                        'loss': pnl
                    })
            
            if sacrifice_candidates:
                # เรียงตาม hopeless score (แย่ที่สุดก่อน)
                sacrifice_candidates.sort(key=lambda x: x['hopeless_score'], reverse=True)
                
                # มอบหมาย SACRIFICE role แค่ 1-2 positions ที่แย่ที่สุด
                max_sacrifice = min(2, len(sacrifice_candidates))
                for i in range(max_sacrifice):
                    pos = sacrifice_candidates[i]['position']
                    pos_id = self._get_position_attribute(pos, 'id', 'unknown')
                    role_assignments[pos_id] = 'SACRIFICE'
                    print(f"🎭 Assigned SACRIFICE role to position {pos_id} (Loss: ${sacrifice_candidates[i]['loss']:.2f})")
                    
        except Exception as e:
            print(f"❌ Sacrifice role assignment error: {e}")
    
    # ==========================================
    # 🎯 SMART RECOMMENDATIONS ENGINE
    # ==========================================
    
    def _generate_smart_recommendations(self, positions: List[Dict], role_assignments: Dict, 
                                      current_price: float) -> List[Dict]:
        """🧠 สร้างคำแนะนำการปิดออเดอร์อัจฉริยะ"""
        try:
            recommendations = []
            
            # 1. 💰 PROFIT HARVESTING - เก็บกำไร MAIN positions
            main_profit_actions = self._find_main_profit_opportunities(positions, role_assignments, current_price)
            recommendations.extend(main_profit_actions)
            
            # 2. ⚖️ HEDGE PAIR CLOSING - ปิดคู่ hedge ที่ net positive
            hedge_pair_actions = self._find_hedge_pair_opportunities(positions, role_assignments, current_price)
            recommendations.extend(hedge_pair_actions)
            
            # 3. 🎭 STRATEGIC SACRIFICE - เสีย SACRIFICE เพื่อช่วย portfolio
            sacrifice_actions = self._find_sacrifice_opportunities(positions, role_assignments, current_price)
            recommendations.extend(sacrifice_actions)
            
            # 4. 🚨 EMERGENCY PORTFOLIO PROTECTION
            emergency_actions = self._find_emergency_opportunities(positions, role_assignments, current_price)
            recommendations.extend(emergency_actions)
            
            # 5. 🔄 ROLE REBALANCING - เปลี่ยนหน้าที่ตาม market
            rebalancing_actions = self._find_rebalancing_opportunities(positions, role_assignments, current_price)
            recommendations.extend(rebalancing_actions)
            
            # เรียงตาม priority (ต่ำ = สำคัญกว่า)
            recommendations.sort(key=lambda x: x.get('priority', 10))
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Smart recommendations error: {e}")
            return []
    def _find_hedge_pair_opportunities(self, positions: List[Dict], role_assignments: Dict, 
                                 current_price: float) -> List[Dict]:
        """⚖️ หาโอกาสปิดคู่ hedge - RESTORED"""
        try:
            pair_actions = []
            
            # หา HG positions
            hg_positions = [p for p in positions if role_assignments.get(p['id']) == 'HG']
            other_positions = [p for p in positions if role_assignments.get(p['id']) != 'HG']
            
            for hg_pos in hg_positions:
                hg_pnl = self._get_position_profit(hg_pos)
                hg_id = self._get_position_attribute(hg_pos, 'id', 'unknown')
                
                # หา partner ที่เมื่อปิดคู่แล้ว net positive
                for partner in other_positions:
                    partner_pnl = self._get_position_profit(partner)
                    partner_id = self._get_position_attribute(partner, 'id', 'unknown')
                    net_result = hg_pnl + partner_pnl
                    
                    # ปิดคู่ได้ถ้า net positive หรือขาดทุนน้อยมาก
                    if net_result >= self.min_net_profit_to_close:
                        pair_actions.append({
                            'action_type': 'hedge_pair_close',
                            'hg_position_id': hg_id,
                            'partner_position_id': partner_id,
                            'net_result': net_result,
                            'hg_profit': hg_pnl,
                            'partner_profit': partner_pnl,
                            'priority': 2 if net_result > 20 else 3,
                            'reason': f"Hedge pair net positive: ${net_result:.2f} (${hg_pnl:.2f} + ${partner_pnl:.2f})"
                        })
                        break  # หา partner ได้แล้ว
            
            return pair_actions
            
        except Exception as e:
            print(f"❌ Hedge pair opportunities error: {e}")
            return []

    def _find_main_profit_opportunities(self, positions: List[Dict], role_assignments: Dict, 
                                    current_price: float) -> List[Dict]:
        """💰 หาโอกาสเก็บกำไร MAIN positions - FIXED"""
        try:
            profit_actions = []
            
            main_positions = [p for p in positions if role_assignments.get(p['id']) == 'MAIN']
            
            for pos in main_positions:
                # ✅ ใช้ helper function แทน
                pnl = self._get_position_profit(pos)
                volume = self._get_position_attribute(pos, 'volume', 0)
                pos_id = self._get_position_attribute(pos, 'id', 'unknown')
                
                profit_per_lot = pnl / max(volume, 0.01)
                
                # เกณฑ์ dynamic ตาม market condition
                profit_threshold = self._calculate_dynamic_profit_threshold(pos, current_price)
                
                if pnl >= profit_threshold and pnl > self.min_net_profit_to_close:
                    priority = 1 if profit_per_lot > 150 else 2
                    
                    profit_actions.append({
                        'action_type': 'main_profit_harvest',
                        'position_id': pos_id,
                        'role': 'MAIN',
                        'profit': pnl,
                        'profit_per_lot': profit_per_lot,
                        'priority': priority,
                        'reason': f"MAIN position profit target reached: ${pnl:.2f} (${profit_per_lot:.0f}/lot)"
                    })
            
            return profit_actions
            
        except Exception as e:
            print(f"❌ Main profit opportunities error: {e}")
            return []
    
    def _find_main_profit_opportunities(self, positions: List[Dict], role_assignments: Dict, 
                                    current_price: float) -> List[Dict]:
        """💰 หาโอกาสเก็บกำไร MAIN positions - FIXED"""
        try:
            profit_actions = []
            
            main_positions = [p for p in positions if role_assignments.get(p['id']) == 'MAIN']
            
            for pos in main_positions:
                # ✅ ใช้ helper function แทน
                pnl = self._get_position_profit(pos)
                volume = self._get_position_attribute(pos, 'volume', 0)
                pos_id = self._get_position_attribute(pos, 'id', 'unknown')
                
                profit_per_lot = pnl / max(volume, 0.01)
                
                # เกณฑ์ dynamic ตาม market condition
                profit_threshold = self._calculate_dynamic_profit_threshold(pos, current_price)
                
                if pnl >= profit_threshold and pnl > self.min_net_profit_to_close:
                    priority = 1 if profit_per_lot > 150 else 2
                    
                    profit_actions.append({
                        'action_type': 'main_profit_harvest',
                        'position_id': pos_id,
                        'role': 'MAIN',
                        'profit': pnl,
                        'profit_per_lot': profit_per_lot,
                        'priority': priority,
                        'reason': f"MAIN position profit target reached: ${pnl:.2f} (${profit_per_lot:.0f}/lot)"
                    })
            
            return profit_actions
            
        except Exception as e:
            print(f"❌ Main profit opportunities error: {e}")
            return []
    
    def _find_sacrifice_opportunities(self, positions: List[Dict], role_assignments: Dict, 
                                    current_price: float) -> List[Dict]:
        """🎭 หาโอกาสเสีย sacrifice เชิงกลยุทธ์ - FIXED"""
        try:
            sacrifice_actions = []
            
            # หา SACRIFICE positions
            sacrifice_positions = [p for p in positions if role_assignments.get(p['id']) == 'SACRIFICE']
            
            # หา profitable positions ที่ดี
            profitable_positions = []
            for p in positions:
                pnl = self._get_position_profit(p)
                if pnl > 30:  # กำไรดี
                    profitable_positions.append(p)
            
            # จับคู่ SACRIFICE + Profitable
            for sacrifice_pos in sacrifice_positions:
                sacrifice_pnl = self._get_position_profit(sacrifice_pos)
                sacrifice_id = self._get_position_attribute(sacrifice_pos, 'id', 'unknown')
                
                # หาคู่ profitable ที่ดีที่สุด
                for profit_pos in profitable_positions:
                    profit_pnl = self._get_position_profit(profit_pos)
                    profit_id = self._get_position_attribute(profit_pos, 'id', 'unknown')
                    
                    net_result = sacrifice_pnl + profit_pnl
                    sacrifice_loss = abs(sacrifice_pnl) if sacrifice_pnl < 0 else 0
                    
                    # ถ้า net positive และ sacrifice loss ไม่เกินที่ยอมรับได้
                    if (net_result > self.min_net_profit_to_close and 
                        sacrifice_loss <= self.max_sacrifice_loss):
                        
                        priority = 2 if net_result > 15 else 3
                        
                        sacrifice_actions.append({
                            'action_type': 'strategic_sacrifice',
                            'sacrifice_position_id': sacrifice_id,
                            'profitable_position_id': profit_id,
                            'sacrifice_loss': sacrifice_loss,
                            'profit_gain': profit_pnl,
                            'net_result': net_result,
                            'priority': priority,
                            'reason': f"Strategic sacrifice: ${sacrifice_loss:.2f} loss + ${profit_pnl:.2f} profit = ${net_result:.2f} net"
                        })
            
            return sacrifice_actions
            
        except Exception as e:
            print(f"❌ Sacrifice opportunities error: {e}")
            return []
    
    def _find_emergency_opportunities(self, positions: List[Dict], role_assignments: Dict, 
                                    current_price: float) -> List[Dict]:
        """🚨 หาโอกาส emergency protection"""
        try:
            emergency_actions = []
            
            # คำนวณสถานการณ์ emergency
            total_pnl = sum(p.get('total_pnl', 0) for p in positions)
            losing_positions_count = len([p for p in positions if p.get('total_pnl', 0) < -20])
            
            # ถ้าพอร์ตขาดทุนหนัก + มีออเดอร์ขาดทุนเยอะ
            if total_pnl < -self.emergency_portfolio_loss * 1.5 and losing_positions_count > 5:
                
                # หาวิธีปิดที่ minimize damage
                profitable_positions = [p for p in positions if p.get('total_pnl', 0) > 30]
                
                if len(profitable_positions) >= 2:
                    # เลือก 2 positions ที่กำไรสูงสุด
                    top_profitable = sorted(profitable_positions, key=lambda x: x.get('total_pnl', 0), reverse=True)[:2]
                    total_profit = sum(p.get('total_pnl', 0) for p in top_profitable)
                    
                    emergency_actions.append({
                        'action_type': 'emergency_portfolio_protection',
                        'positions_to_close': [p['id'] for p in top_profitable],
                        'emergency_profit': total_profit,
                        'portfolio_loss': total_pnl,
                        'priority': 1,  # สำคัญสุด
                        'reason': f"Emergency: Portfolio at ${total_pnl:.2f}, harvest ${total_profit:.2f} profit"
                    })
            
            return emergency_actions
            
        except Exception as e:
            print(f"❌ Emergency opportunities error: {e}")
            return []
    
    def _find_rebalancing_opportunities(self, positions: List[Dict], role_assignments: Dict, 
                                      current_price: float) -> List[Dict]:
        """🔄 หาโอกาส rebalance roles"""
        try:
            rebalancing_actions = []
            
            # วิเคราะห์ความสมดุลของ roles
            role_counts = {}
            for role in ['MAIN', 'HG', 'SUPPORT', 'SACRIFICE']:
                role_counts[role] = sum(1 for r in role_assignments.values() if r == role)
            
            # ถ้ามี MAIN น้อยเกินไป (ควรมี 2-4 positions)
            if role_counts['MAIN'] < 2:
                # หา SUPPORT positions ที่สามารถเป็น MAIN ได้
                support_positions = [p for p in positions if role_assignments.get(p['id']) == 'SUPPORT']
                suitable_mains = [
                    p for p in support_positions 
                    if p.get('total_pnl', 0) > -30  # ไม่ขาดทุนหนักมาก
                ]
                
                if suitable_mains:
                    best_candidate = min(suitable_mains, key=lambda x: abs(x.get('total_pnl', 0)))
                    
                    rebalancing_actions.append({
                        'action_type': 'role_rebalance',
                        'position_id': best_candidate['id'],
                        'old_role': 'SUPPORT',
                        'new_role': 'MAIN',
                        'priority': 8,
                        'reason': f"Promote SUPPORT to MAIN for better balance"
                    })
            
            return rebalancing_actions
            
        except Exception as e:
            print(f"❌ Rebalancing opportunities error: {e}")
            return []
    
    # ==========================================
    # 🎯 EXECUTION ENGINE
    # ==========================================
    
    def execute_smart_recommendation(self, recommendation: Dict) -> Dict:
        """
        ⚡ ดำเนินการตามคำแนะนำอัจฉริยะ
        
        Args:
            recommendation: คำแนะนำจาก smart analysis
            
        Returns:
            Dict: ผลการดำเนินการ
        """
        try:
            action_type = recommendation.get('action_type')
            priority = recommendation.get('priority', 10)
            
            print(f"⚡ Executing smart recommendation: {action_type} (Priority: {priority})")
            
            success = False
            execution_details = {}
            
            if action_type == 'main_profit_harvest':
                success, execution_details = self._execute_main_profit_harvest(recommendation)
                
            elif action_type == 'hedge_pair_close':
                success, execution_details = self._execute_hedge_pair_close(recommendation)
                
            elif action_type == 'strategic_sacrifice':
                success, execution_details = self._execute_strategic_sacrifice(recommendation)
                
            elif action_type == 'emergency_portfolio_protection':
                success, execution_details = self._execute_emergency_protection(recommendation)
                
            elif action_type == 'role_rebalance':
                success, execution_details = self._execute_role_rebalance(recommendation)
                
            else:
                return {
                    'success': False,
                    'reason': f'Unknown action type: {action_type}',
                    'recommendation': recommendation
                }
            
            # บันทึกผลลัพธ์
            if success:
                self._record_execution_success(action_type, recommendation, execution_details)
            
            return {
                'success': success,
                'action_type': action_type,
                'execution_details': execution_details,
                'recommendation': recommendation,
                'execution_time': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Smart recommendation execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendation': recommendation
            }
    
    def _execute_main_profit_harvest(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """💰 ดำเนินการเก็บกำไร MAIN position"""
        try:
            position_id = recommendation.get('position_id')
            expected_profit = recommendation.get('profit', 0)
            
            print(f"💰 Harvesting MAIN position {position_id} profit: ${expected_profit:.2f}")
            
            # ส่งคำสั่งปิดผ่าน MT5
            success = self._close_position_by_id(position_id, "MAIN Profit Harvest")
            
            execution_details = {
                'position_id': position_id,
                'expected_profit': expected_profit,
                'close_reason': 'MAIN Profit Harvest'
            }
            
            if success:
                # อัพเดท role performance
                self.role_performance['MAIN']['closed_count'] += 1
                self.role_performance['MAIN']['total_profit'] += expected_profit
                
                # ลบจาก role tracking
                if position_id in self.order_roles:
                    del self.order_roles[position_id]
            
            return success, execution_details
            
        except Exception as e:
            print(f"❌ Main profit harvest error: {e}")
            return False, {'error': str(e)}
    
    def _execute_hedge_pair_close(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """⚖️ ดำเนินการปิดคู่ hedge"""
        try:
            hg_id = recommendation.get('hg_position_id')
            partner_id = recommendation.get('partner_position_id')
            expected_net = recommendation.get('net_result', 0)
            
            print(f"⚖️ Closing hedge pair: HG {hg_id} + Partner {partner_id} = ${expected_net:.2f}")
            
            # ปิดทั้งคู่
            success1 = self._close_position_by_id(hg_id, "Hedge Pair Close")
            success2 = self._close_position_by_id(partner_id, "Hedge Pair Close")
            
            overall_success = success1 and success2
            
            execution_details = {
                'hg_position_id': hg_id,
                'partner_position_id': partner_id,
                'expected_net_result': expected_net,
                'hg_close_success': success1,
                'partner_close_success': success2
            }
            
            if overall_success:
                # อัพเดท performance
                self.role_performance['HG']['closed_count'] += 1
                self.role_performance['HG']['total_profit'] += expected_net
                
                # ลบจาก role tracking
                for pid in [hg_id, partner_id]:
                    if pid in self.order_roles:
                        del self.order_roles[pid]
            
            return overall_success, execution_details
            
        except Exception as e:
            print(f"❌ Hedge pair close error: {e}")
            return False, {'error': str(e)}
    
    def _execute_strategic_sacrifice(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """🎭 ดำเนินการเสีย sacrifice เชิงกลยุทธ์"""
        try:
            sacrifice_id = recommendation.get('sacrifice_position_id')
            profitable_id = recommendation.get('profitable_position_id')
            expected_net = recommendation.get('net_result', 0)
            sacrifice_loss = recommendation.get('sacrifice_loss', 0)
            
            print(f"🎭 Strategic sacrifice: Position {sacrifice_id} (${sacrifice_loss:.2f}) + Profitable {profitable_id} = ${expected_net:.2f}")
            
            # ปิดทั้งคู่
            success1 = self._close_position_by_id(sacrifice_id, "Strategic Sacrifice")
            success2 = self._close_position_by_id(profitable_id, "Strategic Sacrifice")
            
            overall_success = success1 and success2
            
            execution_details = {
                'sacrifice_position_id': sacrifice_id,
                'profitable_position_id': profitable_id,
                'expected_net_result': expected_net,
                'sacrifice_loss': sacrifice_loss,
                'sacrifice_success': success1,
                'profitable_success': success2
            }
            
            if overall_success:
                # อัพเดท performance
                self.role_performance['SACRIFICE']['closed_count'] += 1
                self.role_performance['SACRIFICE']['total_profit'] += expected_net
                
                # ลบจาก role tracking
                for pid in [sacrifice_id, profitable_id]:
                    if pid in self.order_roles:
                        del self.order_roles[pid]
            
            return overall_success, execution_details
            
        except Exception as e:
            print(f"❌ Strategic sacrifice error: {e}")
            return False, {'error': str(e)}
    
    def _execute_emergency_protection(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """🚨 ดำเนินการป้องกัน emergency"""
        try:
            positions_to_close = recommendation.get('positions_to_close', [])
            expected_profit = recommendation.get('emergency_profit', 0)
            
            print(f"🚨 Emergency protection: Closing {len(positions_to_close)} positions for ${expected_profit:.2f}")
            
            close_results = []
            overall_success = True
            
            for position_id in positions_to_close:
                success = self._close_position_by_id(position_id, "Emergency Protection")
                close_results.append({'position_id': position_id, 'success': success})
                if not success:
                    overall_success = False
            
            execution_details = {
                'positions_closed': positions_to_close,
                'close_results': close_results,
                'expected_profit': expected_profit,
                'overall_success': overall_success
            }
            
            if overall_success:
                # ลบจาก role tracking
                for pid in positions_to_close:
                    if pid in self.order_roles:
                        del self.order_roles[pid]
            
            return overall_success, execution_details
            
        except Exception as e:
            print(f"❌ Emergency protection error: {e}")
            return False, {'error': str(e)}
    
    def _execute_role_rebalance(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """🔄 ดำเนินการ rebalance role"""
        try:
            position_id = recommendation.get('position_id')
            old_role = recommendation.get('old_role')
            new_role = recommendation.get('new_role')
            
            print(f"🔄 Role rebalance: Position {position_id} from {old_role} to {new_role}")
            
            # อัพเดท role assignment
            if position_id in self.order_roles:
                self.order_roles[position_id] = new_role
            
            # บันทึกประวัติ
            self.role_history.append({
                'timestamp': datetime.now(),
                'position_id': position_id,
                'old_role': old_role,
                'new_role': new_role,
                'reason': recommendation.get('reason', '')
            })
            
            execution_details = {
                'position_id': position_id,
                'old_role': old_role,
                'new_role': new_role,
                'rebalance_time': datetime.now()
            }
            
            return True, execution_details
            
        except Exception as e:
            print(f"❌ Role rebalance error: {e}")
            return False, {'error': str(e)}
    
    # ==========================================
    # 🔧 HELPER METHODS
    # ==========================================
    
    def _get_current_price(self) -> Optional[float]:
        """ดึงราคาปัจจุบัน"""
        try:
            if not self.mt5_connector.is_connected:
                return None
                
            tick = mt5.symbol_info_tick(self.symbol)
            if tick:
                return (tick.bid + tick.ask) / 2
            return None
            
        except Exception as e:
            print(f"❌ Get current price error: {e}")
            return None
    
    def _close_position_by_id(self, position_id: int, reason: str = "") -> bool:
        """ปิด position ตาม ID"""
        try:
            # ดึงข้อมูล position
            position = mt5.positions_get(ticket=position_id)
            if not position:
                print(f"❌ Position {position_id} not found")
                return False
            
            pos = position[0]
            
            # สร้างคำสั่งปิด
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
                'deviation': 20,
                'magic': pos.magic,
                'comment': f"Smart Close: {reason}",
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_FOK
            }
            
            # ส่งคำสั่งปิด
            result = mt5.order_send(close_request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Smart close successful: Position {position_id} - {reason}")
                return True
            else:
                error_msg = f"retcode: {result.retcode}, comment: {result.comment}" if result else "No result"
                print(f"❌ Smart close failed: Position {position_id} - {error_msg}")
                return False
                
        except Exception as e:
            print(f"❌ Close position error: {e}")
            return False
    

    def _calculate_dynamic_profit_threshold(self, position: Dict, current_price: float) -> float:
        """🎯 คำนวณ profit threshold แบบ dynamic - FIXED"""
        try:
            # ✅ ใช้ helper function
            volume = self._get_position_attribute(position, 'volume', 0.01)
            age_hours = self._get_position_attribute(position, 'age_hours', 0)
            
            # Base threshold
            base_threshold = self.profit_target_base * volume
            
            # Age factor - ยิ่งเก่า ยิ่งลด threshold
            age_factor = max(0.5, 1 - (age_hours / 24))
            
            # Market volatility factor (ถ้ามี)
            volatility_factor = 1.0  # คงที่ไว้ก่อน
            
            dynamic_threshold = base_threshold * age_factor * volatility_factor
            
            return max(dynamic_threshold, self.min_net_profit_to_close)
            
        except Exception as e:
            return self.min_net_profit_to_close
    
    def _get_market_context(self, current_price: float, positions: List[Dict]) -> Dict:
        """วิเคราะห์ context ของ market"""
        try:
            return {
                'current_price': current_price,
                'total_positions': len(positions),
                'total_pnl': sum(p.get('total_pnl', 0) for p in positions),
                'buy_positions': len([p for p in positions if p.get('type') == 'buy']),
                'sell_positions': len([p for p in positions if p.get('type') == 'sell']),
                'analysis_time': datetime.now()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _record_execution_success(self, action_type: str, recommendation: Dict, execution_details: Dict):
        """บันทึกความสำเร็จของการ execute"""
        try:
            record = {
                'timestamp': datetime.now(),
                'action_type': action_type,
                'priority': recommendation.get('priority'),
                'success': True,
                'execution_details': execution_details
            }
            
            # TODO: Save to persistent storage
            print(f"✅ Recorded successful execution: {action_type}")
            
        except Exception as e:
            print(f"❌ Record execution error: {e}")
    
    # ==========================================
    # 📊 REPORTING & STATUS
    # ==========================================
    
    def get_role_summary(self) -> Dict:
        """📊 สรุปสถานะ roles ทั้งหมด"""
        try:
            role_counts = {}
            for role in ['MAIN', 'HG', 'SUPPORT', 'SACRIFICE']:
                role_counts[role] = sum(1 for r in self.order_roles.values() if r == role)
            
            return {
                'role_counts': role_counts,
                'total_assigned': len(self.order_roles),
                'role_performance': self.role_performance.copy(),
                'last_assignment_time': self.last_role_assignment_time,
                'role_history_count': len(self.role_history)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_smart_portfolio_health(self, positions: List[Dict]) -> Dict:
        """🏥 วิเคราะห์สุขภาพ portfolio แบบ smart + margin analysis"""
        try:
            if not positions:
                return {'health_score': 1.0, 'status': 'healthy', 'recommendations': []}
            
            # ดึงข้อมูล account
            account_info = self.mt5_connector.get_account_info()
            
            # ✅ แก้ใช้ helper function
            total_pnl = sum(self._get_position_profit(p) for p in positions)
            losing_positions = [p for p in positions if self._get_position_profit(p) < -20]
            profitable_positions = [p for p in positions if self._get_position_profit(p) > 20]
            
            # 🆕 MARGIN ANALYSIS
            margin_health = self._analyze_margin_health(account_info, positions)
            
            # 🆕 CORRELATION ANALYSIS  
            correlation_risk = self._analyze_position_correlation(positions)
            
            # คำนวณ comprehensive health score (0-1)
            health_score = 1.0
            
            # 1. P&L Impact (40% weight)
            if total_pnl < -100:
                pnl_penalty = min(0.4, abs(total_pnl) / 1000)
                health_score -= pnl_penalty
            
            # 2. Position Distribution (20% weight)
            losing_ratio = len(losing_positions) / len(positions)
            health_score -= losing_ratio * 0.2
            
            # 3. Margin Health (30% weight) 🆕
            margin_penalty = (1.0 - margin_health.get('health_ratio', 0.5)) * 0.3
            health_score -= margin_penalty
            
            # 4. Correlation Risk (10% weight) 🆕
            correlation_penalty = correlation_risk.get('risk_score', 0) * 0.1
            health_score -= correlation_penalty
            
            # Bonus for profitable positions
            profitable_ratio = len(profitable_positions) / len(positions)
            health_score += profitable_ratio * 0.05
            
            health_score = max(0.0, min(1.0, health_score))
            
            # กำหนดสถานะรวม
            if health_score >= 0.8:
                status = 'excellent'
            elif health_score >= 0.6:
                status = 'good' 
            elif health_score >= 0.4:
                status = 'warning'
            else:
                status = 'critical'
            
            return {
                'health_score': round(health_score, 3),
                'status': status,
                'total_pnl': total_pnl,
                'losing_positions': len(losing_positions),
                'profitable_positions': len(profitable_positions),
                'losing_ratio': round(losing_ratio, 2),
                'profitable_ratio': round(profitable_ratio, 2),
                
                # 🆕 Enhanced Metrics
                'margin_health': margin_health,
                'correlation_risk': correlation_risk,
                'portfolio_risk_factors': self._identify_risk_factors(positions, account_info),
                'optimization_opportunities': self._find_optimization_opportunities(positions, account_info)
            }
            
        except Exception as e:
            return {'error': str(e), 'health_score': 0.5, 'status': 'unknown'}
                   
    def simulate_close_impact(self, positions_to_close: List[int], all_positions: List[Dict]) -> Dict:
        """
        🎮 จำลองผลกระทบของการปิดออเดอร์
        
        Args:
            positions_to_close: รายการ position IDs ที่จะปิด
            all_positions: positions ทั้งหมดปัจจุบัน
            
        Returns:
            Dict: การจำลองผลกระทบต่อ portfolio
        """
        try:
            # แยก positions ที่จะปิด vs ที่เหลือ
            closing_positions = [p for p in all_positions if p['id'] in positions_to_close]
            remaining_positions = [p for p in all_positions if p['id'] not in positions_to_close]
            
            # คำนวณสถิติปัจจุบัน
            current_stats = self._calculate_portfolio_stats(all_positions)
            
            # จำลองสถิติหลังปิด
            after_close_stats = self._calculate_portfolio_stats(remaining_positions)
            
            # คำนวณ impact
            impact_analysis = {
                'positions_to_close': len(closing_positions),
                'positions_remaining': len(remaining_positions),
                
                # P&L Impact
                'profit_from_closing': sum(p.get('total_pnl', 0) for p in closing_positions),
                'remaining_portfolio_pnl': after_close_stats['total_pnl'],
                'pnl_improvement': after_close_stats['total_pnl'] - (current_stats['total_pnl'] - sum(p.get('total_pnl', 0) for p in closing_positions)),
                
                # Volume Impact
                'volume_reduction': sum(p.get('volume', 0) for p in closing_positions),
                'remaining_volume': after_close_stats['total_volume'],
                'volume_balance_improvement': self._calculate_balance_improvement(current_stats, after_close_stats),
                
                # Margin Impact
                'estimated_margin_freed': sum(p.get('estimated_margin', 0) for p in closing_positions),
                'margin_efficiency_change': after_close_stats.get('margin_efficiency', 0) - current_stats.get('margin_efficiency', 0),
                
                # Risk Impact
                'risk_reduction': self._calculate_risk_reduction(closing_positions, remaining_positions),
                
                # Health Score Impact
                'current_health_score': self.get_smart_portfolio_health(all_positions)['health_score'],
                'projected_health_score': self.get_smart_portfolio_health(remaining_positions)['health_score'],
            }
            
            # คำนวณ overall recommendation
            impact_analysis['overall_impact'] = self._assess_overall_impact(impact_analysis)
            
            return impact_analysis
            
        except Exception as e:
            return {'error': str(e), 'simulation_failed': True}
    
    def _calculate_portfolio_stats(self, positions: List[Dict]) -> Dict:
        """คำนวณสถิติ portfolio"""
        try:
            if not positions:
                return {
                    'total_positions': 0,
                    'total_pnl': 0.0,
                    'total_volume': 0.0,
                    'buy_volume': 0.0,
                    'sell_volume': 0.0,
                    'margin_efficiency': 0.0
                }
            
            buy_positions = [p for p in positions if p.get('type') == 'buy']
            sell_positions = [p for p in positions if p.get('type') == 'sell']
            
            total_pnl = sum(p.get('total_pnl', 0) for p in positions)
            total_volume = sum(p.get('volume', 0) for p in positions)
            buy_volume = sum(p.get('volume', 0) for p in buy_positions)
            sell_volume = sum(p.get('volume', 0) for p in sell_positions)
            
            # Margin efficiency
            total_margin = sum(p.get('estimated_margin', 0) for p in positions)
            margin_efficiency = total_pnl / total_margin if total_margin > 0 else 0
            
            return {
                'total_positions': len(positions),
                'total_pnl': total_pnl,
                'total_volume': total_volume,
                'buy_volume': buy_volume,
                'sell_volume': sell_volume,
                'margin_efficiency': margin_efficiency,
                'losing_positions': len([p for p in positions if p.get('total_pnl', 0) < 0]),
                'profitable_positions': len([p for p in positions if p.get('total_pnl', 0) > 0])
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_balance_improvement(self, current_stats: Dict, after_stats: Dict) -> float:
        """คำนวณการปรับปรุง balance"""
        try:
            # Current imbalance
            current_total = current_stats.get('total_volume', 0)
            if current_total > 0:
                current_buy_ratio = current_stats.get('buy_volume', 0) / current_total
                current_imbalance = abs(current_buy_ratio - 0.5)  # เป้าหมาย 50:50
            else:
                current_imbalance = 0
            
            # After imbalance
            after_total = after_stats.get('total_volume', 0)
            if after_total > 0:
                after_buy_ratio = after_stats.get('buy_volume', 0) / after_total
                after_imbalance = abs(after_buy_ratio - 0.5)
            else:
                after_imbalance = 0
            
            # Improvement = ลดลงของ imbalance
            improvement = current_imbalance - after_imbalance
            return round(improvement, 4)
            
        except Exception as e:
            return 0.0
    
    def _calculate_risk_reduction(self, closing_positions: List[Dict], remaining_positions: List[Dict]) -> Dict:
        """คำนวณการลด risk"""
        try:
            # Risk factors ที่จะลดลง
            risk_reduction = {
                'losing_positions_removed': len([p for p in closing_positions if p.get('total_pnl', 0) < -20]),
                'old_positions_removed': len([p for p in closing_positions if p.get('age_hours', 0) > 24]),
                'high_volume_positions_removed': len([p for p in closing_positions if p.get('volume', 0) > 0.1]),
                'total_loss_eliminated': abs(sum(min(0, p.get('total_pnl', 0)) for p in closing_positions))
            }
            
            # Risk score improvement
            current_correlation_risk = self._analyze_position_correlation(closing_positions + remaining_positions)
            after_correlation_risk = self._analyze_position_correlation(remaining_positions)
            
            risk_reduction['correlation_risk_improvement'] = current_correlation_risk.get('risk_score', 0) - after_correlation_risk.get('risk_score', 0)
            
            return risk_reduction
            
        except Exception as e:
            return {'error': str(e)}
    
    def _assess_overall_impact(self, impact_analysis: Dict) -> Dict:
        """ประเมิน overall impact"""
        try:
            scores = []
            reasons = []
            
            # 1. P&L Impact Score
            profit_from_closing = impact_analysis.get('profit_from_closing', 0)
            if profit_from_closing > 50:
                scores.append(0.8)
                reasons.append(f"Good profit harvest: ${profit_from_closing:.0f}")
            elif profit_from_closing > 0:
                scores.append(0.6)
                reasons.append(f"Positive closing: ${profit_from_closing:.0f}")
            elif profit_from_closing > -30:
                scores.append(0.4)
                reasons.append(f"Minor loss: ${profit_from_closing:.0f}")
            else:
                scores.append(0.2)
                reasons.append(f"Significant loss: ${profit_from_closing:.0f}")
            
            # 2. Health Score Impact
            health_improvement = impact_analysis.get('projected_health_score', 0) - impact_analysis.get('current_health_score', 0)
            if health_improvement > 0.1:
                scores.append(0.9)
                reasons.append(f"Significant health improvement: +{health_improvement:.2f}")
            elif health_improvement > 0:
                scores.append(0.7)
                reasons.append(f"Health improvement: +{health_improvement:.2f}")
            elif health_improvement > -0.05:
                scores.append(0.5)
                reasons.append("Neutral health impact")
            else:
                scores.append(0.3)
                reasons.append(f"Health decline: {health_improvement:.2f}")
            
            # 3. Risk Reduction Score
            risk_reduction = impact_analysis.get('risk_reduction', {})
            losing_removed = risk_reduction.get('losing_positions_removed', 0)
            total_loss_eliminated = risk_reduction.get('total_loss_eliminated', 0)
            
            if losing_removed > 2 and total_loss_eliminated > 50:
                scores.append(0.8)
                reasons.append(f"Major risk reduction: {losing_removed} losing positions, ${total_loss_eliminated:.0f} loss eliminated")
            elif losing_removed > 0:
                scores.append(0.6)
                reasons.append(f"Risk reduction: {losing_removed} losing positions removed")
            else:
                scores.append(0.5)
                reasons.append("No significant risk reduction")
            
            # 4. Margin Impact Score  
            margin_freed = impact_analysis.get('estimated_margin_freed', 0)
            if margin_freed > 100:
                scores.append(0.7)
                reasons.append(f"Significant margin freed: ${margin_freed:.0f}")
            elif margin_freed > 0:
                scores.append(0.6)
                reasons.append(f"Margin freed: ${margin_freed:.0f}")
            else:
                scores.append(0.5)
                reasons.append("No margin impact")
            
            # Overall Assessment
            overall_score = sum(scores) / len(scores) if scores else 0.5
            
            if overall_score >= 0.7:
                recommendation = "HIGHLY_RECOMMENDED"
                summary = "Strong positive impact on portfolio"
            elif overall_score >= 0.6:
                recommendation = "RECOMMENDED"
                summary = "Overall positive impact"
            elif overall_score >= 0.5:
                recommendation = "NEUTRAL"
                summary = "Balanced impact - proceed with caution"
            elif overall_score >= 0.4:
                recommendation = "NOT_RECOMMENDED"
                summary = "Likely negative impact"
            else:
                recommendation = "STRONGLY_NOT_RECOMMENDED"
                summary = "High risk of negative impact"
            
            return {
                'overall_score': round(overall_score, 3),
                'recommendation': recommendation,
                'summary': summary,
                'detailed_reasons': reasons,
                'component_scores': {
                    'pnl_impact': scores[0] if len(scores) > 0 else 0,
                    'health_impact': scores[1] if len(scores) > 1 else 0,
                    'risk_impact': scores[2] if len(scores) > 2 else 0,
                    'margin_impact': scores[3] if len(scores) > 3 else 0
                }
            }
            
        except Exception as e:
            return {
                'overall_score': 0.5,
                'recommendation': 'ERROR',
                'summary': f'Assessment error: {str(e)}',
                'error': str(e)
            }
    
    def _analyze_margin_health(self, account_info: Dict, positions: List[Dict]) -> Dict:
        """🔍 วิเคราะห์สุขภาพ margin แบบละเอียด"""
        try:
            if not account_info:
                return {'health_ratio': 0.5, 'status': 'unknown', 'warnings': ['Cannot get account info']}
            
            margin = account_info.get('margin', 0)
            equity = account_info.get('equity', 0)
            free_margin = account_info.get('free_margin', 0)
            balance = account_info.get('balance', 0)
            
            warnings = []
            recommendations = []
            
            # คำนวณ margin level
            if margin > 0 and equity > 0:
                margin_level = (equity / margin) * 100
                
                # Health ratio based on margin level
                if margin_level >= 500:
                    health_ratio = 1.0
                    status = 'excellent'
                elif margin_level >= 300:
                    health_ratio = 0.8
                    status = 'good'
                elif margin_level >= 200:
                    health_ratio = 0.6
                    status = 'warning'
                    warnings.append(f"Margin level at {margin_level:.1f}%")
                elif margin_level >= 150:
                    health_ratio = 0.3
                    status = 'critical'
                    warnings.append(f"LOW margin level: {margin_level:.1f}%")
                    recommendations.append("Close losing positions to free margin")
                else:
                    health_ratio = 0.1
                    status = 'emergency'
                    warnings.append(f"EMERGENCY margin level: {margin_level:.1f}%")
                    recommendations.append("IMMEDIATE action required")
                    
            else:
                # ไม่มี margin = ไม่มี positions เปิด
                margin_level = float('inf')
                health_ratio = 1.0
                status = 'no_positions'
            
            # คำนวณ margin utilization efficiency
            total_volume = sum(p.get('volume', 0) for p in positions)
            total_pnl = sum(p.get('total_pnl', 0) for p in positions)
            
            if margin > 0:
                margin_efficiency = total_pnl / margin  # กำไรต่อ margin ที่ใช้
                
                if margin_efficiency < -0.5:
                    warnings.append("Poor margin efficiency - losing money per margin used")
                elif margin_efficiency > 0.2:
                    recommendations.append("Good margin efficiency - consider scaling up")
            else:
                margin_efficiency = 0.0
            
            return {
                'health_ratio': health_ratio,
                'status': status,
                'margin_level': margin_level,
                'margin_used': margin,
                'free_margin': free_margin,
                'margin_efficiency': round(margin_efficiency, 4),
                'total_volume': total_volume,
                'warnings': warnings,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {'health_ratio': 0.5, 'status': 'error', 'error': str(e)}
    
    def _analyze_position_correlation(self, positions: List[Dict]) -> Dict:
        """🔗 วิเคราะห์ความสัมพันธ์ของ positions"""
        try:
            if len(positions) < 2:
                return {'risk_score': 0.0, 'correlation_groups': [], 'warnings': []}
            
            buy_positions = [p for p in positions if p.get('type') == 'buy']
            sell_positions = [p for p in positions if p.get('type') == 'sell']
            
            warnings = []
            correlation_groups = []
            risk_score = 0.0
            
            # 1. Same Direction Risk
            buy_volume = sum(p.get('volume', 0) for p in buy_positions)
            sell_volume = sum(p.get('volume', 0) for p in sell_positions)
            total_volume = buy_volume + sell_volume
            
            if total_volume > 0:
                buy_ratio = buy_volume / total_volume
                sell_ratio = sell_volume / total_volume
                imbalance = abs(buy_ratio - sell_ratio)
                
                if imbalance > 0.7:  # 70%+ imbalance
                    risk_score += 0.4
                    dominant_side = "BUY" if buy_ratio > sell_ratio else "SELL"
                    warnings.append(f"High directional risk: {imbalance:.1%} imbalance toward {dominant_side}")
                    
                    correlation_groups.append({
                        'type': 'directional_bias',
                        'dominant_side': dominant_side,
                        'imbalance_ratio': imbalance,
                        'positions': buy_positions if buy_ratio > sell_ratio else sell_positions
                    })
            
            # 2. Price Cluster Risk
            entry_prices = [p.get('price_open', 0) for p in positions if p.get('price_open', 0) > 0]
            if len(entry_prices) >= 3:
                price_range = max(entry_prices) - min(entry_prices)
                avg_price = sum(entry_prices) / len(entry_prices)
                
                # หา positions ที่ entry ใกล้กัน
                clustered_positions = []
                for pos in positions:
                    entry = pos.get('price_open', 0)
                    if abs(entry - avg_price) <= price_range * 0.2:  # ภายใน 20% ของ range
                        clustered_positions.append(pos)
                
                if len(clustered_positions) >= len(positions) * 0.6:  # 60%+ ใกล้กัน
                    cluster_risk = len(clustered_positions) / len(positions)
                    risk_score += cluster_risk * 0.3
                    warnings.append(f"Price clustering risk: {cluster_risk:.1%} positions near same price level")
                    
                    correlation_groups.append({
                        'type': 'price_cluster',
                        'cluster_center': round(avg_price, 2),
                        'cluster_range': round(price_range * 0.2, 2),
                        'positions': clustered_positions
                    })
            
            # 3. Age Correlation Risk  
            old_positions = [p for p in positions if p.get('age_hours', 0) > 24]
            if len(old_positions) >= len(positions) * 0.5:  # 50%+ positions เก่า
                age_risk = len(old_positions) / len(positions)
                risk_score += age_risk * 0.2
                warnings.append(f"Portfolio aging risk: {age_risk:.1%} positions over 24h old")
                
                correlation_groups.append({
                    'type': 'aging_portfolio',
                    'old_positions_ratio': age_risk,
                    'positions': old_positions
                })
            
            risk_score = min(1.0, risk_score)  # Cap at 1.0
            
            return {
                'risk_score': round(risk_score, 3),
                'correlation_groups': correlation_groups,
                'warnings': warnings,
                'position_distribution': {
                    'buy_volume': buy_volume,
                    'sell_volume': sell_volume,
                    'buy_ratio': round(buy_ratio, 2) if total_volume > 0 else 0,
                    'sell_ratio': round(sell_ratio, 2) if total_volume > 0 else 0
                }
            }
            
        except Exception as e:
            return {'risk_score': 0.5, 'error': str(e)}
    
    def _identify_risk_factors(self, positions: List[Dict], account_info: Dict) -> List[str]:
        """🚨 ระบุ risk factors - FIXED"""
        try:
            risk_factors = []
            
            # ✅ ใช้ helper function อ่าน profit
            total_pnl = sum(self._get_position_profit(p) for p in positions)
            heavy_losers = [p for p in positions if self._get_position_profit(p) < -50]
            
            if len(heavy_losers) >= 3:
                risk_factors.append(f"{len(heavy_losers)} positions with heavy losses (>$50)")
            
            if total_pnl < -200:
                risk_factors.append(f"Large portfolio loss: ${total_pnl:.2f}")
            
            # Position concentration risk
            buy_count = len([p for p in positions if self._get_position_attribute(p, 'type') == 'BUY'])
            sell_count = len(positions) - buy_count
            
            if buy_count > 0 and sell_count > 0:
                ratio = max(buy_count, sell_count) / (buy_count + sell_count)
                if ratio > 0.8:
                    risk_factors.append(f"High directional concentration: {ratio:.1%}")
            
            return risk_factors
            
        except Exception as e:
            return [f"Risk analysis error: {str(e)}"]

    def _find_optimization_opportunities(self, positions: List[Dict], account_info: Dict) -> List[Dict]:
        """🎯 หาโอกาส optimize portfolio - FIXED"""
        try:
            opportunities = []
            
            # 1. Margin Liberation Opportunity
            if account_info:
                margin = account_info.get('margin', 0)
                if margin > 0:
                    # หา positions ที่กิน margin เยอะแต่ไม่ได้กำไรเท่าที่ควร
                    inefficient_positions = []
                    
                    for pos in positions:
                        # ✅ ใช้ helper function
                        volume = self._get_position_attribute(pos, 'volume', 0)
                        pnl = self._get_position_profit(pos)
                        
                        if volume > 0.05:  # Volume สูง
                            estimated_margin = volume * 50  # Rough estimate
                            margin_roi = pnl / estimated_margin if estimated_margin > 0 else 0
                            
                            if margin_roi < -0.2:  # ROI ติดลบหนัก
                                inefficient_positions.append({
                                    'position': pos,
                                    'estimated_margin': estimated_margin,
                                    'margin_roi': margin_roi
                                })
                    
                    if inefficient_positions:
                        total_margin_can_free = sum(p['estimated_margin'] for p in inefficient_positions)
                        
                        opportunities.append({
                            'type': 'margin_liberation',
                            'potential_margin_freed': total_margin_can_free,
                            'positions_involved': len(inefficient_positions),
                            'description': f"Can free ~${total_margin_can_free:.0f} margin",
                            'action': "Close or hedge high-volume losing positions"
                        })
            
            # 2. Portfolio Rebalancing
            buy_positions = [p for p in positions if self._get_position_attribute(p, 'type') == 'BUY']
            sell_positions = [p for p in positions if self._get_position_attribute(p, 'type') == 'SELL']
            
            # ✅ ใช้ helper function
            buy_volume = sum(self._get_position_attribute(p, 'volume', 0) for p in buy_positions)
            sell_volume = sum(self._get_position_attribute(p, 'volume', 0) for p in sell_positions)
            
            if buy_volume > 0 and sell_volume > 0:
                total_volume = buy_volume + sell_volume
                imbalance = abs(buy_volume - sell_volume) / total_volume
                
                if imbalance > 0.6:  # 60%+ imbalance
                    dominant_side = "BUY" if buy_volume > sell_volume else "SELL"
                    excess_volume = abs(buy_volume - sell_volume)
                    
                    opportunities.append({
                        'type': 'portfolio_rebalancing',
                        'imbalance_ratio': imbalance,
                        'dominant_side': dominant_side,
                        'excess_volume': excess_volume,
                        'description': f"{imbalance:.1%} imbalance toward {dominant_side}",
                        'action': f"Reduce {dominant_side} exposure by {excess_volume:.2f} lots"
                    })
            
            # 3. Profit Crystallization
            highly_profitable_positions = [
                p for p in positions 
                if self._get_position_profit(p) > 100 and self._get_position_attribute(p, 'age_hours', 0) > 6
            ]
            
            if highly_profitable_positions:
                total_profit_available = sum(self._get_position_profit(p) for p in highly_profitable_positions)
                
                opportunities.append({
                    'type': 'profit_crystallization',
                    'positions_count': len(highly_profitable_positions),
                    'total_profit_available': total_profit_available,
                    'description': f"${total_profit_available:.0f} profit ready to harvest",
                    'action': "Close profitable positions to secure gains"
                })
            
            return opportunities
            
        except Exception as e:
            return [{'type': 'analysis_error', 'error': str(e)}]