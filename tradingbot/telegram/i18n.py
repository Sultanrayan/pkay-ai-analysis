"""Bilingual user-facing strings (English / Khmer).

Formatting is done at call time with ``{placeholders}`` (``str.format``
syntax). Unknown keys fall back to English, then to the key itself, so adding
a feature never breaks rendering in the other language.
"""

from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "kh")
DEFAULT_LANGUAGE = "en"

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Buttons / navigation
        "btn_analyze": "🔍 Analyze",
        "btn_sniper": "🎯 Sniper",
        "btn_history": "🕘 History",
        "btn_settings": "⚙️ Settings",
        "btn_help": "❓ Help",
        "btn_menu": "🏠 Main Menu",
        "btn_refresh": "🔄 Refresh",
        "btn_export": "📄 Export",
        "btn_back": "◀ Back",
        "lang_en": "🇬🇧 English",
        "lang_kh": "🇰🇭 ភាសាខ្មែរ",
        "btn_btcusdt": "₿ BTCUSDT",
        "btn_ethusdt": "Ξ ETHUSDT",
        "btn_solusdt": "◎ SOLUSDT",
        "btn_xauusd": "🥇 XAUUSD",
        "btn_all": "🔀 All",
        "btn_memecoin": "🐸 Memecoin",
        # Timeframe buttons
        "tf_1h": "1H", "tf_4h": "4H", "tf_1d": "1D", "tf_1w": "1W",
        # Welcome / help
        "welcome_title": "Welcome to the Trading Analysis Bot 👋",
        "welcome_body": (
            "Get on-demand multi-agent analysis for <b>BTCUSDT</b>, "
            "<b>ETHUSDT</b>, <b>SOLUSDT</b> and <b>XAUUSD</b>.\\n\\n"
            "Use the buttons below or type a command:\\n"
            "/analyze — start a new analysis\\n"
            "/sniper — scan memecoin opportunities (signal-only)\\n"
            "/history — view past reports\\n"
            "/settings — change language & preferences\\n"
            "/help — more help\\n\\n"
            "<i>Analysis is for information only and is not financial advice.</i>"
        ),
        "help_title": "Help & Commands",
        "help_body": (
            "/analyze — analyze BTCUSDT, ETHUSDT, SOLUSDT or XAUUSD "
            "(e.g. <code>/analyze ETHUSDT 4h</code>)\\n"
            "/sniper — memecoin scan (signal-only, never places orders)\\n"
            "/history — show your last 10 analyses\\n"
            "/settings — language and report options\\n"
            "/about — bot information\\n"
            "/cancel — cancel the current action\\n\\n"
            "Timeframes: <code>1h</code>, <code>4h</code>, <code>1d</code>, <code>1w</code>.\\n"
            "Daily analysis limit: {limit} requests."
        ),
        "about_text": (
            "🤖 <b>Trading Analysis Bot</b> v{version}\\n"
            "Multi-asset analysis for BTCUSDT, ETHUSDT, SOLUSDT & XAUUSD with "
            "10 specialized agents across technical, market-intelligence and "
            "risk teams, plus a signal-only memecoin sniper. Reports can be "
            "enriched by DeepSeek-V4-Flash.\\n\\n"
            "<i>Not financial advice.</i>"
        ),
        # Flow prompts
        "asset_prompt": "Which asset would you like to analyze?",
        "tf_prompt": "Select a timeframe for {symbol}:",
        "analyzing": "⏳ Analyzing {symbol} {timeframe} — a few seconds…",
        "rate_limited": "⛔ You reached your daily limit of {limit} analyses. It resets at midnight UTC.",
        "error_generic": "❌ Something went wrong while analyzing. Please try again in a moment.",
        "cancel_done": "Cancelled. Tap Main Menu to continue.",
        # History
        "history_title": "📂 Your last {limit} analyses",
        "history_empty": "You have no analyses yet. Tap <b>Analyze</b> to create your first report.",
        "history_row": "#{row_id} · {symbol} {timeframe} · {signal}",
        # Report
        "report_title": "{symbol} Analysis Report",
        "lbl_time": "Time",
        "lbl_timeframe": "Timeframe",
        "lbl_price": "Current Price",
        "lbl_signal": "Signal",
        "lbl_score": "Score",
        "lbl_confidence": "Confidence",
        "lbl_source": "Data",
        "sec_consensus": "🤝 Agent Consensus",
        "lbl_team_technical": "Technical",
        "lbl_team_intel": "Intel",
        "lbl_team_risk": "Risk",
        "lbl_team_sniper": "Sniper",
        "lbl_market_intel": "Market Intel",
        "sec_technical": "📈 Technical Indicators",
        "sec_sentiment": "💬 Market Sentiment",
        "sec_onchain": "⛓ On-Chain",
        "sec_macro": "🌐 Macro",
        "sec_risk": "🛡️ Risk Management",
        "sec_correlation": "🔗 Correlation",
        "sec_sniper": "🎯 Sniper Scan",
        "sec_summary": "📝 Summary",
        "lbl_rsi": "RSI (14)",
        "lbl_macd": "MACD",
        "lbl_macd_signal": "MACD Signal",
        "lbl_ma50": "MA 50",
        "lbl_ma200": "MA 200",
        "lbl_support": "Support",
        "lbl_resistance": "Resistance",
        "lbl_volume": "Volume",
        "lbl_obv": "OBV trend",
        "lbl_volatility": "Volatility",
        "lbl_band_position": "Band position",
        "lbl_squeeze": "Band squeeze",
        "lbl_pattern": "Pattern",
        "lbl_breakout": "Breakout",
        "lbl_news": "News",
        "lbl_fng": "Fear & Greed",
        "lbl_social": "Social Volume",
        "lbl_whale": "Whale activity",
        "lbl_netflow": "Exchange netflow",
        "lbl_active": "Active addresses",
        "lbl_mvrv": "MVRV",
        "lbl_sopr": "SOPR",
        "lbl_rate": "Rate policy",
        "lbl_dxy": "DXY (dollar)",
        "lbl_inflation": "Inflation",
        "lbl_sl": "Stop Loss",
        "lbl_tp": "Take Profit",
        "lbl_pos": "Position Size",
        "lbl_atr": "ATR (14)",
        "lbl_vol": "Volatility",
        "lbl_corr": "Correlation (r)",
        "lbl_headlines": "Headlines",
        "lbl_opportunity": "Opportunity",
        "lbl_safety": "Safety",
        "lbl_liquidity": "Liquidity",
        "lbl_hype": "Hype",
        "lbl_chain": "Chain",
        "lbl_risk_flags": "Risk flags",
        "sniper_title": "🎯 Sniper Scan",
        "sniper_empty": "No opportunities passed the safety & liquidity filters right now.",
        "sniper_disclaimer": "💡 <i>Signal-only detection — no orders are ever placed.</i>",
        "ai_enhanced": "🤖 AI-enhanced (DeepSeek-V4-Flash)",
        "demo_notice": "⚠️ <i>Simulated/heuristic data: {sources} — configure live APIs in .env</i>",
        "na": "n/a",
        # Settings
        "settings_title": "⚙️ Settings",
        "settings_lang": "Language",
        "settings_chart": "Chart image",
        "settings_indicators": "Indicators section",
        "settings_risk": "Risk section",
        "settings_sentiment": "Sentiment section",
        "value_on": "✅ On",
        "value_off": "⛔ Off",
        "exported": "📄 Exported as CSV",
    },
    "kh": {
        "btn_analyze": "🔍 វិភាគ",
        "btn_sniper": "🎯 Sniper",
        "btn_history": "🕘 ប្រវត្តិ",
        "btn_settings": "⚙️ ការកំណត់",
        "btn_help": "❓ ជំនួយ",
        "btn_menu": "🏠 ម៉ឺនុយមេ",
        "btn_refresh": "🔄 ធ្វើឱ្យថ្មី",
        "btn_export": "📄 នាំចេញ",
        "btn_back": "◀ ត្រឡប់ក្រោយ",
        "lang_en": "🇬🇧 English",
        "lang_kh": "🇰🇭 ភាសាខ្មែរ",
        "btn_btcusdt": "₿ BTCUSDT",
        "btn_ethusdt": "Ξ ETHUSDT",
        "btn_solusdt": "◎ SOLUSDT",
        "btn_xauusd": "🥇 XAUUSD",
        "btn_all": "🔀 ទាំងអស់",
        "btn_memecoin": "🐸 Memecoin",
        "tf_1h": "1H", "tf_4h": "4H", "tf_1d": "1D", "tf_1w": "1W",
        "welcome_title": "សូមស្វាគមន៍មកកាន់ Bot វិភាគការជួញដូរ 👋",
        "welcome_body": (
            "ទទួលការវិភាគពហុភ្នាក់ងារតាមតម្រូវការសម្រាប់ <b>BTCUSDT</b>, "
            "<b>ETHUSDT</b>, <b>SOLUSDT</b> និង <b>XAUUSD</b>។\\n\\n"
            "ប្រើប៊ូតុងខាងក្រោម ឬវាយបញ្ជា៖\\n"
            "/analyze — ចាប់ផ្តើមការវិភាគថ្មី\\n"
            "/sniper — ស្កេនឱកាស memecoin (មានតែសញ្ញា)\\n"
            "/history — មើលរបាយការណ៍មុនៗ\\n"
            "/settings — ផ្លាស់ប្តូរភាសា និងចំណូលចិត្ត\\n"
            "/help — ជំនួយបន្ថែម\\n\\n"
            "<i>ការវិភាគគ្រាន់តែសម្រាប់ព័ត៌មាន មិនមែនជាដំបូន្មានហិរញ្ញវត្ថុទេ។</i>"
        ),
        "help_title": "ជំនួយ និងបញ្ជា",
        "help_body": (
            "/analyze — វិភាគ BTCUSDT, ETHUSDT, SOLUSDT ឬ XAUUSD (ឧ. <code>/analyze ETHUSDT 4h</code>)\\n"
            "/sniper — ស្កេន memecoin (មានតែសញ្ញា មិនដាក់ការបញ្ជាទិញ)\\n"
            "/history — បង្ហាញការវិភាគ 10 ចុងក្រោយ\\n"
            "/settings — ភាសា និងជម្រើសរបាយការណ៍\\n"
            "/about — ព័ត៌មានអំពី Bot\\n"
            "/cancel — បោះបង់សកម្មភាពបច្ចុប្បន្ន\\n\\n"
            "ពេលវេលា: <code>1h</code>, <code>4h</code>, <code>1d</code>, <code>1w</code>។\\n"
            "ដែនកំណត់ការវិភាគប្រចាំថ្ងៃ: {limit} ដង។"
        ),
        "about_text": (
            "🤖 <b>Trading Analysis Bot</b> v{version}\\n"
            "ការវិភាគពហុទ្រព្យសម្រាប់ BTCUSDT, ETHUSDT, SOLUSDT & XAUUSD ជាមួយ "
            "ភ្នាក់ងារឯកទេស 10 លើក្រុមបច្ចេកទេស ព័ត៌មានទីផ្សារ និងហានិភ័យ "
            "បូកនឹង memecoin sniper ដែលមានតែសញ្ញា។ របាយការណ៍អាចត្រូវបាន "
            "បង្កើនដោយ DeepSeek-V4-Flash។\\n\\n"
            "<i>មិនមែនជាដំបូន្មានហិរញ្ញវត្ថុទេ។</i>"
        ),
        "asset_prompt": "តើអ្នកចង់វិភាគទ្រព្យសកម្មមួយណា?",
        "tf_prompt": "ជ្រើសរើសពេលវេលាសម្រាប់ {symbol}៖",
        "analyzing": "⏳ កំពុងវិភាគ {symbol} {timeframe} — ចំណាយពេលប៉ុន្មានវិនាទី…",
        "rate_limited": "⛔ អ្នកឈានដល់ដែនកំណត់ {limit} ដងក្នុងមួយថ្ងៃហើយ។ វានឹងចាប់ផ្តើមឡើងវិញនៅពាក់កណ្តាលអធ្រាត្រ UTC។",
        "error_generic": "❌ មានបញ្ហាក្នុងការវិភាគ។ សូមព្យាយាមម្តងទៀត។",
        "cancel_done": "បានបោះបង់។ ប៉ះ Main Menu ដើម្បីបន្ត។",
        "history_title": "📂 ការវិភាគ {limit} ចុងក្រោយរបស់អ្នក",
        "history_empty": "អ្នកមិនទាន់មានការវិភាគទេ។ ប៉ះ <b>Analyze</b> ដើម្បីបង្កើតរបាយការណ៍ដំបូង។",
        "history_row": "#{row_id} · {symbol} {timeframe} · {signal}",
        "report_title": "របាយការណ៍វិភាគ {symbol}",
        "lbl_time": "ម៉ោង",
        "lbl_timeframe": "ពេលវេលា",
        "lbl_price": "តម្លៃបច្ចុប្បន្ន",
        "lbl_signal": "សញ្ញា",
        "lbl_score": "ពិន្ទុ",
        "lbl_confidence": "កម្រិតទំនុកចិត្ត",
        "lbl_source": "ទិន្នន័យ",
        "sec_consensus": "🤝 ការឯកភាពរបស់ភ្នាក់ងារ",
        "lbl_team_technical": "បច្ចេកទេស",
        "lbl_team_intel": "ព័ត៌មាន",
        "lbl_team_risk": "ហានិភ័យ",
        "lbl_team_sniper": "Sniper",
        "lbl_market_intel": "ព័ត៌មានទីផ្សារ",
        "sec_technical": "📈 សូចនាករបច្ចេកទេស",
        "sec_sentiment": "💬 អារម្មណ៍ទីផ្សារ",
        "sec_onchain": "⛓ ទិន្នន័យ On-Chain",
        "sec_macro": "🌐 ម៉ាក្រូ",
        "sec_risk": "🛡️ ការគ្រប់គ្រងហានិភ័យ",
        "sec_correlation": "🔗 ការជាប់ទាក់ទង",
        "sec_sniper": "🎯 ស្កេន Sniper",
        "sec_summary": "📝 សង្ខេប",
        "lbl_rsi": "RSI (14)",
        "lbl_macd": "MACD",
        "lbl_macd_signal": "MACD Signal",
        "lbl_ma50": "MA 50",
        "lbl_ma200": "MA 200",
        "lbl_support": "Support",
        "lbl_resistance": "Resistance",
        "lbl_volume": "បរិមាណ",
        "lbl_obv": "និន្នាការ OBV",
        "lbl_volatility": "ភាពប្រែប្រួល",
        "lbl_band_position": "ទីតាំង Band",
        "lbl_squeeze": "Band squeeze",
        "lbl_pattern": "លំនាំតម្លៃ",
        "lbl_breakout": "Breakout",
        "lbl_news": "ព័ត៌មាន",
        "lbl_fng": "Fear & Greed",
        "lbl_social": "Social Volume",
        "lbl_whale": "សកម្មភាព Whale",
        "lbl_netflow": "Exchange netflow",
        "lbl_active": "អាសយដ្ឋានសកម្ម",
        "lbl_mvrv": "MVRV",
        "lbl_sopr": "SOPR",
        "lbl_rate": "គោលនយោបាយអត្រា",
        "lbl_dxy": "DXY (ដុល្លារ)",
        "lbl_inflation": "អតិផរណា",
        "lbl_sl": "Stop Loss",
        "lbl_tp": "Take Profit",
        "lbl_pos": "ទំហំទីតាំង",
        "lbl_atr": "ATR (14)",
        "lbl_vol": "ភាពប្រែប្រួល",
        "lbl_corr": "ការជាប់ទាក់ទង (r)",
        "lbl_headlines": "ចំណងជើងព័ត៌មាន",
        "lbl_opportunity": "ឱកាស",
        "lbl_safety": "សុវត្ថិភាព",
        "lbl_liquidity": "សាច់ប្រាក់ងាយស្រួល",
        "lbl_hype": "Hype",
        "lbl_chain": "បណ្តាញ",
        "lbl_risk_flags": "ទង់ហានិភ័យ",
        "sniper_title": "🎯 ស្កេន Sniper",
        "sniper_empty": "មិនមានឱកាសណាឆ្លងកាត់តម្រងសុវត្ថិភាព និងសាច់ប្រាក់ទេ។",
        "sniper_disclaimer": "💡 <i>ការរកឃើញតែសញ្ញា — មិនដាក់ការបញ្ជាទិញណាមួយទេ។</i>",
        "ai_enhanced": "🤖 បង្កើនដោយ AI (DeepSeek-V4-Flash)",
        "demo_notice": "⚠️ <i>ទិន្នន័យស្មូត/ប៉ាន់ស្មាន: {sources} — កំណត់ API ផ្ទាល់ក្នុង .env</i>",
        "na": "n/a",
        "settings_title": "⚙️ ការកំណត់",
        "settings_lang": "ភាសា",
        "settings_chart": "រូបភាពតារាង",
        "settings_indicators": "ផ្នែកសូចនាករ",
        "settings_risk": "ផ្នែកហានិភ័យ",
        "settings_sentiment": "ផ្នែកអារម្មណ៍ទីផ្សារ",
        "value_on": "✅ បើក",
        "value_off": "⛔ បិទ",
        "exported": "📄 បាននាំចេញជា CSV",
    },
}


def _resolve(language: str | None) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language  # type: ignore[return-value]
    return DEFAULT_LANGUAGE


class I18n:
    """Scoped translator bound to one user language."""

    def __init__(self, language: str | None = None) -> None:
        self.language = _resolve(language)

    @property
    def is_khmer(self) -> bool:
        return self.language == "kh"

    def t(self, key: str, **kwargs: object) -> str:
        """Translate ``key`` for this language, formatting placeholders."""
        en = STRINGS[DEFAULT_LANGUAGE].get(key)
        template = STRINGS.get(self.language, {}).get(key, en)
        if template is None:
            return key  # dev aid: missing key shows itself in the UI
        return template.format(**kwargs) if kwargs else template