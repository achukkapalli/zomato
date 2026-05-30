#!/usr/bin/env python3
"""
Live FastAPI integration test script (Phase 6).
Starts the FastAPI server locally, performs health and recommendation queries,
and shuts down the server.
"""

from __future__ import annotations

import subprocess
import sys
sys.stdout.reconfigure(encoding="utf-8")
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    port = "8089"
    url = f"http://127.0.0.1:{port}"
    print(f"Starting FastAPI server on port {port}...")

    # Start the FastAPI server using the current Python interpreter
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--port",
        port,
        "--log-level",
        "warning",
    ]
    process = subprocess.Popen(cmd, cwd=str(ROOT))

    try:
        # Poll health endpoint to wait for startup
        print("Waiting for server to load the dataset and respond...")
        health_url = f"{url}/api/v1/health"
        success = False
        for _ in range(60):  # Wait up to 60 seconds
            try:
                res = requests.get(health_url, timeout=2.0)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("dataset_loaded") is True:
                        print("Server is fully loaded and ready!")
                        success = True
                        break
                    else:
                        print("Server is up but dataset is still loading...")
            except requests.RequestException:
                pass
            time.sleep(1.0)

        if not success:
            print("Error: FastAPI server failed to start or load the dataset within 60 seconds.")
            return 1

        # Test root endpoint
        print("\n--- Testing Root Endpoint ---")
        res = requests.get(f"{url}/", timeout=5.0)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.json()}")
        assert res.status_code == 200

        # Test health endpoint details
        print("\n--- Testing Health Endpoint ---")
        res = requests.get(health_url, timeout=5.0)
        print(f"Status: {res.status_code}")
        health_data = res.json()
        print(f"Response: {health_data}")
        assert res.status_code == 200
        assert health_data["status"] == "ok"
        assert health_data["dataset_loaded"] is True
        assert "restaurant_count" in health_data

        # Test recommendation endpoint with valid preferences
        print("\n--- Testing Recommendation Endpoint ---")
        reco_url = f"{url}/api/v1/recommendations"
        payload = {
            "location": "Banashankari",
            "budget": "medium",
            "cuisine": "North Indian",
            "min_rating": 4.0,
            "additional_preferences": "family-friendly",
        }
        print(f"Sending preferences: {payload}")
        res = requests.post(reco_url, json=payload, timeout=10.0)
        print(f"Status: {res.status_code}")
        reco_data = res.json()
        assert res.status_code == 200
        assert "items" in reco_data, f"Expected items in recommendations, got: {reco_data}"

        if "items" in reco_data:
            print(f"Success! Got {len(reco_data['items'])} recommendations.")
            print(f"Summary: {reco_data.get('summary')}")
            for item in reco_data["items"][:2]:
                r = item["restaurant"]
                print(f"  - [{item['rank']}] {r['name']} in {r['location']} | rating={r['rating']} | cost={r['estimated_cost']}")
                print(f"    AI Explanation: {item['explanation']}")
        else:
            print(f"Got empty filter result as expected for these parameters: {reco_data}")
            assert "suggestions" in reco_data

        # Test empty-state recommendations
        print("\n--- Testing Empty State (Tokyo) ---")
        payload = {
            "location": "Tokyo",
            "budget": "medium",
        }
        res = requests.post(reco_url, json=payload, timeout=5.0)
        print(f"Status: {res.status_code}")
        reco_data = res.json()
        assert res.status_code == 200
        assert "suggestions" in reco_data
        print(f"Empty state response keys: {list(reco_data.keys())}")
        print(f"Message: {reco_data.get('message')}")
        print(f"Suggestions: {reco_data.get('suggestions')}")

        print("\nAll live backend API integration tests passed successfully!")
        return 0

    except AssertionError as err:
        print(f"\nAssertion Error during test execution: {err}")
        return 1
    except Exception as exc:
        print(f"\nUnexpected error during test execution: {exc}")
        return 1
    finally:
        print("Shutting down FastAPI server...")
        process.terminate()
        process.wait()
        print("FastAPI server shut down successfully.")


if __name__ == "__main__":
    sys.exit(main())
