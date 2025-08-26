"""
🛡️ Risk Management System
risk_manager.py

🚀 Features:
✅ Position Limits Monitoring (max 30)
✅ Risk per Trade Control (2%)
✅ Margin Level Monitoring
✅ Daily Trading Limits
✅ Emergency Stop Protocols
✅ Portfolio Risk Assessment

🎯 ป้องกันความเสี่ยงและคุ้มครองบัญชีเทรด
ตรวจสอบและบังคับใช้กฎความเสี่ยงทั้งหมด
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics

class RiskManager:
    """
    🛡️ Risk Management System
    
    จัดการและควบคุมความเสี่ยงทั้งหมดของระบบเทรด
    ป้องกันการสูญเสียที่เกินกำหนด
    """
    
    def __init__(self, mt5_connector, config: Dict):
        """
        🔧 เริ่มต้น Risk Manager
        
        Args:
            mt5_connector: MT5 connection object
            config: การตั้งค่าระบบ
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # Risk configuration
        self.risk_config = config.get("risk_management", {})
        self.trading_config = config.get("trading", {})
        
        # Position limits
        self.max_positions = self.risk_config.get("max_positions", 30)
        self.max_buy_positions = self.risk_config.get("max_buy_positions", 20)
        self.max_sell_positions = self.risk_config.get("max_sell_positions", 20)
        
        # Risk per trade
        self.risk_per_trade_percent = self.risk_config.get("risk_per_trade_percent", 2.0)
        self.max_risk_per_trade = self.risk_config.get("max_risk_per_trade", 100.0)
        
        # Daily limits
        self.max_daily_trades = self.risk_config.get("max_daily_trades", 50)
        self.max_daily_loss = self.risk_config.get("max_daily_loss", -200.0)
        self.max_daily_volume = self.risk_config.get("max_daily_volume", 10.0)
        
        # Margin and equity limits
        self.min_margin_level = self.risk_config.get("min_margin_level", 200.0)
        self.stop_trading_margin_level = self.risk_config.get("stop_trading_margin_level", 150.0)
        self.max_drawdown_percent = self.risk_config.get("max_drawdown_percent", 10.0)
        
        # Emergency settings
        self.emergency_close_loss = self.risk_config.get("emergency_close_loss", -500.0)
        self.max_consecutive_losses = self.risk_config.get("max_consecutive_losses", 5)
        
        # Tracking variables
        self.daily_stats = {}
        self.consecutive_losses = 0
        self.last_reset_date = datetime.now().date()
        self.risk_warnings = []
        self.emergency_triggers = []
        
        print(f"🛡️ Risk Manager initialized")
        print(f"   Max positions: {self.max_positions}")
        print(f"   Risk per trade: {self.risk_per_trade_percent}%")
        print(f"   Max daily trades: {self.max_daily_trades}")
        print(f"   Min margin level: {self.min_margin_level}%")
        print(f"   Max drawdown: {self.max_drawdown_percent}%")
    
    # ==========================================
    # 🛡️ MAIN RISK CHECK METHODS
    # ==========================================
    
    def check_risk_levels(self) -> Dict:
        """
        🛡️ ตรวจสอบระดับความเสี่ยงทั้งหมด
        
        Returns:
            Dict: สถานะความเสี่ยงและคำแนะนำ
        """
        try:
            risk_status = {
                'overall_risk': 'low',
                'can_trade': True,
                'emergency_stop': False,
                'warnings': [],
                'restrictions': [],
                'risk_score': 0.0,  # 0-1 (0=ไม่มีความเสี่ยง, 1=ความเสี่ยงสูงสุด)
                'check_time': datetime.now()
            }
            
            # รีเซ็ตรายวันถ้าจำเป็น
            self._reset_daily_stats_if_needed()
            
            # 1. ตรวจสอบ Position Limits
            position_risk = self._check_position_limits()
            risk_status.update(position_risk)
            
            # 2. ตรวจสอบ Account Health
            account_risk = self._check_account_health()
            risk_status = self._merge_risk_assessments(risk_status, account_risk)
            
            # 3. ตรวจสอบ Daily Limits  
            daily_risk = self._check_daily_limits()
            risk_status = self._merge_risk_assessments(risk_status, daily_risk)
            
            # 4. ตรวจสอบ Margin Levels
            margin_risk = self._check_margin_levels()
            risk_status = self._merge_risk_assessments(risk_status, margin_risk)
            
            # 5. ตรวจสอบ Consecutive Losses
            streak_risk = self._check_loss_streak()
            risk_status = self._merge_risk_assessments(risk_status, streak_risk)
            
            # 6. ตรวจสอบ Emergency Conditions
            emergency_risk = self._check_emergency_conditions()
            risk_status = self._merge_risk_assessments(risk_status, emergency_risk)
            
            # คำนวณ Overall Risk Score
            risk_status['risk_score'] = self._calculate_overall_risk_score(risk_status)
            
            # กำหนด Overall Risk Level
            risk_score = risk_status['risk_score']
            if risk_score >= 0.8:
                risk_status['overall_risk'] = 'critical'
            elif risk_score >= 0.6:
                risk_status['overall_risk'] = 'high'
            elif risk_score >= 0.4:
                risk_status['overall_risk'] = 'medium'
            else:
                risk_status['overall_risk'] = 'low'
            
            # Log สถานะความเสี่ยง
            if risk_status['warnings'] or risk_status['restrictions']:
                print(f"🛡️ Risk Check: {risk_status['overall_risk']} risk (Score: {risk_score:.2f})")
                for warning in risk_status['warnings']:
                    print(f"   ⚠️ {warning}")
                for restriction in risk_status['restrictions']:
                    print(f"   🚫 {restriction}")
            
            return risk_status
            
        except Exception as e:
            print(f"❌ Risk level check error: {e}")
            return {
                'overall_risk': 'unknown',
                'can_trade': False,
                'emergency_stop': False,
                'error': str(e)
            }
    
    def _check_position_limits(self) -> Dict:
        """📊 ตรวจสอบขีดจำกัดจำนวน Positions"""
        try:
            if not self.mt5_connector.is_connected:
                return {'can_trade': False, 'warnings': ['MT5 not connected']}
            
            # ดึงข้อมูล positions ปัจจุบัน
            positions = mt5.positions_get(symbol=self.trading_config.get("symbol", "XAUUSD.v"))
            
            if positions is None:
                positions = []
            
            total_count = len(positions)
            buy_count = len([p for p in positions if p.type == mt5.POSITION_TYPE_BUY])
            sell_count = len([p for p in positions if p.type == mt5.POSITION_TYPE_SELL])
            
            warnings = []
            restrictions = []
            can_trade = True
            
            # ตรวจสอบขีดจำกัดทั้งหมด
            if total_count >= self.max_positions:
                warnings.append(f"Position limit reached: {total_count}/{self.max_positions}")
                restrictions.append("No new positions allowed")
                can_trade = False
                
            elif total_count >= self.max_positions * 0.9:  # ใกล้ถึงขีดจำกัด
                warnings.append(f"Approaching position limit: {total_count}/{self.max_positions}")
            
            # ตรวจสอบขีดจำกัด BUY
            if buy_count >= self.max_buy_positions:
                warnings.append(f"BUY position limit reached: {buy_count}/{self.max_buy_positions}")
                restrictions.append("No new BUY positions allowed")
            
            # ตรวจสอบขีดจำกัด SELL
            if sell_count >= self.max_sell_positions:
                warnings.append(f"SELL position limit reached: {sell_count}/{self.max_sell_positions}")
                restrictions.append("No new SELL positions allowed")
            
            return {
                'position_check': 'completed',
                'total_positions': total_count,
                'buy_positions': buy_count,
                'sell_positions': sell_count,
                'can_trade': can_trade,
                'warnings': warnings,
                'restrictions': restrictions,
                'risk_contribution': min(total_count / self.max_positions, 1.0) * 0.3  # 30% ของ risk score
            }
            
        except Exception as e:
            print(f"❌ Position limits check error: {e}")
            return {
                'can_trade': False,
                'warnings': [f"Position check error: {str(e)}"],
                'risk_contribution': 0.5
            }
    
    def _check_account_health(self) -> Dict:
        """💰 ตรวจสอบสุขภาพบัญชี"""
        try:
            account_info = self.mt5_connector.get_account_info()
            
            if not account_info:
                return {
                    'can_trade': False,
                    'warnings': ['Cannot get account information'],
                    'risk_contribution': 0.5
                }
            
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            free_margin = account_info.get('free_margin', 0)
            
            warnings = []
            restrictions = []
            can_trade = True
            
            # ตรวจสอบ Drawdown
            if balance > 0:
                current_drawdown = ((balance - equity) / balance) * 100
                
                if current_drawdown >= self.max_drawdown_percent:
                    warnings.append(f"Maximum drawdown reached: {current_drawdown:.1f}%")
                    restrictions.append("Emergency stop - Max drawdown exceeded")
                    can_trade = False
                    
                elif current_drawdown >= self.max_drawdown_percent * 0.8:
                    warnings.append(f"Approaching max drawdown: {current_drawdown:.1f}%")
            
            # ตรวจสอบ Free Margin
            if equity > 0:
                margin_usage = ((equity - free_margin) / equity) * 100
                
                if margin_usage >= 90:
                    warnings.append(f"High margin usage: {margin_usage:.1f}%")
                    restrictions.append("Limit new positions - High margin usage")
                    can_trade = False
                    
                elif margin_usage >= 70:
                    warnings.append(f"Elevated margin usage: {margin_usage:.1f}%")
            
            # คำนวณ risk contribution
            drawdown_risk = min(current_drawdown / self.max_drawdown_percent, 1.0) if 'current_drawdown' in locals() else 0
            margin_risk = min(margin_usage / 90, 1.0) if 'margin_usage' in locals() else 0
            account_risk_score = max(drawdown_risk, margin_risk) * 0.4  # 40% ของ risk score
            
            return {
                'account_check': 'completed',
                'balance': balance,
                'equity': equity,
                'free_margin': free_margin,
                'current_drawdown': locals().get('current_drawdown', 0),
                'margin_usage': locals().get('margin_usage', 0),
                'can_trade': can_trade,
                'warnings': warnings,
                'restrictions': restrictions,
                'risk_contribution': account_risk_score
            }
            
        except Exception as e:
            print(f"❌ Account health check error: {e}")
            return {
                'can_trade': False,
                'warnings': [f"Account check error: {str(e)}"],
                'risk_contribution': 0.5
            }
    
    def _check_daily_limits(self) -> Dict:
        """📅 ตรวจสอบขีดจำกัดรายวัน"""
        try:
            today = datetime.now().date().isoformat()
            daily_data = self.daily_stats.get(today, {
                'trades_count': 0,
                'daily_profit': 0.0,
                'daily_volume': 0.0,
                'start_balance': 0.0
            })
            
            warnings = []
            restrictions = []
            can_trade = True
            
            # ตรวจสอบจำนวน trades วันนี้
            if daily_data['trades_count'] >= self.max_daily_trades:
                warnings.append(f"Daily trade limit reached: {daily_data['trades_count']}/{self.max_daily_trades}")
                restrictions.append("No more trades today")
                can_trade = False
                
            elif daily_data['trades_count'] >= self.max_daily_trades * 0.9:
                warnings.append(f"Approaching daily trade limit: {daily_data['trades_count']}/{self.max_daily_trades}")
            
            # ตรวจสอบ daily loss
            if daily_data['daily_profit'] <= self.max_daily_loss:
                warnings.append(f"Daily loss limit exceeded: ${daily_data['daily_profit']:.2f}")
                restrictions.append("Daily loss limit exceeded")
                can_trade = False
                
            elif daily_data['daily_profit'] <= self.max_daily_loss * 0.8:
                warnings.append(f"Approaching daily loss limit: ${daily_data['daily_profit']:.2f}")
            
            # ตรวจสอบ daily volume
            if daily_data['daily_volume'] >= self.max_daily_volume:
                warnings.append(f"Daily volume limit reached: {daily_data['daily_volume']:.2f} lots")
                restrictions.append("Daily volume limit exceeded")
                can_trade = False
            
            # คำนวณ risk contribution
            trades_risk = daily_data['trades_count'] / self.max_daily_trades
            loss_risk = abs(daily_data['daily_profit']) / abs(self.max_daily_loss) if self.max_daily_loss != 0 else 0
            volume_risk = daily_data['daily_volume'] / self.max_daily_volume
            
            daily_risk_score = max(trades_risk, loss_risk, volume_risk) * 0.2  # 20% ของ risk score
            
            return {
                'daily_check': 'completed',
                'daily_trades': daily_data['trades_count'],
                'daily_profit': daily_data['daily_profit'],
                'daily_volume': daily_data['daily_volume'],
                'can_trade': can_trade,
                'warnings': warnings,
                'restrictions': restrictions,
                'risk_contribution': daily_risk_score
            }
            
        except Exception as e:
            print(f"❌ Daily limits check error: {e}")
            return {
                'can_trade': True,
                'warnings': [f"Daily check error: {str(e)}"],
                'risk_contribution': 0.1
            }
    
    def _check_margin_levels(self) -> Dict:
        """📊 ตรวจสอบระดับ Margin"""
        try:
            account_info = self.mt5_connector.get_account_info()
            
            if not account_info:
                return {
                    'can_trade': False,
                    'warnings': ['Cannot check margin levels'],
                    'risk_contribution': 0.3
                }
            
            margin = account_info.get('margin', 0)
            equity = account_info.get('equity', 0)
            
            warnings = []
            restrictions = []
            can_trade = True
            
            if margin > 0 and equity > 0:
                margin_level = (equity / margin) * 100
                
                # ตรวจสอบระดับ margin
                if margin_level <= self.stop_trading_margin_level:
                    warnings.append(f"CRITICAL: Margin level {margin_level:.1f}% <= {self.stop_trading_margin_level}%")
                    restrictions.append("STOP TRADING - Critical margin level")
                    can_trade = False
                    
                elif margin_level <= self.min_margin_level:
                    warnings.append(f"LOW MARGIN: {margin_level:.1f}% <= {self.min_margin_level}%")
                    restrictions.append("Reduce position sizes")
                    
                elif margin_level <= self.min_margin_level * 1.5:
                    warnings.append(f"Margin warning: {margin_level:.1f}%")
                
                # คำนวณ risk contribution
                margin_risk = max(0, (self.min_margin_level * 2 - margin_level) / self.min_margin_level)
                margin_risk = min(margin_risk, 1.0) * 0.3  # 30% ของ risk score
            else:
                margin_level = 0
                margin_risk = 0.5  # ไม่ทราบข้อมูล = ความเสี่ยงปานกลาง
                warnings.append("Cannot calculate margin level")
            
            return {
                'margin_check': 'completed',
                'margin_level': locals().get('margin_level', 0),
                'margin': margin,
                'equity': equity,
                'can_trade': can_trade,
                'warnings': warnings,
                'restrictions': restrictions,
                'risk_contribution': locals().get('margin_risk', 0.3)
            }
            
        except Exception as e:
            print(f"❌ Margin check error: {e}")
            return {
                'can_trade': True,
                'warnings': [f"Margin check error: {str(e)}"],
                'risk_contribution': 0.3
            }
    
    def _check_loss_streak(self) -> Dict:
        """📉 ตรวจสอบการขาดทุนต่อเนื่อง"""
        try:
            warnings = []
            restrictions = []
            can_trade = True
            
            if self.consecutive_losses >= self.max_consecutive_losses:
                warnings.append(f"Max consecutive losses: {self.consecutive_losses}/{self.max_consecutive_losses}")
                restrictions.append("Trading suspended - Too many consecutive losses")
                can_trade = False
                
            elif self.consecutive_losses >= self.max_consecutive_losses * 0.8:
                warnings.append(f"Approaching max consecutive losses: {self.consecutive_losses}/{self.max_consecutive_losses}")
            
            # คำนวณ risk contribution
            streak_risk = (self.consecutive_losses / self.max_consecutive_losses) * 0.2  # 20% ของ risk score
            
            return {
                'streak_check': 'completed',
                'consecutive_losses': self.consecutive_losses,
                'max_consecutive_losses': self.max_consecutive_losses,
                'can_trade': can_trade,
                'warnings': warnings,
                'restrictions': restrictions,
                'risk_contribution': min(streak_risk, 1.0)
            }
            
        except Exception as e:
            print(f"❌ Loss streak check error: {e}")
            return {
                'can_trade': True,
                'warnings': [f"Streak check error: {str(e)}"],
                'risk_contribution': 0.1
            }
    
    def _check_emergency_conditions(self) -> Dict:
        """🚨 ตรวจสอบเงื่อนไขฉุกเฉิน"""
        try:
            # ดึงข้อมูล positions เพื่อคำนวณ total P&L
            if not self.mt5_connector.is_connected:
                return {'emergency_stop': False, 'risk_contribution': 0.0}
            
            positions = mt5.positions_get(symbol=self.trading_config.get("symbol", "XAUUSD.v"))
            
            if positions is None:
                positions = []
            
            total_pnl = sum(float(pos.profit) for pos in positions)
            
            warnings = []
            restrictions = []
            emergency_stop = False
            
            # ตรวจสอบการสูญเสียรวม
            if total_pnl <= self.emergency_close_loss:
                warnings.append(f"EMERGENCY: Total loss ${total_pnl:.2f} >= ${self.emergency_close_loss}")
                restrictions.append("EMERGENCY STOP TRIGGERED")
                emergency_stop = True
                
                # บันทึก emergency trigger
                self.emergency_triggers.append({
                    'timestamp': datetime.now(),
                    'trigger_type': 'total_loss',
                    'total_pnl': total_pnl,
                    'threshold': self.emergency_close_loss
                })
            
            # คำนวณ risk contribution
            if self.emergency_close_loss != 0:
                emergency_risk = min(abs(total_pnl) / abs(self.emergency_close_loss), 1.0) * 0.5  # 50% ของ risk score
            else:
                emergency_risk = 0.0
            
            return {
                'emergency_check': 'completed',
                'total_pnl': total_pnl,
                'emergency_threshold': self.emergency_close_loss,
                'emergency_stop': emergency_stop,
                'warnings': warnings,
                'restrictions': restrictions,
                'risk_contribution': emergency_risk
            }
            
        except Exception as e:
            print(f"❌ Emergency check error: {e}")
            return {
                'emergency_stop': False,
                'warnings': [f"Emergency check error: {str(e)}"],
                'risk_contribution': 0.2
            }
    
    # ==========================================
    # 🔧 UTILITY & CALCULATION METHODS
    # ==========================================
    
    def _merge_risk_assessments(self, base_risk: Dict, new_risk: Dict) -> Dict:
        """🔄 รวม Risk Assessments"""
        try:
            # รวม warnings และ restrictions
            base_warnings = base_risk.get('warnings', [])
            new_warnings = new_risk.get('warnings', [])
            base_risk['warnings'] = base_warnings + new_warnings
            
            base_restrictions = base_risk.get('restrictions', [])
            new_restrictions = new_risk.get('restrictions', [])
            base_risk['restrictions'] = base_restrictions + new_restrictions
            
            # รวม can_trade (AND logic)
            base_risk['can_trade'] = base_risk.get('can_trade', True) and new_risk.get('can_trade', True)
            
            # รวม emergency_stop (OR logic)
            base_risk['emergency_stop'] = base_risk.get('emergency_stop', False) or new_risk.get('emergency_stop', False)
            
            # รวม risk contributions
            base_contribution = base_risk.get('risk_contribution', 0)
            new_contribution = new_risk.get('risk_contribution', 0)
            
            # อัพเดท base_risk ด้วยข้อมูลใหม่ที่ไม่ซ้ำ
            for key, value in new_risk.items():
                if key not in ['warnings', 'restrictions', 'can_trade', 'emergency_stop', 'risk_contribution']:
                    base_risk[key] = value
            
            return base_risk
            
        except Exception as e:
            print(f"❌ Risk assessment merge error: {e}")
            return base_risk
    
    def _calculate_overall_risk_score(self, risk_status: Dict) -> float:
        """📊 คำนวณคะแนนความเสี่ยงรวม"""
        try:
            total_risk = 0.0
            
            # รวม risk contributions จาก components ต่างๆ
            for key, value in risk_status.items():
                if isinstance(value, dict) and 'risk_contribution' in value:
                    contribution = value['risk_contribution']
                    total_risk += contribution
                    print(f"   Risk contribution from {key}: {contribution:.3f}")
            
            # เพิ่ม penalty สำหรับ emergency stop
            if risk_status.get('emergency_stop', False):
                total_risk += 0.5
            
            # เพิ่ม penalty สำหรับจำนวน warnings
            warning_count = len(risk_status.get('warnings', []))
            warning_penalty = min(warning_count * 0.1, 0.3)  # สูงสุด 0.3
            total_risk += warning_penalty
            
            # จำกัดในช่วง 0-1
            total_risk = max(0.0, min(1.0, total_risk))
            
            return round(total_risk, 3)
            
        except Exception as e:
            print(f"❌ Overall risk calculation error: {e}")
            return 0.5
    
    def _reset_daily_stats_if_needed(self):
        """🔄 รีเซ็ตสถิติรายวันถ้าจำเป็น"""
        try:
            today = datetime.now().date()
            
            if today != self.last_reset_date:
                print(f"🔄 Daily stats reset for {today}")
                
                # เก็บข้อมูลเมื่อวาน
                yesterday = self.last_reset_date.isoformat()
                if yesterday not in self.daily_stats:
                    self.daily_stats[yesterday] = {
                        'trades_count': 0,
                        'daily_profit': 0.0,
                        'daily_volume': 0.0
                    }
                
                # รีเซ็ตตัวแปรวันนี้
                today_iso = today.isoformat()
                self.daily_stats[today_iso] = {
                    'trades_count': 0,
                    'daily_profit': 0.0,
                    'daily_volume': 0.0,
                    'start_balance': 0.0
                }
                
                # อัพเดทวันที่
                self.last_reset_date = today
                
                # รีเซ็ต consecutive losses (เริ่มใหม่ทุกวัน)
                self.consecutive_losses = 0
                
        except Exception as e:
            print(f"❌ Daily reset error: {e}")
    
    # ==========================================
    # 📝 EXTERNAL UPDATE METHODS
    # ==========================================
    
    def update_trade_result(self, trade_result: str, profit: float, volume: float):
        """
        📝 อัพเดทผลการเทรด
        
        Args:
            trade_result: 'win', 'loss', หรือ 'break_even'
            profit: กำไรขาดทุน
            volume: ขนาด lot
        """
        try:
            today = datetime.now().date().isoformat()
            
            # ตรวจสอบว่ามีข้อมูลวันนี้หรือไม่
            if today not in self.daily_stats:
                self.daily_stats[today] = {
                    'trades_count': 0,
                    'daily_profit': 0.0,
                    'daily_volume': 0.0
                }
            
            # อัพเดทสถิติ
            self.daily_stats[today]['trades_count'] += 1
            self.daily_stats[today]['daily_profit'] += profit
            self.daily_stats[today]['daily_volume'] += volume
            
            # อัพเดท consecutive losses
            if trade_result == 'loss':
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0  # รีเซ็ตเมื่อไม่ใช่ loss
            
            print(f"📝 Trade result updated: {trade_result} (${profit:.2f})")
            print(f"   Consecutive losses: {self.consecutive_losses}")
            
        except Exception as e:
            print(f"❌ Trade result update error: {e}")
    
    def validate_new_trade(self, signal_data: Dict) -> Dict:
        """
        ✅ ตรวจสอบว่าสามารถทำ Trade ใหม่ได้หรือไม่
        
        Args:
            signal_data: ข้อมูล signal ที่จะส่งออเดอร์
            
        Returns:
            Dict: ผลการตรวจสอบ
        """
        try:
            validation_result = {
                'can_trade': True,
                'reasons': [],
                'warnings': [],
                'recommended_lot_adjustment': 1.0
            }
            
            # ตรวจสอบ risk levels ปัจจุบัน
            risk_status = self.check_risk_levels()
            
            if not risk_status.get('can_trade', True):
                validation_result['can_trade'] = False
                validation_result['reasons'].append("Risk manager prohibits trading")
                validation_result['reasons'].extend(risk_status.get('restrictions', []))
            
            if risk_status.get('emergency_stop', False):
                validation_result['can_trade'] = False
                validation_result['reasons'].append("Emergency stop activated")
            
            # ปรับ lot size ตามความเสี่ยง
            risk_score = risk_status.get('risk_score', 0)
            if risk_score > 0.6:
                validation_result['recommended_lot_adjustment'] = 0.5  # ลดครึ่งหนึ่ง
                validation_result['warnings'].append("High risk - Reducing position size")
            elif risk_score > 0.4:
                validation_result['recommended_lot_adjustment'] = 0.75  # ลด 25%
                validation_result['warnings'].append("Medium risk - Slightly reducing position size")
            
            return validation_result
            
        except Exception as e:
            print(f"❌ Trade validation error: {e}")
            return {
                'can_trade': False,
                'reasons': [f"Validation error: {str(e)}"]
            }
    
    # ==========================================
    # 📊 REPORTING & STATISTICS
    # ==========================================
    
    def get_risk_summary(self) -> Dict:
        """📊 สรุปสถานะความเสี่ยงทั้งหมด"""
        try:
            current_risk = self.check_risk_levels()
            
            return {
                'overall_risk_level': current_risk.get('overall_risk', 'unknown'),
                'risk_score': current_risk.get('risk_score', 0),
                'can_trade': current_risk.get('can_trade', False),
                'emergency_stop': current_risk.get('emergency_stop', False),
                'active_warnings': len(current_risk.get('warnings', [])),
                'active_restrictions': len(current_risk.get('restrictions', [])),
                'consecutive_losses': self.consecutive_losses,
                'emergency_triggers_today': len([
                    t for t in self.emergency_triggers 
                    if t.get('timestamp', datetime.min).date() == datetime.now().date()
                ]),
                'last_check_time': current_risk.get('check_time', datetime.now())
            }
            
        except Exception as e:
            print(f"❌ Risk summary error: {e}")
            return {'error': str(e)}
    
    def get_daily_risk_report(self) -> Dict:
        """📅 รายงานความเสี่ยงรายวัน"""
        try:
            today = datetime.now().date().isoformat()
            daily_data = self.daily_stats.get(today, {})
            
            # คำนวณเปอร์เซ็นต์การใช้ขีดจำกัด
            trades_usage = (daily_data.get('trades_count', 0) / self.max_daily_trades) * 100
            volume_usage = (daily_data.get('daily_volume', 0) / self.max_daily_volume) * 100
            loss_usage = (abs(daily_data.get('daily_profit', 0)) / abs(self.max_daily_loss)) * 100 if self.max_daily_loss != 0 else 0
            
            return {
                'date': today,
                'trades_count': daily_data.get('trades_count', 0),
                'trades_usage_percent': trades_usage,
                'daily_profit': daily_data.get('daily_profit', 0.0),
                'loss_usage_percent': loss_usage,
                'daily_volume': daily_data.get('daily_volume', 0.0),
                'volume_usage_percent': volume_usage,
                'limits': {
                    'max_trades': self.max_daily_trades,
                    'max_loss': self.max_daily_loss,
                    'max_volume': self.max_daily_volume
                }
            }
            
        except Exception as e:
            print(f"❌ Daily risk report error: {e}")
            return {'error': str(e)}
    
    def force_emergency_stop(self, reason: str):
        """🚨 บังคับ Emergency Stop"""
        try:
            print(f"🚨 FORCED EMERGENCY STOP: {reason}")
            
            # บันทึก emergency trigger
            self.emergency_triggers.append({
                'timestamp': datetime.now(),
                'trigger_type': 'forced',
                'reason': reason
            })
            
            # อัพเดทสถิติ
            today = datetime.now().date().isoformat()
            if today in self.daily_stats:
                self.daily_stats[today]['emergency_stops'] = self.daily_stats[today].get('emergency_stops', 0) + 1
            
        except Exception as e:
            print(f"❌ Force emergency stop error: {e}")
    
    def reset_consecutive_losses(self):
        """🔄 รีเซ็ตการนับขาดทุนต่อเนื่อง"""
        try:
            old_count = self.consecutive_losses
            self.consecutive_losses = 0
            print(f"🔄 Consecutive losses reset: {old_count} → 0")
        except Exception as e:
            print(f"❌ Consecutive losses reset error: {e}")
    
    def is_ready(self) -> bool:
        """✅ ตรวจสอบความพร้อม"""
        return (
            self.mt5_connector is not None and
            self.config is not None
        )
    
    def get_manager_info(self) -> Dict:
        """ℹ️ ข้อมูล Risk Manager"""
        return {
            'name': 'Pure Candlestick Risk Manager',
            'version': '1.0.0',
            'max_positions': self.max_positions,
            'risk_per_trade_percent': self.risk_per_trade_percent,
            'max_daily_trades': self.max_daily_trades,
            'max_daily_loss': self.max_daily_loss,
            'min_margin_level': self.min_margin_level,
            'emergency_close_loss': self.emergency_close_loss,
            'max_consecutive_losses': self.max_consecutive_losses,
            'max_drawdown_percent': self.max_drawdown_percent
        }