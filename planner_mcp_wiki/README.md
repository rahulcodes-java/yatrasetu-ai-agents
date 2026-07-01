# Wikipedia MCP Service

This is a lightweight external Wikipedia service that exposes Wikipedia summaries and URL links for key destinations.

## Architecture
- **Flask Server**: Runs on `http://localhost:5002`.
- **Wikipedia API wrapper**: Queries Wikipedia summary API (`/page/summary/{title}`) with fallback to search API (`/w/api.php`) for flexible matching.

## How to Run
From the root of the project:
```bash
python planner_mcp_wiki/server.py
```

## Example API Call
```bash
curl "http://localhost:5002/wiki?destination=Taj+Mahal"
```

## Example Response
```json
{
  "extract": "The Taj Mahal is an ivory-white marble mausoleum on the south bank of the Yamuna river in the Indian city of Agra...",
  "status": "success",
  "summary": "The Taj Mahal is an ivory-white marble mausoleum on the south bank of the Yamuna river in the Indian city of Agra...",
  "title": "Taj Mahal",
  "url": "https://en.wikipedia.org/wiki/Taj_Mahal"
}
```
