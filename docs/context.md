# Project Context: AI-Powered Restaurant Recommendation System

## Overview

Build an **AI-powered restaurant recommendation service** inspired by **Zomato**. The system suggests restaurants from user preferences by combining **structured restaurant data** with a **Large Language Model (LLM)** to produce personalized, human-like recommendations.

## Objective

Design and implement an application that:

1. Accepts user preferences (location, budget, cuisine, ratings, and more)
2. Uses a real-world restaurant dataset
3. Uses an LLM to generate personalized, natural-language recommendations
4. Presents clear, useful results to the user

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face:  
  [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- Extract relevant fields, including:
  - Restaurant name
  - Location
  - Cuisine
  - Cost
  - Rating
  - Other applicable attributes from the dataset

### 2. User Input

Collect user preferences:

| Preference | Examples / Notes |
|------------|------------------|
| **Location** | Delhi, Bangalore, etc. |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese, etc. |
| **Minimum rating** | Numeric threshold |
| **Additional** | family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter and prepare restaurant records that match user input
- Pass structured, filtered results into an LLM prompt
- Design prompts so the LLM can **reason** and **rank** options effectively

### 4. Recommendation Engine

Use the LLM to:

- **Rank** restaurants by fit for the user
- **Explain** why each recommendation matches the preferences
- **Optionally summarize** the overall set of choices

### 5. Output Display

Present top recommendations in a user-friendly format. Each result should include:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation (why it was recommended)

## Technical Scope Summary

| Layer | Responsibility |
|-------|----------------|
| **Data** | Hugging Face Zomato dataset → load, clean, field extraction |
| **Input** | Preference collection (location, budget, cuisine, rating, extras) |
| **Filter** | Structured filtering before LLM |
| **LLM** | Ranking, explanations, optional summary |
| **UI / Output** | Readable list of top picks with metadata and explanations |

## Success Criteria

- Recommendations reflect stated user preferences (location, budget, cuisine, rating).
- Results are grounded in real dataset records, not invented restaurants.
- LLM output is actionable: ranked list with clear, per-restaurant reasoning.
- End-to-end flow works: ingest → input → filter → LLM → display.

## Reference

- **Source problem statement:** `docs/problemStatement.txt`
- **Dataset:** https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation
