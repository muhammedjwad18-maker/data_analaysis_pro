import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import asyncio
import threading
import json
import sqlite3
from datetime import datetime

# 🔧 إعدادات البوت - التوكن الخاص بك
BOT_TOKEN = "8271273469:AAF6oPqkSm14mvfyao9Mz45uOaj_qsXo5Gg"

class TelegramPaymentBot:
    def __init__(self, db_manager, payment_system):
        self.db = db_manager
        self.payment_system = payment_system
        self.token = BOT_TOKEN
        self.application = None
        self.bot = None
        
        # قائمة المسؤولين - سنضيف ID حسابك تلقائياً
        self.admin_users = [7355375396]  # سيتم ملؤها تلقائياً
        
    async def start_bot(self):
        """بدء تشغيل البوت"""
        try:
            self.application = Application.builder().token(self.token).build()
            self.bot = telegram.Bot(token=self.token)
            
            # الحصول على معلومات البوت
            bot_info = await self.bot.get_me()
            bot_username = bot_info.username
            print(f"🤖 البوت يعمل بنجاح: @{bot_username}")
            print(f"🔗 رابط البوت: https://t.me/{bot_username}")
            
            # إضافة handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("admin", self.admin_command))
            self.application.add_handler(CommandHandler("stats", self.stats_command))
            self.application.add_handler(CommandHandler("id", self.get_id_command))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            
            print("✅ بوت الدفع يعمل وجاهز لاستقبال الأوامر...")
            await self.application.run_polling()
            
        except Exception as e:
            print(f"❌ خطأ في تشغيل البوت: {e}")

    async def start_command(self, update: Update, context):
        """أمر /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "بدون اسم"
        first_name = update.effective_user.first_name or "مستخدم"
        
        print(f"👤 مستخدم جديد: {user_id} - @{username} - {first_name}")
        
        # إذا كان هذا أول مستخدم، أضفه كمسؤول
        if not self.admin_users:
            self.admin_users.append(user_id)
            print(f"👑 تم تعيين المستخدم {user_id} كمسؤول رئيسي")
            
            welcome_text = f"""
            👑 **مرحباً بك {first_name}!**

            ✅ لقد تم تعيينك كمسؤول رئيسي في النظام
            🤖 هذا البوت سيتلقى إشعارات الدفع تلقائياً

            📊 **الأوامر المتاحة:**
            /admin - لوحة التحكم
            /stats - إحصائيات النظام  
            /id - عرض رقمك

            🔔 **سيصلك إشعار** عند كل دفعة جديدة
            ✅ **يمكنك تفعيل الحسابات** بنقرة واحدة

            🆔 **رقمك:** `{user_id}`
            👤 **اسمك:** {first_name}
            """
            
            keyboard = [
                [InlineKeyboardButton("📊 لوحة التحكم", callback_data="admin_panel")],
                [InlineKeyboardButton("🆔 عرض رقمي", callback_data="show_id")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif user_id in self.admin_users:
            # إذا كان مسؤولاً موجوداً
            welcome_text = f"""
            👑 **مرحباً بعودتك {first_name}!**

            ✅ أنت مسؤول في النظام
            📊 للإحصائيات: /stats
            🛠 للإدارة: /admin

            🆔 رقمك: `{user_id}`
            """
            
            keyboard = [
                [InlineKeyboardButton("📊 إحصائيات النظام", callback_data="stats")],
                [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="manage_users")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        else:
            # إذا كان مستخدم عادي
            welcome_text = f"""
            🤖 **مرحباً بك {first_name}!**

            🔔 هذا البوت مخصص لإدارة مدفوعات Data Analysis Pro
            📞 للاستفسارات، تواصل مع المسؤول.

            👤 أنت: {first_name}
            🆔 رقمك: `{user_id}`
            """
            await update.message.reply_text(welcome_text, parse_mode='Markdown')
            
            # إعلام المسؤولين بمستخدم جديد
            for admin_id in self.admin_users:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=f"👤 مستخدم جديد يتفقد البوت:\n👤 الاسم: {first_name}\n🆔 الرقم: `{user_id}`\n📱 المعرف: @{username}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"❌ خطأ في إرسال إشعار للمسؤول: {e}")

    async def get_id_command(self, update: Update, context):
        """أمر /id لمعرفة رقم المستخدم"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "بدون معرف"
        first_name = update.effective_user.first_name or "مستخدم"
        
        id_text = f"""
        🆔 **معلومات حسابك:**

        👤 **الاسم:** {first_name}
        📱 **المعرف:** @{username}
        🔢 **الرقم:** `{user_id}`

        💡 **ملاحظة:** احفظ هذا الرقم للإعدادات
        """
        
        await update.message.reply_text(id_text, parse_mode='Markdown')

    async def admin_command(self, update: Update, context):
        """لوحة تحكم المسؤول"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_users:
            await update.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا الأمر")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 إحصائيات النظام", callback_data="stats")],
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="manage_users")],
            [InlineKeyboardButton("💰 المدفوعات المعلقة", callback_data="pending_payments")],
            [InlineKeyboardButton("🔄 آخر المدفوعات", callback_data="recent_payments")],
            [InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="bot_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👑 **لوحة تحكم المسؤول**\n\nاختر الإدارة المناسبة:",
            reply_markup=reply_markup
        )

    async def stats_command(self, update: Update, context):
        """إحصائيات النظام"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_users:
            await update.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا الأمر")
            return
        
        stats_text = self.get_system_stats()
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    def get_system_stats(self):
        """الحصول على إحصائيات النظام"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            # عدد المستخدمين
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # المستخدمين النشطين
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_login > datetime('now', '-7 days')")
            active_users = cursor.fetchone()[0]
            
            # المدفوعات
            cursor.execute("SELECT COUNT(*) FROM payments")
            total_payments = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM payments WHERE payment_status = 'completed'")
            completed_payments = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM payments WHERE DATE(created_at) = DATE('now')")
            today_payments = cursor.fetchone()[0]
            
            # إجمالي الإيرادات
            cursor.execute("SELECT SUM(amount) FROM payments WHERE payment_status = 'completed'")
            total_revenue = cursor.fetchone()[0] or 0
            
            # الخطط
            cursor.execute("SELECT account_type, COUNT(*) FROM users GROUP BY account_type")
            plan_stats = cursor.fetchall()
            
            conn.close()
            
            # بناء النص
            stats_text = f"""
