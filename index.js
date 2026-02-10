import express from "express";
import fetch from "node-fetch";
import cors from "cors";

const app = express();
app.use(cors());

// Use /proxy instead of / to avoid Render stripping query params
app.get("/proxy", async (req, res) => {
  console.log("Incoming request:", req.query);

  const targetUrl = req.query.url;

  if (!targetUrl) {
    return res.status(400).json({ error: "Missing 'url' query parameter" });
  }

  try {
    // Force Ergast to return JSON instead of HTML
    const response = await fetch(targetUrl, {
  headers: {
    "Accept": "application/json, text/plain"
  }
});

    const data = await response.json();

    res.set("Content-Type", "application/json");
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
