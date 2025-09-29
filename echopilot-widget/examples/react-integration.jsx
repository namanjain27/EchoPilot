import React, { useEffect, useState } from 'react';

// EchoPilot Widget React Hook
const useEchoPilotWidget = (config) => {
  const [widgetLoaded, setWidgetLoaded] = useState(false);
  const [widget, setWidget] = useState(null);

  useEffect(() => {
    // Set global configuration
    window.echopilotSettings = config;

    // Load SDK script
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/@echopilot/widget/dist/sdk.js';
    script.async = true;

    script.onload = () => {
      if (window.echopilotSDK) {
        window.echopilotSDK.run({
          baseUrl: config.baseUrl,
          tenantId: config.tenantId
        });

        setWidget(window.$echopilot);
        setWidgetLoaded(true);
      }
    };

    document.head.appendChild(script);

    return () => {
      // Cleanup on unmount
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, [config]);

  return { widget, widgetLoaded };
};

// Main App Component
const App = () => {
  const [user, setUser] = useState(null);
  const [sessionActive, setSessionActive] = useState(false);

  const widgetConfig = {
    baseUrl: process.env.REACT_APP_ECHOPILOT_API || 'https://your-api.com',
    tenantId: process.env.REACT_APP_TENANT_ID || 'react-demo',
    position: 'right',
    launcherTitle: 'AI Assistant',
    welcomeTitle: 'Welcome!',
    welcomeDescription: 'How can I help you today?',
    widgetColor: '#3b82f6',
    enableFileUpload: true,
  };

  const { widget, widgetLoaded } = useEchoPilotWidget(widgetConfig);

  // Handle user login
  const handleLogin = (userData) => {
    setUser(userData);

    if (widget) {
      widget.setUser(userData.id, {
        name: userData.name,
        email: userData.email,
        avatar_url: userData.avatar
      });
    }
  };

  // Handle logout
  const handleLogout = () => {
    setUser(null);
    setSessionActive(false);

    if (widget) {
      widget.reset();
    }
  };

  // Toggle chat widget
  const toggleChat = () => {
    if (widget) {
      widget.toggle();
    }
  };

  // Start support session
  const startSupportSession = () => {
    if (widget) {
      widget.toggle('open');
      setSessionActive(true);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">
              EchoPilot React Demo
            </h1>

            <div className="flex items-center space-x-4">
              {user ? (
                <div className="flex items-center space-x-3">
                  <img
                    className="w-8 h-8 rounded-full"
                    src={user.avatar || `https://ui-avatars.com/api/?name=${user.name}`}
                    alt={user.name}
                  />
                  <span className="text-sm text-gray-700">
                    {user.name}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <LoginForm onLogin={handleLogin} />
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">
              Widget Integration Demo
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Widget Status */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">
                  Widget Status
                </h3>
                <p className="text-sm text-blue-700">
                  {widgetLoaded ? '✅ Loaded' : '⏳ Loading...'}
                </p>
              </div>

              {/* User Status */}
              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="font-medium text-green-900 mb-2">
                  User Status
                </h3>
                <p className="text-sm text-green-700">
                  {user ? `✅ Logged in as ${user.name}` : '❌ Not logged in'}
                </p>
              </div>

              {/* Session Status */}
              <div className="bg-purple-50 p-4 rounded-lg">
                <h3 className="font-medium text-purple-900 mb-2">
                  Support Session
                </h3>
                <p className="text-sm text-purple-700">
                  {sessionActive ? '✅ Active' : '❌ Inactive'}
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                onClick={toggleChat}
                disabled={!widgetLoaded}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
              >
                Toggle Chat
              </button>

              <button
                onClick={startSupportSession}
                disabled={!widgetLoaded || !user}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50"
              >
                Start Support Session
              </button>
            </div>

            {/* Configuration Display */}
            <div className="mt-6">
              <h3 className="font-medium mb-2">Current Configuration:</h3>
              <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                {JSON.stringify(widgetConfig, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

// Login Form Component
const LoginForm = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin({
      id: Date.now().toString(),
      ...formData
    });
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center space-x-2">
      <input
        type="text"
        name="name"
        placeholder="Name"
        value={formData.name}
        onChange={handleChange}
        required
        className="px-3 py-1 border rounded text-sm"
      />
      <input
        type="email"
        name="email"
        placeholder="Email"
        value={formData.email}
        onChange={handleChange}
        required
        className="px-3 py-1 border rounded text-sm"
      />
      <button
        type="submit"
        className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
      >
        Login
      </button>
    </form>
  );
};

export default App;