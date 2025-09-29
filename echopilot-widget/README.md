# EchoPilot Widget

An embeddable AI chat widget for customer support, extracted and adapted from Chatwoot's open-source widget. Provides a complete chat interface with file upload capabilities for knowledge base integration.

## ✨ Features

- 🤖 **AI-Powered Chat** - Connect with your EchoPilot AI assistant
- 📁 **File Upload** - Upload documents to knowledge base during chat
- 🏢 **Multi-tenant Support** - Enterprise-ready with tenant isolation
- 📱 **Responsive Design** - Works on desktop and mobile
- 🎨 **Customizable** - Easy theming and branding options
- 🔒 **Session Management** - Persistent conversation sessions

## 🚀 Quick Start

### 1. Install

```bash
npm install @echopilot/widget
```

### 2. Basic Integration

Add the widget script to your HTML:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Your Website</title>
</head>
<body>
  <!-- Your website content -->

  <!-- EchoPilot Widget -->
  <script>
    window.echopilotSettings = {
      baseUrl: 'https://your-echopilot-api.com',
      tenantId: 'your-tenant-id', // Optional for multi-tenant
      position: 'right', // 'left' or 'right'
      launcherTitle: 'Chat with AI Assistant',
    };
  </script>
  <script src="https://cdn.jsdelivr.net/npm/@echopilot/widget/dist/sdk.js"></script>
</body>
</html>
```

### 3. Initialize

```javascript
window.echopilotSDK.run({
  baseUrl: 'https://your-echopilot-api.com',
  tenantId: 'your-tenant-id'
});
```

## 📖 Configuration Options

```javascript
window.echopilotSettings = {
  // Required
  baseUrl: 'https://your-echopilot-api.com',

  // Optional
  tenantId: 'your-tenant-id',
  position: 'right', // 'left' or 'right'
  launcherTitle: 'Chat with Support',
  welcomeTitle: 'Welcome!',
  welcomeDescription: 'How can I help you today?',

  // Appearance
  widgetColor: '#1f93ff',
  darkMode: 'auto', // 'light', 'dark', or 'auto'
  widgetStyle: 'standard', // 'standard' or 'flat'

  // Features
  enableFileUpload: true,
  enableEmojiPicker: true,
  hideMessageBubble: false,

  // User identification
  user: {
    identifier: 'user@example.com',
    name: 'John Doe',
    email: 'user@example.com',
    avatar_url: 'https://example.com/avatar.jpg'
  }
};
```

## 🔧 API Integration

The widget connects to your EchoPilot API endpoints:

### Chat Endpoints
- `POST /api/v1/chat` - Basic chat
- `POST /api/v1/chat-tenant` - Tenant-aware chat

### Knowledge Base
- `POST /api/v1/knowledge-base/upload-tenant` - File uploads

### Session Management
- `POST /api/v1/session/start` - Start session
- `POST /api/v1/session/end` - End session
- `GET /api/v1/session/history` - Get history

## 🎨 Customization

### Custom CSS
```css
/* Override widget colors */
:root {
  --echopilot-primary: #your-brand-color;
  --echopilot-background: #ffffff;
}

/* Custom bubble styling */
.echopilot-widget-bubble {
  background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
}
```

### JavaScript API
```javascript
// Show/hide widget
window.$echopilot.toggle('open');
window.$echopilot.toggle('close');

// Set user
window.$echopilot.setUser('user123', {
  name: 'John Doe',
  email: 'john@example.com'
});

// Set custom attributes
window.$echopilot.setCustomAttributes({
  plan: 'premium',
  department: 'engineering'
});
```

## 📁 File Structure

```
echopilot-widget/
├── build/              # Entry points
├── sdk/                # Website embedding SDK
├── widget/             # Vue.js chat application
│   ├── api/           # API integration
│   ├── components/    # Vue components
│   ├── store/         # Vuex state management
│   └── views/         # Page components
├── shared/            # Shared utilities
└── assets/            # Styles and images
```

## 🔨 Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Build SDK only
npm run build:sdk

# Lint code
npm run lint
```

## 📋 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built upon the excellent foundation of [Chatwoot](https://github.com/chatwoot/chatwoot)'s open-source widget system.