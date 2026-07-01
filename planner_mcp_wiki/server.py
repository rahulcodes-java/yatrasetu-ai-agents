# server.py - Flask HTTP server for Wikipedia MCP Service
import urllib.request
import urllib.parse
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

def fetch_wikipedia_summary(destination: str) -> dict:
    title = destination.strip()
    encoded_title = urllib.parse.quote(title.replace(' ', '_'))
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
    
    headers = {"User-Agent": "YatraSetuWikiMCP/1.0 (contact@yatrasetu.ai)"}
    
    try:
        req = urllib.request.Request(summary_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            extract = data.get("extract", "")
            return {
                "status": "success",
                "title": data.get("title", title),
                "summary": extract[:300],
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded_title}"),
                "extract": extract
            }
    except Exception:
        # Fallback: Search Wikipedia for the best matching page title
        try:
            search_query = urllib.parse.quote(title)
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_query}&format=json&utf8="
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                search_data = json.loads(response.read().decode('utf-8'))
                search_results = search_data.get("query", {}).get("search", [])
                if search_results:
                    best_title = search_results[0]["title"]
                    encoded_best_title = urllib.parse.quote(best_title.replace(' ', '_'))
                    best_summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_best_title}"
                    req2 = urllib.request.Request(best_summary_url, headers=headers)
                    with urllib.request.urlopen(req2, timeout=5) as response2:
                        data2 = json.loads(response2.read().decode('utf-8'))
                        extract2 = data2.get("extract", "")
                        return {
                            "status": "success",
                            "title": data2.get("title", best_title),
                            "summary": extract2[:300],
                            "url": data2.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded_best_title}"),
                            "extract": extract2
                        }
        except Exception:
            pass
            
        return {
            "status": "not_found",
            "message": f"Could not find Wikipedia summary for '{destination}'."
        }

@app.route("/wiki", methods=["GET"])
def wiki_route():
    destination = request.args.get("destination")
    if not destination:
        return jsonify({"error": "Missing required parameter 'destination'"}), 400
        
    result = fetch_wikipedia_summary(destination)
    return jsonify(result)

if __name__ == "__main__":
    print("Starting Wikipedia Service on http://localhost:5002 ...")
    app.run(host="localhost", port=5002, debug=False)
