# Getting Started with EchoPilot Widget

This guide will help you integrate the EchoPilot AI chat widget into your website in just a few minutes.

## 🚀 Quick Setup (5 minutes)

### Step 1: Add the Script Tag

Add this script to your HTML before the closing `</body>` tag:

```html
<script>
  window.echopilotSettings = {
    baseUrl: 'https://your-echopilot-api.com',
    tenantId: 'your-tenant-id', // Optional
    position: 'right',
    launcherTitle: 'Chat with AI Assistant',
  };
</script>
<script src="https://cdn.jsdelivr.net/npm/@echopilot/widget/dist/sdk.js"></script>
```

### Step 2: Configure Your Settings

Replace the configuration values:
- `baseUrl`: Your EchoPilot API endpoint
- `tenantId`: Your tenant identifier (for multi-tenant setups)

### Step 3: Test It!

Open your website and you should see a chat bubble in the bottom-right corner. Click it to start chatting!

## 🛠️ Development Setup

If you want to customize the widget or contribute to development:

### Prerequisites
- Node.js 16+
- npm or pnpm

### Installation
```bash
git clone <this-repository>
cd echopilot-widget
npm install
```

### Development
```bash
# Start development server
npm run dev

# Build for production
npm run build
```

## 📋 Configuration Reference

### Basic Settings
```javascript
window.echopilotSettings = {
  baseUrl: 'https://your-api.com',     // Required: Your API endpoint
  tenantId: 'your-tenant',            // Optional: Multi-tenant support
  position: 'right',                   // 'left' or 'right'
  launcherTitle: 'Chat with Support',  // Bubble tooltip text
};
```

### Appearance
```javascript
window.echopilotSettings = {
  // ... basic settings
  widgetColor: '#1f93ff',              // Primary color
  darkMode: 'auto',                    // 'light', 'dark', 'auto'
  widgetStyle: 'standard',             // 'standard' or 'flat'
  hideMessageBubble: false,            // Hide the chat bubble
};
```

### Welcome Messages
```javascript
window.echopilotSettings = {
  // ... other settings
  welcomeTitle: 'Welcome!',
  welcomeDescription: 'How can I help you today?',
  availableMessage: 'We are online',
  unavailableMessage: 'We are offline',
};
```

### User Identification
```javascript
window.echopilotSettings = {
  // ... other settings
  user: {
    identifier: 'user@example.com',
    name: 'John Doe',
    email: 'user@example.com',
    avatar_url: 'https://example.com/avatar.jpg'
  }
};
```

## 🔧 JavaScript API

### Control the Widget
```javascript
// Open/close widget
window.$echopilot.toggle('open');
window.$echopilot.toggle('close');

// Set user information
window.$echopilot.setUser('user123', {
  name: 'John Doe',
  email: 'john@example.com'
});

// Set custom attributes
window.$echopilot.setCustomAttributes({
  plan: 'premium',
  department: 'engineering'
});

// Reset widget (clears conversation)
window.$echopilot.reset();
```

### Event Handling
```javascript
// Listen for widget events
window.addEventListener('chatwoot:ready', () => {
  console.log('Widget is ready');
});

window.addEventListener('chatwoot:opened', () => {
  console.log('Widget opened');
});

window.addEventListener('chatwoot:closed', () => {
  console.log('Widget closed');
});
```

## 🎨 Customization

### CSS Custom Properties
```css
:root {
  --echopilot-primary: #your-brand-color;
  --echopilot-background: #ffffff;
  --echopilot-text: #333333;
}
```

### Custom Styling
```css
/* Override bubble appearance */
.echopilot-widget-bubble {
  background: linear-gradient(45deg, #667eea, #764ba2) !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}

/* Custom widget container */
.echopilot-widget-container {
  border-radius: 12px !important;
}
```

## 🐛 Troubleshooting

### Widget Not Appearing
1. Check browser console for errors
2. Verify `baseUrl` is correct and accessible
3. Ensure script is loaded after DOM is ready

### API Connection Issues
1. Check CORS settings on your API server
2. Verify SSL certificate if using HTTPS
3. Check network tab for failed requests

### Styling Issues
1. Check for CSS conflicts with your site
2. Use browser dev tools to inspect widget elements
3. Add `!important` to custom CSS if needed

## 📚 Examples

Check the `/examples` folder for complete integration examples:

- `basic.html` - Simple HTML integration
- `react-integration.jsx` - React component example
- `vue-integration.vue` - Vue 3 composition API example

## 🆘 Support

- 📖 [Full Documentation](./README.md)
- 🐛 [Report Issues](https://github.com/your-repo/issues)
- 💬 [Community Chat](https://discord.gg/your-server)

## ✅ Next Steps

1. ✅ Basic integration working
2. 🔲 Customize appearance to match your brand
3. 🔲 Set up user identification
4. 🔲 Configure custom attributes
5. 🔲 Test file upload functionality
6. 🔲 Set up analytics/monitoring

Happy chatting! 🚀