export default async function handler(req, res) {
  const cronSecret = process.env.CRON_SECRET || 'otoichi_cron_secret_key_change_me';
  const apiBase = (process.env.VITE_API_BASE_URL || 'https://otoichi.onrender.com/api/v1').replace(/\/+$/, '');

  try {
    const response = await fetch(`${apiBase}/newsletter/trigger-weekly`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Cron-Secret': cronSecret
      },
      body: JSON.stringify({})
    });
    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
}
