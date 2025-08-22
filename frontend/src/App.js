import React, { useState, createContext, useContext } from 'react';
import './App.css';

// --- Fake Auth Context (always logged in) ---
const AuthContext = createContext();

const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user] = useState({
    id: 1,
    username: "Aaditya",
    level: 1,
    total_xp: 0,
    current_streak: 0,
    badges: []
  });

  return (
    <AuthContext.Provider value={{ user }}>
      {children}
    </AuthContext.Provider>
  );
};

// --- Dashboard Component ---
const Dashboard = () => {
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState('dashboard');
  const [quests, setQuests] = useState([]);
  const [powerUps, setPowerUps] = useState([]);
  const [badGuys, setBadGuys] = useState([]);

  // Local XP tracker
  const [xp, setXp] = useState(0);

  // Add XP helper
  const gainXP = (amount) => {
    setXp(prev => prev + amount);
  };

  // --- Handlers ---
  const createQuest = (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const newQuest = {
      id: Date.now(),
      title: form.get("title"),
      description: form.get("description"),
      quest_type: form.get("quest_type"),
      deadline: form.get("deadline"),
      status: "Pending",
      xp_reward: form.get("quest_type") === "Epic" ? 50 : form.get("quest_type") === "Weekly" ? 25 : 10
    };
    setQuests([...quests, newQuest]);
    e.target.reset();
  };

  const completeQuest = (id) => {
    setQuests(quests.map(q => q.id === id ? { ...q, status: "Done" } : q));
    const quest = quests.find(q => q.id === id);
    if (quest) gainXP(quest.xp_reward);
  };

  const createPowerUp = (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const newPower = {
      id: Date.now(),
      title: form.get("title"),
      description: form.get("description"),
      xp_reward: 5
    };
    setPowerUps([...powerUps, newPower]);
    e.target.reset();
  };

  const usePowerUp = (id) => {
    const power = powerUps.find(p => p.id === id);
    if (power) gainXP(power.xp_reward);
  };

  const createBadGuy = (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const newBadGuy = {
      id: Date.now(),
      title: form.get("title"),
      description: form.get("description"),
      max_hp: parseInt(form.get("max_hp")),
      current_hp: parseInt(form.get("max_hp")),
      defeat_xp_reward: 20
    };
    setBadGuys([...badGuys, newBadGuy]);
    e.target.reset();
  };

  const attackBadGuy = (id) => {
    setBadGuys(badGuys.map(b => {
      if (b.id === id) {
        const newHP = b.current_hp - 20;
        if (newHP <= 0) {
          gainXP(b.defeat_xp_reward);
          return { ...b, current_hp: 0 };
        }
        return { ...b, current_hp: newHP };
      }
      return b;
    }));
  };

  // --- UI Tabs ---
  const renderDashboard = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl p-6 text-white">
        <h2 className="text-2xl font-bold">{user.username}</h2>
        <p className="text-purple-200">Level {user.level} Hero</p>
        <div className="mt-4 text-lg">Total XP: {xp}</div>
      </div>
    </div>
  );

  const renderQuests = () => (
    <div>
      <form onSubmit={createQuest} className="space-y-4 bg-white p-4 rounded-lg mb-6">
        <input name="title" placeholder="Quest title" required className="border px-3 py-2 w-full"/>
        <textarea name="description" placeholder="Description" required className="border px-3 py-2 w-full"/>
        <select name="quest_type" className="border px-3 py-2 w-full">
          <option value="Daily">Daily Quest (10 XP)</option>
          <option value="Weekly">Weekly Quest (25 XP)</option>
          <option value="Epic">Epic Quest (50 XP)</option>
        </select>
        <input type="datetime-local" name="deadline" className="border px-3 py-2 w-full"/>
        <button type="submit" className="bg-purple-600 text-white px-4 py-2 rounded">Add Quest</button>
      </form>

      {quests.map(q => (
        <div key={q.id} className="p-3 border rounded mb-2 flex justify-between">
          <div>
            <strong>{q.title}</strong> ({q.quest_type}) - {q.status}
            <div className="text-sm">{q.description}</div>
          </div>
          {q.status !== "Done" && (
            <button onClick={() => completeQuest(q.id)} className="bg-green-500 text-white px-2 py-1 rounded">
              Complete
            </button>
          )}
        </div>
      ))}
    </div>
  );

  const renderPowerUps = () => (
    <div>
      <form onSubmit={createPowerUp} className="space-y-4 bg-white p-4 rounded-lg mb-6">
        <input name="title" placeholder="Power-up title" required className="border px-3 py-2 w-full"/>
        <textarea name="description" placeholder="Description" required className="border px-3 py-2 w-full"/>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Add Power-Up</button>
      </form>

      {powerUps.map(p => (
        <div key={p.id} className="p-3 border rounded mb-2 flex justify-between">
          <div>
            <strong>{p.title}</strong> (+{p.xp_reward} XP)  
            <div className="text-sm">{p.description}</div>
          </div>
          <button onClick={() => usePowerUp(p.id)} className="bg-blue-500 text-white px-2 py-1 rounded">
            Use
          </button>
        </div>
      ))}
    </div>
  );

  const renderBadGuys = () => (
    <div>
      <form onSubmit={createBadGuy} className="space-y-4 bg-white p-4 rounded-lg mb-6">
        <input name="title" placeholder="Bad Guy Name" required className="border px-3 py-2 w-full"/>
        <textarea name="description" placeholder="Description" required className="border px-3 py-2 w-full"/>
        <input type="number" name="max_hp" defaultValue={100} min="10" className="border px-3 py-2 w-full"/>
        <button type="submit" className="bg-red-600 text-white px-4 py-2 rounded">Add Bad Guy</button>
      </form>

      {badGuys.map(b => (
        <div key={b.id} className="p-3 border rounded mb-2">
          <div className="flex justify-between mb-2">
            <strong>{b.title}</strong> ({b.current_hp}/{b.max_hp} HP)
            <button onClick={() => attackBadGuy(b.id)} className="bg-red-500 text-white px-2 py-1 rounded">
              Attack
            </button>
          </div>
          <div className="h-2 bg-gray-200 rounded">
            <div className="h-2 bg-red-600 rounded" style={{ width: `${(b.current_hp / b.max_hp) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-md border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">⚡ LevelUp Daily</h1>
        </div>
      </header>

      <nav className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 flex space-x-6">
          <button onClick={() => setActiveTab('dashboard')} className={`py-3 ${activeTab === 'dashboard' && "font-bold border-b-2 border-purple-500"}`}>Dashboard</button>
          <button onClick={() => setActiveTab('quests')} className={`py-3 ${activeTab === 'quests' && "font-bold border-b-2 border-purple-500"}`}>Quests</button>
          <button onClick={() => setActiveTab('powerups')} className={`py-3 ${activeTab === 'powerups' && "font-bold border-b-2 border-blue-500"}`}>Power-Ups</button>
          <button onClick={() => setActiveTab('badguys')} className={`py-3 ${activeTab === 'badguys' && "font-bold border-b-2 border-red-500"}`}>Bad Guys</button>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 py-6">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'quests' && renderQuests()}
        {activeTab === 'powerups' && renderPowerUps()}
        {activeTab === 'badguys' && renderBadGuys()}
      </main>
    </div>
  );
};

// --- App Root ---
function App() {
  return (
    <AuthProvider>
      <Dashboard />
    </AuthProvider>
  );
}

export default App;
