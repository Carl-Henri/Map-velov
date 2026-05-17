# Map-Vélov — Toulouse Bike-Sharing Interactive Map

A full-stack web application that displays real-time availability of **Vélo Toulouse** bike-sharing stations on an interactive map, with historical data visualization.

Developed as a team project for the **INF-TC3** course at **Centrale Lyon** (2023–2024).

## Features

- **Interactive map** — Leaflet.js map showing all Vélo Toulouse stations with real-time color-coded availability (green / yellow / red)
- **Station details** — click any station to see the current number of mechanical bikes, electric bikes, and available docking stands
- **Historical charts** — visualize usage trends over time for any combination of stations
- **Python backend** — lightweight server that fetches live data from the Toulouse open data API and serves it to the frontend

## Tech Stack

- **Backend** — Python (HTTP server)
- **Frontend** — HTML, CSS, JavaScript
- **Map** — Leaflet.js
- **Data** — Toulouse Métropole open data API, SQLite for historical records

## Team

Gegout Carl-Henri · Tribout Rémy · Gros Maxime · Cres Raphaël · Marois Viki

## Running Locally

```bash
python serveur.py
# Then open client/map-velov.html in your browser
```
