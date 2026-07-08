import os
import logging
import re
import statistics
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import textstat

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)

# --- Text Analysis Engine ---
def analyze_readability(text: str):
    """Runs multiple readability formulas and identifies complex areas."""
    
    # 1. Basic Stats
    word_count = len(text.split())
    sentence_count = len(re.findall(r'[.!?]+', text))
    char_count = len(text)

    # 2. Readability Scores (Multiple Formulas)
    try:
        scores = {
            'flesch_kincaid': textstat.flesch_kincaid_grade(text),
            'gunning_fog': textstat.gunning_fog(text),
            'smog': textstat.smog_index(text),
            'coleman_liau': textstat.coleman_liau_index(text),
            'automated_readability': textstat.automated_readability_index(text),
            'dale_chall': textstat.dale_chall_readability_score(text) if textstat.dale_chall_readability_score(text) <= 9 else 9.9,
            'linsear_write': textstat.linsear_write_formula(text),
        }
        # Calculate consensus grade (average of all formulas)
        grade_values = [v for v in scores.values() if isinstance(v, (int, float)) and v >= 0]
        consensus_grade = round(statistics.mean(grade_values), 1) if grade_values else 0
    except:
        scores = {}
        consensus_grade = 0

    # 3. Hemingway-Style Highlights
    hard_words = []
    very_hard_words = []
    passive_voice_pattern = r'\b(am|are|is|was|were|be|been|being)\s+\w+ed\b'
    
    sentences = re.split(r'[.!?]+', text)
    for sent in sentences:
        words = sent.split()
        if len(words) > 20:
            hard_words.append(sent.strip())
        if len(words) > 30:
            very_hard_words.append(sent.strip())
            
    passive_voice = re.findall(passive_voice_pattern, text, re.IGNORECASE)

    return {
        'word_count': word_count,
        'sentence_count': sentence_count,
        'char_count': char_count,
        'consensus_grade': consensus_grade,
        'scores': scores,
        'hard_sentences': hard_words[:5],
        'very_hard_sentences': very_hard_words[:5],
        'passive_voice_count': len(passive_voice),
    }

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *HemingwayBot*!\n\n"
        "Send me any text, and I'll analyze its readability using multiple formulas. "
        "I'll highlight hard sentences, track passive voice, and give you a consensus grade.\n\n"
        "Built with ❤️ using Python + Railway.",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if len(user_text) < 10:
        await update.message.reply_text("Please send a longer text (at least 10 characters) for proper analysis.")
        return

    await update.message.reply_text("🧐 Analyzing your text...")
    
    analysis = analyze_readability(user_text)
    
    # Build a readable report
    report = (
        f"📊 *Readability Report*\n\n"
        f"📝 Words: {analysis['word_count']}\n"
        f"📄 Sentences: {analysis['sentence_count']}\n"
        f"🔤 Characters: {analysis['char_count']}\n\n"
        f"📈 *Consensus Grade Level:* {analysis['consensus_grade']} / 18\n"
        f"(Lower is better. Aim for 8-10 for general audiences.)\n\n"
        f"⚡ Passive voice instances: {analysis['passive_voice_count']}\n"
    )
    
    if analysis['hard_sentences']:
        report += f"\n🔴 *Hard Sentences* (20+ words):\n"
        for s in analysis['hard_sentences'][:3]:
            report += f"- {s[:80]}...\n"
            
    if analysis['very_hard_sentences']:
        report += f"\n🔥 *Very Hard Sentences* (30+ words):\n"
        for s in analysis['very_hard_sentences'][:3]:
            report += f"- {s[:80]}...\n"
    
    await update.message.reply_text(report, parse_mode='Markdown')

def main():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")
    
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot is starting with long polling...")
    app.run_polling()

if __name__ == '__main__':
    main()
