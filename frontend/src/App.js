import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // You could validate the token here by calling a user endpoint
    }
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { token: newToken, user: userData } = response.data;
      
      setToken(newToken);
      setUser(userData);
      localStorage.setItem('token', newToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const register = async (email, username, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`, { email, username, password });
      const { token: newToken, user: userData } = response.data;
      
      setToken(newToken);
      setUser(userData);
      localStorage.setItem('token', newToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      return true;
    } catch (error) {
      console.error('Registration error:', error);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login/Register Component
const AuthForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    let success;
    if (isLogin) {
      success = await login(email, password);
    } else {
      success = await register(email, username, password);
    }
    
    if (!success) {
      setError(isLogin ? 'Invalid credentials' : 'Registration failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-white/20">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">⚡ LevelUp Daily</h1>
          <p className="text-gray-300">Your personal growth adventure</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />
          </div>
          
          {!isLogin && (
            <div>
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
                required
              />
            </div>
          )}
          
          <div>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />
          </div>
          
          {error && (
            <div className="text-red-400 text-sm text-center">{error}</div>
          )}
          
          <button
            type="submit"
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition duration-200"
          >
            {isLogin ? 'Login' : 'Sign Up'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-purple-300 hover:text-purple-200 transition duration-200"
          >
            {isLogin ? 'Need an account? Sign up' : 'Already have an account? Login'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [quests, setQuests] = useState([]);
  const [powerUps, setPowerUps] = useState([]);
  const [badGuys, setBadGuys] = useState([]);

  // Quest Form States
  const [questForm, setQuestForm] = useState({
    title: '',
    description: '',
    quest_type: 'Daily',
    deadline: ''
  });

  // Power-up Form States
  const [powerUpForm, setPowerUpForm] = useState({
    title: '',
    description: ''
  });

  // Bad Guy Form States
  const [badGuyForm, setBadGuyForm] = useState({
    title: '',
    description: '',
    max_hp: 100
  });

  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchDashboard();
    } else if (activeTab === 'quests') {
      fetchQuests();
    } else if (activeTab === 'powerups') {
      fetchPowerUps();
    } else if (activeTab === 'badguys') {
      fetchBadGuys();
    }
  }, [activeTab]);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    }
  };

  const fetchQuests = async () => {
    try {
      const response = await axios.get(`${API}/quests`);
      setQuests(response.data);
    } catch (error) {
      console.error('Error fetching quests:', error);
    }
  };

  const fetchPowerUps = async () => {
    try {
      const response = await axios.get(`${API}/power-ups`);
      setPowerUps(response.data);
    } catch (error) {
      console.error('Error fetching power-ups:', error);
    }
  };

  const fetchBadGuys = async () => {
    try {
      const response = await axios.get(`${API}/bad-guys`);
      setBadGuys(response.data);
    } catch (error) {
      console.error('Error fetching bad guys:', error);
    }
  };

  const createQuest = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/quests`, questForm);
      setQuestForm({ title: '', description: '', quest_type: 'Daily', deadline: '' });
      fetchQuests();
    } catch (error) {
      console.error('Error creating quest:', error);
    }
  };

  const completeQuest = async (questId) => {
    try {
      const response = await axios.put(`${API}/quests/${questId}/complete`);
      alert(`${response.data.message} +${response.data.xp_gained} XP`);
      fetchQuests();
      fetchDashboard();
    } catch (error) {
      console.error('Error completing quest:', error);
    }
  };

  const createPowerUp = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/power-ups`, powerUpForm);
      setPowerUpForm({ title: '', description: '' });
      fetchPowerUps();
    } catch (error) {
      console.error('Error creating power-up:', error);
    }
  };

  const logPowerUp = async (powerUpId) => {
    try {
      const response = await axios.post(`${API}/power-ups/${powerUpId}/log`);
      alert(`${response.data.message} +${response.data.xp_gained} XP`);
      fetchDashboard();
    } catch (error) {
      console.error('Error logging power-up:', error);
    }
  };

  const createBadGuy = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/bad-guys`, badGuyForm);
      setBadGuyForm({ title: '', description: '', max_hp: 100 });
      fetchBadGuys();
    } catch (error) {
      console.error('Error creating bad guy:', error);
    }
  };

  const defeatBadGuy = async (badGuyId) => {
    try {
      const response = await axios.post(`${API}/bad-guys/${badGuyId}/defeat`);
      alert(`${response.data.message} +${response.data.xp_gained} XP`);
      fetchBadGuys();
      fetchDashboard();
    } catch (error) {
      console.error('Error defeating bad guy:', error);
    }
  };

  const completeSideQuest = async () => {
    try {
      const response = await axios.post(`${API}/side-quests/complete`);
      alert(`${response.data.message} +${response.data.xp_gained} XP`);
      fetchDashboard();
    } catch (error) {
      console.error('Error completing side quest:', error);
    }
  };

  const getProgressPercentage = () => {
    if (!user) return 0;
    const currentLevelXP = user.total_xp % 100;
    return (currentLevelXP / 100) * 100;
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* User Stats */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">{user?.username}</h2>
            <p className="text-purple-200">Level {user?.level} Hero</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{user?.total_xp} XP</div>
            <div className="text-sm text-purple-200">{user?.current_streak} day streak 🔥</div>
          </div>
        </div>
        
        {/* XP Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span>Progress to Level {(user?.level || 1) + 1}</span>
            <span>{user?.total_xp % 100}/100 XP</span>
          </div>
          <div className="w-full bg-white/20 rounded-full h-3">
            <div 
              className="bg-white rounded-full h-3 transition-all duration-500"
              style={{ width: `${getProgressPercentage()}%` }}
            ></div>
          </div>
        </div>
        
        {/* Daily Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold">{dashboardData?.quests_completed_today || 0}</div>
            <div className="text-sm text-purple-200">Quests Today</div>
          </div>
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold">{user?.badges?.length || 0}</div>
            <div className="text-sm text-purple-200">Badges Earned</div>
          </div>
        </div>
      </div>

      {/* Daily Side Quest */}
      {dashboardData?.daily_side_quest && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-bold text-yellow-800 mb-2">⭐ Today's Side Quest</h3>
          <p className="text-yellow-700 mb-2">{dashboardData.daily_side_quest.title}</p>
          <p className="text-sm text-yellow-600 mb-3">{dashboardData.daily_side_quest.description}</p>
          <button
            onClick={completeSideQuest}
            className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
          >
            Complete (+{dashboardData.daily_side_quest.xp_reward} XP)
          </button>
        </div>
      )}

      {/* Recent Badges */}
      {user?.badges?.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold mb-3">🏆 Your Badges</h3>
          <div className="flex flex-wrap gap-2">
            {user.badges.map((badge, index) => (
              <span key={index} className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                {badge}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderQuests = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold mb-4">Create New Quest</h3>
        <form onSubmit={createQuest} className="space-y-4">
          <input
            type="text"
            placeholder="Quest title"
            value={questForm.title}
            onChange={(e) => setQuestForm({...questForm, title: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            required
          />
          <textarea
            placeholder="Quest description"
            value={questForm.description}
            onChange={(e) => setQuestForm({...questForm, description: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            rows="3"
            required
          />
          <select
            value={questForm.quest_type}
            onChange={(e) => setQuestForm({...questForm, quest_type: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="Daily">Daily Quest (10 XP)</option>
            <option value="Weekly">Weekly Quest (25 XP)</option>
            <option value="Epic">Epic Quest (50 XP)</option>
          </select>
          <input
            type="datetime-local"
            value={questForm.deadline}
            onChange={(e) => setQuestForm({...questForm, deadline: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <button
            type="submit"
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md font-medium transition duration-200"
          >
            Create Quest
          </button>
        </form>
      </div>

      <div className="space-y-4">
        {quests.map(quest => (
          <div key={quest.id} className={`rounded-lg p-4 border ${quest.status === 'Done' ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'}`}>
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="font-bold">{quest.title}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    quest.quest_type === 'Epic' ? 'bg-red-100 text-red-800' :
                    quest.quest_type === 'Weekly' ? 'bg-blue-100 text-blue-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {quest.quest_type}
                  </span>
                  <span className="text-sm text-gray-500">+{quest.xp_reward} XP</span>
                </div>
                <p className="text-gray-600 text-sm">{quest.description}</p>
                {quest.deadline && (
                  <p className="text-xs text-gray-500 mt-1">
                    Due: {new Date(quest.deadline).toLocaleDateString()}
                  </p>
                )}
              </div>
              {quest.status !== 'Done' && (
                <button
                  onClick={() => completeQuest(quest.id)}
                  className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm font-medium transition duration-200"
                >
                  Complete
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderPowerUps = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold mb-4">Create Power-Up</h3>
        <form onSubmit={createPowerUp} className="space-y-4">
          <input
            type="text"
            placeholder="Power-up title (e.g., Drink Water)"
            value={powerUpForm.title}
            onChange={(e) => setPowerUpForm({...powerUpForm, title: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <textarea
            placeholder="Power-up description"
            value={powerUpForm.description}
            onChange={(e) => setPowerUpForm({...powerUpForm, description: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="2"
            required
          />
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition duration-200"
          >
            Create Power-Up
          </button>
        </form>
      </div>

      <div className="grid gap-4">
        {powerUps.map(powerUp => (
          <div key={powerUp.id} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-blue-800">{powerUp.title}</h4>
                <p className="text-blue-600 text-sm">{powerUp.description}</p>
                <span className="text-xs text-blue-500">+{powerUp.xp_reward} XP</span>
              </div>
              <button
                onClick={() => logPowerUp(powerUp.id)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition duration-200"
              >
                ⚡ Use
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderBadGuys = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold mb-4">Create Bad Guy</h3>
        <form onSubmit={createBadGuy} className="space-y-4">
          <input
            type="text"
            placeholder="Bad guy name (e.g., Procrastination)"
            value={badGuyForm.title}
            onChange={(e) => setBadGuyForm({...badGuyForm, title: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
            required
          />
          <textarea
            placeholder="Bad guy description"
            value={badGuyForm.description}
            onChange={(e) => setBadGuyForm({...badGuyForm, description: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
            rows="2"
            required
          />
          <input
            type="number"
            placeholder="Max HP"
            value={badGuyForm.max_hp}
            onChange={(e) => setBadGuyForm({...badGuyForm, max_hp: parseInt(e.target.value)})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
            min="10"
            max="500"
            required
          />
          <button
            type="submit"
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium transition duration-200"
          >
            Create Bad Guy
          </button>
        </form>
      </div>

      <div className="grid gap-4">
        {badGuys.map(badGuy => (
          <div key={badGuy.id} className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="font-bold text-red-800">{badGuy.title}</h4>
                <p className="text-red-600 text-sm">{badGuy.description}</p>
                <span className="text-xs text-red-500">+{badGuy.defeat_xp_reward} XP per defeat</span>
              </div>
              <button
                onClick={() => defeatBadGuy(badGuy.id)}
                className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium transition duration-200"
              >
                ⚔️ Attack
              </button>
            </div>
            
            {/* HP Bar */}
            <div className="mb-2">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-red-700">HP</span>
                <span className="text-red-700">{badGuy.current_hp}/{badGuy.max_hp}</span>
              </div>
              <div className="w-full bg-red-200 rounded-full h-2">
                <div 
                  className="bg-red-600 rounded-full h-2 transition-all duration-300"
                  style={{ width: `${(badGuy.current_hp / badGuy.max_hp) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-md border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">⚡ LevelUp Daily</h1>
          <button
            onClick={logout}
            className="text-red-600 hover:text-red-700 font-medium transition duration-200"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex space-x-8">
            {[
              { id: 'dashboard', label: '🏠 Dashboard', color: 'purple' },
              { id: 'quests', label: '⚔️ Quests', color: 'purple' },
              { id: 'powerups', label: '⚡ Power-Ups', color: 'blue' },
              { id: 'badguys', label: '👹 Bad Guys', color: 'red' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition duration-200 ${
                  activeTab === tab.id
                    ? `border-${tab.color}-500 text-${tab.color}-600`
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'quests' && renderQuests()}
        {activeTab === 'powerups' && renderPowerUps()}
        {activeTab === 'badguys' && renderBadGuys()}
      </main>
    </div>
  );
};

// Main App Component
function App() {
  const { token } = useAuth();
  
  if (!token) {
    return <AuthForm />;
  }

  return <Dashboard />;
}

// App with Auth Provider
function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWithAuth;