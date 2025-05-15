import time
from exchange.binance_connector import BinanceTrader
from strategies.ob_choch_fib import TradingStrategy
from telegram.notifications import Notifier
import config

def main():
    # تهيئة المكونات
    trader = BinanceTrader()
    strategy = TradingStrategy()
    notifier = Notifier()
    
    # اختبار الاتصال
    try:
        price = trader.get_btc_price()
        notifier.send_trade_alert({
            'side': 'TEST',
            'amount': config.INITIAL_BALANCE,
            'price': price,
            'strategy': 'Initial Connection Test',
            'balance': config.INITIAL_BALANCE
        })
        print("✅ تم الاتصال بنجاح بـ Binance Testnet")
    except Exception as e:
        print(f"❌ فشل الاتصال: {e}")
        return

    # حلقة التداول الرئيسية
    while True:
        try:
            # 1. الحصول على سعر BTC الحالي
            current_price = trader.get_btc_price()
            
            # 2. تحليل الإستراتيجية
            signal = strategy.analyze({'price': current_price})
            
            # 3. تنفيذ الصفقة إذا كانت الإشارة قوية
            if signal['confidence'] > 0.7:
                # حساب حجم الصفقة (0.1% من رأس المال)
                quantity = (config.INITIAL_BALANCE * 0.001) / current_price
                
                # تنفيذ الصفقة
                order = trader.create_order(
                    side=signal['action'],
                    quantity=quantity
                )
                
                # إرسال الإشعار
                if 'error' not in order:
                    notifier.send_trade_alert({
                        'side': signal['action'],
                        'amount': quantity * current_price,
                        'price': current_price,
                        'strategy': strategy.strategy_name,
                        'balance': config.INITIAL_BALANCE
                    })
            
            time.sleep(60)  # الانتظار دقيقة بين كل فحص
            
        except Exception as e:
            print(f"حدث خطأ: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
