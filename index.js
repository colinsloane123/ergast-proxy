import express from 'express';
import fetch from 'node-fetch';

const app = express();

app.get('/', async (req, res) => {
  const targetUrl = req.query.url;

  if (!targetUrl) {
    return res.status(400).send('Missing "url" query parameter.');
  }

  try {
    const response = await fetch(targetUrl, {
      headers: {
        'User-Agent': 'ergast-proxy/1.0 (https://yourdomain.com)'
      }
    });

    const contentType = response.headers.get('content-type') || 'text/plain';
    const body = await response.text();

    res.set('Content-Type', contentType);
    res.status(response.status).send(body);
  } catch (err) {
    console.error('Proxy error:', err);
    res.status(500).send(`Proxy error: ${err.message}`);
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Proxy listening on port ${PORT}`);
});