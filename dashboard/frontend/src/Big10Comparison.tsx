import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Big10Comparison.css';

const API_BASE = 'http://localhost:8000';

interface SchoolSeasonData {
  Date: string;
  CumulativeScore: number;
  Opponent: string;
  Result: string;
}

interface SchoolData {
  name: string;
  logo: string;
  color: string;
  data: SchoolSeasonData[];
  record: { wins: number; losses: number };
  latestScore: number;
}

// All schools including UCLA
const ALL_SCHOOLS = [
  { name: 'UCLA', color: '#2774AE', logo: '🐻', isUcla: true },
  { name: 'USC', color: '#990000', logo: '🔱', isUcla: false },
  { name: 'Ohio State', color: '#BB0000', logo: '🌰', isUcla: false },
  { name: 'Michigan', color: '#00274C', logo: 'M', isUcla: false },
  { name: 'Penn State', color: '#041E42', logo: 'PSU', isUcla: false },
  { name: 'Illinois', color: '#13294B', logo: 'ILL', isUcla: false },
  { name: 'Northwestern', color: '#4E2A84', logo: 'NU', isUcla: false },
  { name: 'Indiana', color: '#990000', logo: 'IU', isUcla: false },
  { name: 'Purdue', color: '#000000', logo: 'PU', isUcla: false },
  { name: 'Wisconsin', color: '#C5050C', logo: 'W', isUcla: false },
  { name: 'Nebraska', color: '#E41C38', logo: 'N', isUcla: false },
  { name: 'Michigan State', color: '#18453B', logo: 'MSU', isUcla: false },
];

const Big10Comparison: React.FC = () => {
  const [leftSchool, setLeftSchool] = useState<string>('UCLA');
  const [rightSchool, setRightSchool] = useState<string>('USC');
  const [leftData, setLeftData] = useState<SchoolData | null>(null);
  const [rightData, setRightData] = useState<SchoolData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedSeason, setSelectedSeason] = useState('2025-26');

  useEffect(() => {
    fetchComparisonData();
  }, [leftSchool, rightSchool, selectedSeason]);

  const fetchSchoolData = async (schoolName: string): Promise<SchoolData | null> => {
    try {
      const school = ALL_SCHOOLS.find(s => s.name === schoolName);
      if (!school) return null;

      let response;
      if (school.isUcla) {
        // Fetch UCLA data from the standard endpoint
        response = await axios.get(`${API_BASE}/seasons/${selectedSeason}`);
      } else {
        // Fetch other school data
        response = await axios.get(`${API_BASE}/schools/${schoolName}/seasons/${selectedSeason}`);
      }

      const gameData = response.data;
      const games = gameData.filter((d: SchoolSeasonData) => d.Result && d.Result.trim() !== '');
      const wins = games.filter((d: SchoolSeasonData) => d.Result.toUpperCase().startsWith('W')).length;
      const losses = games.filter((d: SchoolSeasonData) => d.Result.toUpperCase().startsWith('L')).length;
      const latestScore = gameData.length > 0 ? gameData[gameData.length - 1].CumulativeScore : 0;

      return {
        name: schoolName,
        logo: school.logo,
        color: school.color,
        data: gameData,
        record: { wins, losses },
        latestScore
      };
    } catch (error) {
      console.error(`Error fetching ${schoolName} data:`, error);
      return null;
    }
  };

  const fetchComparisonData = async () => {
    setLoading(true);
    
    try {
      const [left, right] = await Promise.all([
        fetchSchoolData(leftSchool),
        fetchSchoolData(rightSchool)
      ]);

      setLeftData(left);
      setRightData(right);
    } catch (error) {
      console.error('Error fetching comparison data:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderSchoolCard = (schoolData: SchoolData | null, side: 'left' | 'right') => {
    if (!schoolData) {
      return (
        <div className={`school-card ${side}`}>
          <div className="no-data-placeholder">
            <p>No data available</p>
          </div>
        </div>
      );
    }

    return (
      <div className={`school-card ${side}`} style={{ borderColor: schoolData.color }}>
        <div className="school-header" style={{ backgroundColor: schoolData.color }}>
          <div className="school-logo">{schoolData.logo}</div>
          <h3>{schoolData.name}</h3>
        </div>
        
        <div className="school-stats-summary">
          <div className="stat-box">
            <div className="stat-label">Record</div>
            <div className="stat-value">{schoolData.record.wins}-{schoolData.record.losses}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Score</div>
            <div className="stat-value" style={{ 
              color: schoolData.latestScore > 0 ? 'green' : schoolData.latestScore < 0 ? 'red' : '#333' 
            }}>
              {schoolData.latestScore > 0 ? '+' : ''}{schoolData.latestScore}
            </div>
          </div>
        </div>

        <div className="school-chart">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={schoolData.data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="Date" 
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="CumulativeScore" 
                stroke={schoolData.color}
                strokeWidth={3}
                connectNulls={false}
                dot={{ r: 4, fill: schoolData.color }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="recent-games">
          <h4>Recent Games</h4>
          <div className="games-list">
            {schoolData.data
              .filter(game => game.Result && game.Result.trim() !== '')
              .slice(-5)
              .reverse()
              .map((game, idx) => (
                <div key={idx} className="game-item">
                  <span className="game-date">{game.Date}</span>
                  <span className="game-opponent">{game.Opponent}</span>
                  <span className={`game-result ${game.Result.toUpperCase().startsWith('W') ? 'win' : 'loss'}`}>
                    {game.Result}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="big10-comparison-container">
      <div className="comparison-header">
        <h2 className="comparison-title">🏆 Big Ten Head-to-Head Comparison</h2>
        
        <div className="season-selector-top">
          <label>Season:</label>
          <select value={selectedSeason} onChange={(e) => setSelectedSeason(e.target.value)}>
            <option value="2025-26">2025-26</option>
            <option value="2024-25">2024-25</option>
            <option value="2023-24">2023-24</option>
            <option value="2022-23">2022-23</option>
            <option value="2021-22">2021-22</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner">Loading...</div>
        </div>
      ) : (
        <div className="comparison-layout">
          <div className="left-side">
            <div className="school-selector-box">
              <label>School 1:</label>
              <select 
                value={leftSchool} 
                onChange={(e) => setLeftSchool(e.target.value)}
                style={{ borderColor: ALL_SCHOOLS.find(s => s.name === leftSchool)?.color }}
              >
                {ALL_SCHOOLS.map(school => (
                  <option key={school.name} value={school.name}>
                    {school.name}
                  </option>
                ))}
              </select>
            </div>
            {renderSchoolCard(leftData, 'left')}
          </div>

          <div className="vs-divider">
            <div className="vs-circle">VS</div>
          </div>

          <div className="right-side">
            <div className="school-selector-box">
              <label>School 2:</label>
              <select 
                value={rightSchool} 
                onChange={(e) => setRightSchool(e.target.value)}
                style={{ borderColor: ALL_SCHOOLS.find(s => s.name === rightSchool)?.color }}
              >
                {ALL_SCHOOLS.map(school => (
                  <option key={school.name} value={school.name}>
                    {school.name}
                  </option>
                ))}
              </select>
            </div>
            {renderSchoolCard(rightData, 'right')}
          </div>
        </div>
      )}
    </div>
  );
};

export default Big10Comparison;