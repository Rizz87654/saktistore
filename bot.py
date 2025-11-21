import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import sqlite3

# Konfigurasi
TOKEN = "7689078975:AAFg8QRmrTKC3YXjYPcinGWIHo_SrMkzoFI"
ADMIN_ID = 7235188932

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Inisialisasi database
def init_database():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            amount TEXT PRIMARY KEY,
            price INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_date TEXT
        )
    ''')
    
    # Data default
    default_prices = [
        ('1000', 5000),
        ('5000', 25000),
        ('10000', 50000),
        ('15000', 75000),
        ('20000', 100000),
        ('50000', 250000),
        ('100000', 500000)
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO prices (amount, price)
        VALUES (?, ?)
    ''', default_prices)
    
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value)
        VALUES ('stock_status', 'Tersedia')
    ''')
    
    conn.commit()
    conn.close()

# Fungsi untuk mendapatkan status stok dengan emoji
def get_stock_status_with_emoji():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'stock_status'")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        stock_status = result[0]
        if "tersedia" in stock_status.lower():
            return "🟢 " + stock_status
        elif "diisi" in stock_status.lower():
            return "🟡 " + stock_status
        elif "habis" in stock_status.lower():
            return "🔴 " + stock_status
    return "📦 Tersedia"

# Fungsi untuk mendapatkan semua harga
def get_all_prices():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT amount, price FROM prices ORDER BY CAST(amount AS INTEGER)")
    prices = cursor.fetchall()
    conn.close()
    return prices

# Fungsi untuk mendapatkan status stok
def get_stock_status():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'stock_status'")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Tersedia"

# Update website data
async def update_website_data():
    try:
        prices_data = {}
        for amount, price in get_all_prices():
            prices_data[amount] = price
        
        website_data = {
            'prices': prices_data,
            'stock_status': get_stock_status(),
            'stock_status_with_emoji': get_stock_status_with_emoji(),
            'last_update': datetime.now().isoformat(),
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        with open('website_data.json', 'w', encoding='utf-8') as f:
            json.dump(website_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Website data updated successfully")
        return True
    except Exception as e:
        print(f"❌ Error updating website data: {e}")
        return False

# Handler command start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Simpan user ke database
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, joined_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        user_id,
        update.effective_user.username,
        update.effective_user.first_name,
        update.effective_user.last_name,
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()
    
    # Dapatkan status stok terkini
    stock_status_display = get_stock_status_with_emoji()
    
    if user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("💰 Kelola Harga", callback_data="manage_prices")],
            [InlineKeyboardButton("📊 Status Stok", callback_data="stock_status")],
            [InlineKeyboardButton("👥 Statistik User", callback_data="user_stats")],
            [InlineKeyboardButton("🔄 Update Website", callback_data="update_website")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("💰 Cek Harga", callback_data="view_prices")],
            [InlineKeyboardButton("📦 Cek Stok", callback_data="check_stock")],
            [InlineKeyboardButton("🛒 Website Top Up", url="https://my-repo-ujicoba-saktistore.vercel.app")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"Halo {update.effective_user.first_name}! 👋\n\n"
    
    if user_id == ADMIN_ID:
        welcome_text += "**Admin Panel Top Up BBC**\n\n"
        welcome_text += "Anda dapat:\n"
        welcome_text += "• Mengelola harga BBC\n"
        welcome_text += "• Update status stok\n"
        welcome_text += "• Melihat statistik\n"
        welcome_text += "• Update website secara real-time\n"
    else:
        welcome_text += "**Bot Info Top Up BBC MLBB**\n\n"
        welcome_text += "Saya dapat membantu Anda:\n"
        welcome_text += "• Melihat harga terbaru BBC\n"
        welcome_text += "• Cek status stok terkini\n"
        welcome_text += "• Info pembaruan harga\n\n"
        welcome_text += f"📦 Status Stok Saat Ini: {stock_status_display}\n\n"
        
        # Tambahkan peringatan jika stok habis
        if "habis" in stock_status_display.lower():
            welcome_text += "⚠️ *PERINGATAN:* Stok BBC sedang habis. Pembelian sementara tidak dapat diproses.\n\n"
        elif "diisi" in stock_status_display.lower():
            welcome_text += "ℹ️ *INFORMASI:* Stok BBC sedang diisi ulang. Proses pembelian mungkin sedikit lebih lambat.\n\n"
        
        welcome_text += "Untuk pembelian, kunjungi website kami!"
    
    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Handler untuk tombol callback
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "view_prices":
        await show_prices(query)
    elif data == "manage_prices" and user_id == ADMIN_ID:
        await manage_prices(query)
    elif data == "stock_status" and user_id == ADMIN_ID:
        await stock_status_menu(query)
    elif data == "check_stock":
        await check_stock(query)
    elif data == "user_stats" and user_id == ADMIN_ID:
        await user_stats(query)
    elif data == "update_website" and user_id == ADMIN_ID:
        await update_website(query)
    elif data.startswith("edit_price_"):
        await edit_price(query, context)
    elif data.startswith("set_stock_"):
        await set_stock(query)
    elif data == "back_to_main":
        await start(update, context)

async def show_prices(query):
    prices = get_all_prices()
    stock_status_display = get_stock_status_with_emoji()
    
    prices_text = "💰 *HARGA BBC TERBARU* 💰\n\n"
    for amount, price in prices:
        prices_text += f"• {amount} BBC : Rp {price:,}\n"
    
    prices_text += f"\n📊 Status Stok: {stock_status_display}"
    prices_text += f"\n\n_Update: {datetime.now().strftime('%d/%m/%Y %H:%M')}_"
    
    # Tambahkan peringatan berdasarkan status stok
    if "habis" in stock_status_display.lower():
        prices_text += "\n\n⚠️ *PERINGATAN:* Stok BBC sedang habis. Pembelian sementara tidak dapat diproses."
    elif "diisi" in stock_status_display.lower():
        prices_text += "\n\nℹ️ *INFORMASI:* Stok BBC sedang diisi ulang. Proses pembelian mungkin sedikit lebih lambat."
    
    keyboard = [[InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        prices_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def manage_prices(query):
    prices = get_all_prices()
    
    keyboard = []
    for amount, price in prices:
        keyboard.append([InlineKeyboardButton(
            f"{amount} BBC - Rp {price:,}", 
            callback_data=f"edit_price_{amount}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📝 *KELOLA HARGA BBC*\n\nPilih paket yang ingin diedit:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def edit_price(query, context):
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Akses ditolak.")
        return
    
    amount = query.data.replace("edit_price_", "")
    
    # Simpan amount yang sedang diedit
    context.user_data['editing_amount'] = amount
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM prices WHERE amount = ?", (amount,))
    result = cursor.fetchone()
    conn.close()
    
    current_price = result[0] if result else 0
    
    await query.edit_message_text(
        f"✏️ Edit Harga {amount} BBC\n\n"
        f"Harga saat ini: Rp {current_price:,}\n\n"
        "Kirim harga baru (dalam Rupiah, tanpa titik/koma):",
        parse_mode='Markdown'
    )

async def stock_status_menu(query):
    current_status = get_stock_status()
    current_status_display = get_stock_status_with_emoji()
    
    keyboard = [
        [InlineKeyboardButton("🟢 Tersedia", callback_data="set_stock_available")],
        [InlineKeyboardButton("🟡 Sedang Diisi", callback_data="set_stock_refilling")],
        [InlineKeyboardButton("🔴 Stok Habis", callback_data="set_stock_out")],
        [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📦 *KELOLA STATUS STOK*\n\nStatus saat ini: {current_status_display}\n\nPilih status baru:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def set_stock(query):
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Akses ditolak.")
        return
    
    stock_action = query.data.replace("set_stock_", "")
    
    if stock_action == "available":
        new_status = "Tersedia"
    elif stock_action == "refilling":
        new_status = "Sedang Diisi Ulang"
    elif stock_action == "out":
        new_status = "Stok Habis"
    else:
        new_status = "Tersedia"
    
    # Update database
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('stock_status', ?)",
        (new_status,)
    )
    conn.commit()
    conn.close()
    
    # Update website secara real-time
    await update_website_data()
    
    await query.edit_message_text(
        f"✅ Status stok berhasil diubah menjadi:\n*{new_status}*",
        parse_mode='Markdown'
    )

async def check_stock(query):
    stock_status_display = get_stock_status_with_emoji()
    
    keyboard = [[InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status_text = f"*STATUS STOK BBC*\n\n"
    status_text += f"Status: {stock_status_display}\n"
    status_text += f"Update: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    # Tambahkan peringatan berdasarkan status stok
    if "habis" in stock_status_display.lower():
        status_text += "⚠️ *PERINGATAN:* Stok BBC sedang habis. Pembelian sementara tidak dapat diproses.\n\n"
    elif "diisi" in stock_status_display.lower():
        status_text += "ℹ️ *INFORMASI:* Stok BBC sedang diisi ulang. Proses pembelian mungkin sedikit lebih lambat.\n\n"
    
    status_text += "Untuk informasi real-time, kunjungi website kami."
    
    await query.edit_message_text(
        status_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def user_stats(query):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE joined_date >= date('now', '-7 days')")
    new_users_week = cursor.fetchone()[0]
    
    conn.close()
    
    await query.edit_message_text(
        f"👥 *STATISTIK PENGGUNA*\n\n"
        f"• Total Users: *{total_users}*\n"
        f"• User Baru (7 hari): *{new_users_week}*\n"
        f"• Update: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        parse_mode='Markdown'
    )

async def update_website(query):
    success = await update_website_data()
    if success:
        await query.edit_message_text(
            "✅ Website berhasil diupdate dengan data terbaru!",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "❌ Gagal mengupdate website. Silakan coba lagi.",
            parse_mode='Markdown'
        )

# Handler untuk pesan teks (edit harga)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Anda tidak memiliki akses.")
        return
    
    if 'editing_amount' in context.user_data:
        try:
            amount = context.user_data['editing_amount']
            new_price = int(update.message.text.replace('.', '').replace(',', ''))
            
            # Update database
            conn = sqlite3.connect('bot_data.db')
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE prices SET price = ? WHERE amount = ?",
                (new_price, amount)
            )
            conn.commit()
            conn.close()
            
            # Update website
            await update_website_data()
            
            del context.user_data['editing_amount']
            
            await update.message.reply_text(
                f"✅ Harga {amount} BBC berhasil diupdate!\n"
                f"💰 Harga baru: Rp {new_price:,}",
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Format harga tidak valid. Harap masukkan angka saja.\n"
                "Contoh: 75000"
            )

# Command untuk set stok
async def setstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Akses ditolak.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /setstock <status>\n"
            "Contoh: /setstock \"Stok Habis - Sedang diisi ulang\""
        )
        return
    
    new_status = ' '.join(context.args)
    
    # Update database
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('stock_status', ?)",
        (new_status,)
    )
    conn.commit()
    conn.close()
    
    # Update website
    await update_website_data()
    
    await update.message.reply_text(
        f"✅ Status stok berhasil diubah menjadi:\n*{new_status}*",
        parse_mode='Markdown'
    )

# Command untuk stats
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Akses ditolak.")
        return
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    prices = get_all_prices()
    
    stock_status = get_stock_status()
    
    conn.close()
    
    stats_text = f"📊 *STATISTIK BOT*\n\n"
    stats_text += f"• Total Users: {total_users}\n"
    stats_text += f"• Status Stok: {stock_status}\n\n"
    stats_text += f"*Harga Saat Ini:*\n"
    
    for amount, price in prices:
        stats_text += f"• {amount} BBC: Rp {price:,}\n"
    
    stats_text += f"\n_Update: {datetime.now().strftime('%d/%m/%Y %H:%M')}_"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

def main():
    # Inisialisasi database
    init_database()
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setstock", setstock_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    print("🤖 Bot sedang berjalan...")
    application.run_polling()

if __name__ == '__main__':
    main()