import { defineRailway, project, service } from "railway/iac";

export default defineRailway(() => {
  const web = service("web", {
    source: {
      repository: "Sultanrayan/pkay-ai-analysis",
      branch: "main",
    },
    env: {
      PYTHON_VERSION: "3.12",
      START_COMMAND: "python webhook_server.py",
      TELEGRAM_BOT_TOKEN: process.env.TELEGRAM_BOT_TOKEN,
      TELEGRAM_WEBHOOK_URL: process.env.TELEGRAM_WEBHOOK_URL,
      WEBHOOK_SECRET: process.env.WEBHOOK_SECRET,
      WEBHOOK_HOST: "0.0.0.0",
      LOG_LEVEL: "INFO",
      USE_DEMO_DATA: "false",
      DEMO_FALLBACK: "true",
      DEFAULT_SYMBOL: "BTCUSD",
      DEFAULT_TIMEFRAME: "1h",
      MAX_DAILY_REQUESTS: "10",
    },
    addons: [
      service("Postgres"),
      service("Redis"),
    ],
  });

  const postgres = service("Postgres");
  const redis = service("Redis");

  return project("trading-bot-analysis", {
    resources: [web, postgres, redis],
  });
});
