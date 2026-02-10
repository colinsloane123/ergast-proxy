import express from "express";
import fetch from "node-fetch";
import cors from "cors";

const app = express();
app.use(cors());

// Proxy endpoint
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

    let data;

    // Try to parse JSON directly
    try {
      data = await response.json();
    } catch {
      // If JSON parsing fails, fall back to text
      const text = await response.text();

      // Try to extract JSON from inside the text
      try {
        data = JSON.parse(text);
      } catch {
        // If still not JSON, return the raw HTML so we can debug
        return res.status(500).json({
          error: "Ergast did not return JSON",
          raw: text
        });
      }
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