📊 **إحصائيات النظام الشاملة**

👥 **المستخدمون:**
• إجمالي المستخدمين: {total_users}
• المستخدمين النشطين: {active_users}

💰 **المدفوعات:**
• إجمالي المدفوعات: {total_payments}
• المدفوعات المكتملة: {completed_payments}
• مدفوعات اليوم: {today_payments}
• إجمالي الإيرادات: {total_revenue:,} دينار

📋 **توزيع الخطط:**
"""
            
            for plan_type, count in plan_stats:
                stats_text += f"• {plan_type}: {count} مستخدم\n"
            
            stats_text += f"\n🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            stats_text += f"\n👑 عدد المسؤولين: {len(self.admin_users)}"
            
            return stats_text
            
        except Exception as e:
            return f"❌ خطأ في جلب الإحصائيات: {str(e)}"

    async def handle_callback(self, update: Update, context):
        """معالجة ضغطات الأزرار"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if user_id not in self.admin_users:
            await query.edit_message_text("❌ ليس لديك صلاحية لهذا الإجراء")
            return
        
        if data == "stats":
            stats_text = self.get_system_stats()
            await query.edit_message_text(stats_text, parse_mode='Markdown')
            
        elif data == "admin_panel":
            await self.admin_command(update, context)
            
        elif data == "show_id":
            user_id = query.from_user.id
            await query.edit_message_text(f"🆔 رقمك هو: `{user_id}`", parse_mode='Markdown')
            
        elif data == "manage_users":
            users_text = self.get_users_list()
            await query.edit_message_text(users_text, parse_mode='Markdown')
            
        elif data == "pending_payments":
            payments_text = self.get_pending_payments()
            await query.edit_message_text(payments_text, parse_mode='Markdown')
            
        elif data == "recent_payments":
            payments_text = self.get_recent_payments()
            await query.edit_message_text(payments_text, parse_mode='Markdown')
            
        elif data == "bot_settings":
            settings_text = self.get_bot_settings()
            await query.edit_message_text(settings_text, parse_mode='Markdown')
            
        elif data.startswith("activate_"):
            await self.activate_user_account(query, data)
            
        elif data.startswith("reject_"):
            await self.reject_payment(query, data)
            
        elif data.startswith("user_details_"):
            await self.show_user_details(query, data)

    async def activate_user_account(self, query, data):
        """تفعيل حساب المستخدم"""
        try:
            parts = data.split("_")
            target_user_id = int(parts[1])
            plan_type = parts[2]
            transaction_id = parts[3] if len(parts) > 3 else "غير معروف"
            
            success = self.db.update_user_account(target_user_id, plan_type)
            
            if success:
                # تحديث حالة الدفع
                self.update_payment_status(transaction_id, 'completed')
                
                await query.edit_message_text(
                    f"✅ **تم تفعيل الحساب بنجاح**\n\n"
                    f"👤 المستخدم: `{target_user_id}`\n"
                    f"📋 الخطة: {plan_type}\n"
                    f"🧾 المعاملة: `{transaction_id}`\n"
                    f"🕒 الوقت: {datetime.now().strftime('%H:%M')}"
                )
                
                # إرسال إشعار للمسؤولين
                for admin_id in self.admin_users:
                    if admin_id != query.from_user.id:
                        try:
                            await self.bot.send_message(
                                chat_id=admin_id,
                                text=f"✅ تم تفعيل حساب المستخدم `{target_user_id}`\nالخطة: {plan_type}",
                                parse_mode='Markdown'
                            )
                        except:
                            pass
                    
            else:
                await query.edit_message_text("❌ فشل في تفعيل الحساب")
                
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في التفعيل: {str(e)}")

    async def reject_payment(self, query, data):
        """رفض الدفع"""
        transaction_id = data.split("_")[1]
        
        self.update_payment_status(transaction_id, 'rejected')
        
        await query.edit_message_text(
            f"❌ **تم رفض الدفع**\n\n"
            f"🧾 رقم المعاملة: `{transaction_id}`\n"
            f"🕒 الوقت: {datetime.now().strftime('%H:%M')}"
        )

    async def show_user_details(self, query, data):
        """عرض تفاصيل المستخدم"""
        try:
            user_id = int(data.split("_")[2])
            user_info = self.db.get_user_info(user_id)
            
            if user_info:
                user_text = f"""
👤 **تفاصيل المستخدم**

🆔 **الرقم:** `{user_info['id']}`
👤 **الاسم:** {user_info['username']}
📧 **البريد:** {user_info.get('email', 'غير محدد')}
📋 **الخطة:** {user_info['account_type']}
📅 **تاريخ التسجيل:** {user_info['created_at']}
🔐 **آخر دخول:** {user_info.get('last_login', 'غير معروف')}
✅ **الحالة:** {'نشط' if user_info.get('is_active', True) else 'غير نشط'}
                """
            else:
                user_text = "❌ المستخدم غير موجود"
                
            await query.edit_message_text(user_text, parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في جلب البيانات: {str(e)}")

    def get_users_list(self):
        """قائمة المستخدمين"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, account_type, created_at, last_login 
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            users = cursor.fetchall()
            
            conn.close()
            
            if not users:
                return "📭 لا يوجد مستخدمين بعد"
            
            users_text = "👥 **آخر 20 مستخدم**\n\n"
            
            for user in users:
                user_id, username, account_type, created_at, last_login = user
                users_text += f"🆔 `{user_id}` - 👤 {username}\n"
                users_text += f"   📋 {account_type} - 📅 {created_at[:10]}\n\n"
            
            return users_text
            
        except Exception as e:
            return f"❌ خطأ في جلب المستخدمين: {str(e)}"

    def get_pending_payments(self):
        """المدفوعات المعلقة"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.transaction_id, p.user_id, u.username, p.amount, p.plan_type, p.created_at
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.id
                WHERE p.payment_status = 'pending'
                ORDER BY p.created_at DESC
            """)
            payments = cursor.fetchall()
            
            conn.close()
            
            if not payments:
                return "✅ لا توجد مدفوعات معلقة"
            
            payments_text = "💰 **المدفوعات المعلقة**\n\n"
            
            for payment in payments:
                transaction_id, user_id, username, amount, plan_type, created_at = payment
                payments_text += f"🧾 `{transaction_id}`\n"
                payments_text += f"👤 {username} (`{user_id}`)\n"
                payments_text += f"💵 {amount:,} دينار - 📋 {plan_type}\n"
                payments_text += f"🕒 {created_at}\n\n"
            
            return payments_text
            
        except Exception as e:
            return f"❌ خطأ في جلب المدفوعات: {str(e)}"

    def get_recent_payments(self):
        """آخر المدفوعات"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.transaction_id, u.username, p.amount, p.plan_type, p.payment_status, p.created_at
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.id
                ORDER BY p.created_at DESC
                LIMIT 10
            """)
            payments = cursor.fetchall()
            
            conn.close()
            
            if not payments:
                return "📭 لا توجد مدفوعات بعد"
            
            payments_text = "🔄 **آخر 10 مدفوعات**\n\n"
            
            for payment in payments:
                transaction_id, username, amount, plan_type, status, created_at = payment
                status_icon = "✅" if status == 'completed' else "🔄" if status == 'pending' else "❌"
                payments_text += f"{status_icon} `{transaction_id[:12]}...`\n"
                payments_text += f"👤 {username} - 💵 {amount:,} دينار\n"
                payments_text += f"📋 {plan_type} - 🕒 {created_at[:16]}\n\n"
            
            return payments_text
            
        except Exception as e:
            return f"❌ خطأ في جلب المدفوعات: {str(e)}"

    def get_bot_settings(self):
        """إعدادات البوت"""
        settings_text = f"""
⚙️ **إعدادات البوت**

🤖 **اسم البوت:** Data Analysis Pro Payments
👑 **عدد المسؤولين:** {len(self.admin_users)}
🆔 **المسؤولين:** {', '.join([str(admin) for admin in self.admin_users])}

🕒 **وقت التشغيل:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
✅ **الحالة:** يعمل بشكل طبيعي

💡 **لإضافة مسؤولين:** أرسل /start من الحساب المراد إضافته
        """
        return settings_text

    def update_payment_status(self, transaction_id, status):
        """تحديث حالة الدفع"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE payments 
                SET payment_status = ? 
                WHERE transaction_id = ?
            ''', (status, transaction_id))
            
            conn.commit()
            conn.close()
            print(f"✅ تم تحديث حالة الدفع {transaction_id} إلى {status}")
            
        except Exception as e:
            print(f"❌ خطأ في تحديث حالة الدفع: {e}")

    def run_in_thread(self):
        """تشغيل البوت في thread منفصل"""
        def run():
            asyncio.run(self.start_bot())
        
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

# نظام إرسال الفواتير
class InvoiceManager:
    def __init__(self, telegram_bot, db_manager):
        self.bot = telegram_bot
        self.db = db_manager
    
    async def send_invoice_to_admins(self, payment_data):
        """إرسال الفاتورة لجميع المسؤولين"""
        try:
            invoice_text = self.generate_invoice_text(payment_data)
            
            if not self.bot.admin_users:
                print("⚠️ لا يوجد مسؤولين لإرسال الفاتورة لهم")
                return
            
            for admin_id in self.bot.admin_users:
                try:
                    keyboard = [
                        [
                            InlineKeyboardButton("✅ تفعيل الحساب", 
                                              callback_data=f"activate_{payment_data['user_id']}_{payment_data['plan_type']}_{payment_data['transaction_id']}"),
                            InlineKeyboardButton("❌ رفض الدفع", 
                                              callback_data=f"reject_{payment_data['transaction_id']}")
                        ],
                        [
                            InlineKeyboardButton("👤 تفاصيل المستخدم", 
                                              callback_data=f"user_details_{payment_data['user_id']}")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await self.bot.bot.send_message(
                        chat_id=admin_id,
                        text=invoice_text,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    
                    print(f"✅ تم إرسال الفاتورة للمسؤول {admin_id}")
                    
                except Exception as e:
                    print(f"❌ خطأ في إرسال الفاتورة للمسؤول {admin_id}: {e}")
                    
        except Exception as e:
            print(f"❌ خطأ عام في إرسال الفواتير: {e}")
    
    def generate_invoice_text(self, payment_data):
        """توليد نص الفاتورة"""
        return f"""
🧾 **فاتورة دفع جديدة**

👤 **المستخدم:** {payment_data['username']}
🆔 **رقم المستخدم:** `{payment_data['user_id']}`
📧 **البريد الإلكتروني:** {payment_data.get('email', 'غير محدد')}

💳 **تفاصيل الدفع:**
• رقم المعاملة: `{payment_data['transaction_id']}`
• المبلغ: {payment_data['amount']:,} دينار عراقي
• الضريبة: {payment_data.get('tax_amount', 0):,} دينار
• الإجمالي: {payment_data.get('total_amount', payment_data['amount']):,} دينار

📋 **الخطة المطلوبة:** {payment_data['plan_type']}
🕒 **وقت الدفع:** {payment_data.get('payment_date', datetime.now().strftime('%Y-%m-%d %H:%M'))}
🏦 **طريقة الدفع:** {payment_data.get('payment_method', 'غير محدد')}

🔍 **حالة الحساب الحالية:** {payment_data.get('current_plan', 'غير معروف')}
        """