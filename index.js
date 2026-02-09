import express from "express";
import fetch from "node-fetch";
import cors from "cors";

const app = express();
app.use(cors());

app.get("/", async (req, res) => {
  const targetUrl = req.query.url;

  if (!targetUrl) {
    return res.status(400).json({ error: "Missing 'url' query parameter" });
  }

  try {
    const response = await fetch(targetUrl);
    const data = await response.text();

    res.set("Content-Type", "application/json");
    res.send(data);
  } catch (error) {
    res.status(500).json({ error: "Proxy request failed", details: error.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Proxy running on port ${PORT}`));
