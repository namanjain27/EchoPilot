<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <h1 class="text-3xl font-bold text-gray-900">
            EchoPilot Vue Demo
          </h1>

          <div class="flex items-center space-x-4">
            <div v-if="user" class="flex items-center space-x-3">
              <img
                :src="user.avatar || `https://ui-avatars.com/api/?name=${user.name}`"
                :alt="user.name"
                class="w-8 h-8 rounded-full"
              />
              <span class="text-sm text-gray-700">{{ user.name }}</span>
              <button
                @click="handleLogout"
                class="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>

            <div v-else class="flex items-center space-x-2">
              <input
                v-model="loginForm.name"
                type="text"
                placeholder="Name"
                required
                class="px-3 py-1 border rounded text-sm"
              />
              <input
                v-model="loginForm.email"
                type="email"
                placeholder="Email"
                required
                class="px-3 py-1 border rounded text-sm"
              />
              <button
                @click="handleLogin"
                class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
              >
                Login
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="px-4 py-6 sm:px-0">
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-4">
            Widget Integration Demo
          </h2>

          <!-- Status Cards -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div class="bg-blue-50 p-4 rounded-lg">
              <h3 class="font-medium text-blue-900 mb-2">Widget Status</h3>
              <p class="text-sm text-blue-700">
                {{ widgetLoaded ? '✅ Loaded' : '⏳ Loading...' }}
              </p>
            </div>

            <div class="bg-green-50 p-4 rounded-lg">
              <h3 class="font-medium text-green-900 mb-2">User Status</h3>
              <p class="text-sm text-green-700">
                {{ user ? `✅ Logged in as ${user.name}` : '❌ Not logged in' }}
              </p>
            </div>

            <div class="bg-purple-50 p-4 rounded-lg">
              <h3 class="font-medium text-purple-900 mb-2">Session</h3>
              <p class="text-sm text-purple-700">
                {{ sessionActive ? '✅ Active' : '❌ Inactive' }}
              </p>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex flex-wrap gap-3 mb-6">
            <button
              @click="toggleChat"
              :disabled="!widgetLoaded"
              class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
            >
              Toggle Chat
            </button>

            <button
              @click="startSupportSession"
              :disabled="!widgetLoaded || !user"
              class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50"
            >
              Start Support Session
            </button>

            <button
              @click="setCustomAttributes"
              :disabled="!widgetLoaded"
              class="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 disabled:opacity-50"
            >
              Set Custom Attributes
            </button>
          </div>

          <!-- Widget API Examples -->
          <div class="bg-gray-50 p-4 rounded-lg">
            <h3 class="font-medium mb-3">Widget API Methods</h3>
            <div class="space-y-2 text-sm">
              <div>
                <code class="bg-white px-2 py-1 rounded">window.$echopilot.toggle('open')</code> - Open chat widget
              </div>
              <div>
                <code class="bg-white px-2 py-1 rounded">window.$echopilot.setUser(id, userData)</code> - Set user information
              </div>
              <div>
                <code class="bg-white px-2 py-1 rounded">window.$echopilot.setCustomAttributes(attrs)</code> - Set custom attributes
              </div>
              <div>
                <code class="bg-white px-2 py-1 rounded">window.$echopilot.reset()</code> - Reset widget state
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, onMounted, reactive } from 'vue'

export default {
  name: 'EchoPilotDemo',
  setup() {
    // Reactive state
    const widgetLoaded = ref(false)
    const user = ref(null)
    const sessionActive = ref(false)
    const widget = ref(null)

    const loginForm = reactive({
      name: '',
      email: ''
    })

    // Widget configuration
    const widgetConfig = {
      baseUrl: process.env.VUE_APP_ECHOPILOT_API || 'https://your-api.com',
      tenantId: process.env.VUE_APP_TENANT_ID || 'vue-demo',
      position: 'right',
      launcherTitle: 'AI Assistant',
      welcomeTitle: 'Welcome to Vue Demo!',
      welcomeDescription: 'How can I help you today?',
      widgetColor: '#10b981',
      enableFileUpload: true,
      enableEmojiPicker: true,
    }

    // Load EchoPilot Widget
    const loadWidget = async () => {
      try {
        // Set global configuration
        window.echopilotSettings = widgetConfig

        // Load SDK script
        const script = document.createElement('script')
        script.src = 'https://cdn.jsdelivr.net/npm/@echopilot/widget/dist/sdk.js'
        script.async = true

        script.onload = () => {
          if (window.echopilotSDK) {
            window.echopilotSDK.run({
              baseUrl: widgetConfig.baseUrl,
              tenantId: widgetConfig.tenantId
            })

            widget.value = window.$echopilot
            widgetLoaded.value = true

            console.log('✅ EchoPilot widget loaded successfully')
          }
        }

        script.onerror = () => {
          console.error('❌ Failed to load EchoPilot widget')
        }

        document.head.appendChild(script)
      } catch (error) {
        console.error('Error loading widget:', error)
      }
    }

    // Handle user login
    const handleLogin = () => {
      if (!loginForm.name || !loginForm.email) return

      const userData = {
        id: Date.now().toString(),
        name: loginForm.name,
        email: loginForm.email,
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(loginForm.name)}`
      }

      user.value = userData

      // Set user in widget if loaded
      if (widget.value) {
        widget.value.setUser(userData.id, {
          name: userData.name,
          email: userData.email,
          avatar_url: userData.avatar
        })
      }

      // Clear form
      loginForm.name = ''
      loginForm.email = ''
    }

    // Handle logout
    const handleLogout = () => {
      user.value = null
      sessionActive.value = false

      if (widget.value) {
        widget.value.reset()
      }
    }

    // Toggle chat widget
    const toggleChat = () => {
      if (widget.value) {
        widget.value.toggle()
      }
    }

    // Start support session
    const startSupportSession = () => {
      if (widget.value) {
        widget.value.toggle('open')
        sessionActive.value = true
      }
    }

    // Set custom attributes example
    const setCustomAttributes = () => {
      if (widget.value) {
        widget.value.setCustomAttributes({
          plan: 'premium',
          source: 'vue-demo',
          timestamp: new Date().toISOString()
        })

        alert('Custom attributes set! Check the network tab to see them sent with chat messages.')
      }
    }

    // Lifecycle
    onMounted(() => {
      loadWidget()
    })

    return {
      // State
      widgetLoaded,
      user,
      sessionActive,
      loginForm,

      // Methods
      handleLogin,
      handleLogout,
      toggleChat,
      startSupportSession,
      setCustomAttributes
    }
  }
}
</script>

<style scoped>
/* Add Tailwind CSS classes or custom styles here */
</style>