import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './App.css';

const API_BASE = 'http://localhost:8000';

interface Player {
  Player: string;
  Singles_Wins: string;
  Singles_Losses: string;
  Doubles_Wins: string;
  Doubles_Losses: string;
}

interface Match {
  Date: string;
  Opponent: string;
  Location: string;
  Result: string;
  CumulativeScore?: number;
}

function App() {
  const [roster, setRoster] = useState<Player[]>([]);
  const [schedule, setSchedule] = useState<Match[]>([]);
  const [seasons, setSeasons] = useState<string[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<string>('');
  const [seasonData, setSeasonData] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedSeason) {
      fetchSeasonData(selectedSeason);
    }
  }, [selectedSeason]);

  const fetchData = async () => {
    try {
      const [rosterRes, scheduleRes, seasonsRes] = await Promise.all([
        axios.get(`${API_BASE}/roster`).catch(e => ({ data: [] })),
        axios.get(`${API_BASE}/schedule`).catch(e => ({ data: [] })),
        axios.get(`${API_BASE}/seasons`).catch(e => ({ data: [] }))
      ]);
      
      setRoster(rosterRes.data);
      setSchedule(scheduleRes.data);
      setSeasons(seasonsRes.data);
      if (seasonsRes.data.length > 0) {
        setSelectedSeason(seasonsRes.data[0]);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSeasonData = async (season: string) => {
    try {
      const res = await axios.get(`${API_BASE}/seasons/${season}`);
      setSeasonData(res.data);
    } catch (error) {
      console.error('Error fetching season data:', error);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎾 UCLA Men's Tennis Dashboard</h1>
      </header>

      <main className="main-content">
        <section className="roster-section">
          <h2>Team Roster</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Player</th>
                  <th>Singles W</th>
                  <th>Singles L</th>
                  <th>Doubles W</th>
                  <th>Doubles L</th>
                </tr>
              </thead>
              <tbody>
                {roster.map((player, idx) => (
                  <tr key={idx}>
                    <td>{player.Player}</td>
                    <td>{player.Singles_Wins}</td>
                    <td>{player.Singles_Losses}</td>
                    <td>{player.Doubles_Wins}</td>
                    <td>{player.Doubles_Losses}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="schedule-section">
          <h2>Current Schedule</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Opponent</th>
                  <th>Location</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {schedule.map((match, idx) => (
                  <tr key={idx}>
                    <td>{match.Date}</td>
                    <td>{match.Opponent}</td>
                    <td>{match.Location}</td>
                    <td>{match.Result}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="performance-section">
          <h2>Performance Graph</h2>
          <select 
            value={selectedSeason} 
            onChange={(e) => setSelectedSeason(e.target.value)}
            className="season-select"
          >
            {seasons.map(season => (
              <option key={season} value={season}>{season}</option>
            ))}
          </select>
          
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={seasonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="Date" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="CumulativeScore" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;