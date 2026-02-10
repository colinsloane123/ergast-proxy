import express from "express";
import fetch from "node-fetch";
import cors from "cors";

const app = express();
app.use(cors());

app.get("/proxy", async (req, res) => {
  console.log("Incoming request:", req.query);

  const targetUrl = req.query.url;

  if (!targetUrl) {
    return res.status(400).json({ error: "Missing 'url' query parameter" });
  }

  try {
    const response = await fetch(targetUrl, {
      headers: {
        "Accept": "application/json, text/plain"
      }
    });

    // Read the body ONCE
    const raw = await response.text();

    let data;

    // Try to parse JSON
    try {
      data = JSON.parse(raw);
    } catch {
      return res.status(500).json({
        error: "Ergast did not return JSON",
        raw: raw
      });
    }

    res.json(data);

  } catch (error) {
    res.status(500).json({
      error: "Proxy request failed",
      details: error.message
    });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Proxy running on port ${PORT}`));