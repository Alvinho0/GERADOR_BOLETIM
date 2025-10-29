class LoginSystem {
    constructor() {
      this.init()
    }

    init() {
      this.setupEventListeners()
    }

    setupEventListeners() {
      const form = document.getElementById('loginForm')
      const togglePassword = document.getElementById('togglePassword')
      const passwordInput = document.getElementById('password')

      form.addEventListener('submit', (e) => this.handleLogin(e))

      togglePassword.addEventListener('click', () => {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password'
        passwordInput.setAttribute('type', type)
        togglePassword.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>'
      })
    }

    async handleLogin(e) {
      e.preventDefault()

      const loginButton = document.getElementById('loginButton')
      const btnText = loginButton.querySelector('.btn-text')
      const btnLoading = loginButton.querySelector('.btn-loading')

      btnText.style.display = 'none'
      btnLoading.style.display = 'flex'
      loginButton.disabled = true

      const formData = {
        email: document.getElementById('email').value.trim(),
        password: document.getElementById('password').value,
        user_type: document.querySelector('input[name="userType"]:checked').value,
      }

      try {
        const endpoint = window.LOGIN_CONFIG?.loginEndpoint || '/api/auth/login'
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        })

        const data = await response.json()

        if (data.success) {
          this.showSuccess()
          const redirectTo = window.LOGIN_CONFIG?.successRedirect || '/sistema'
          setTimeout(() => {
            window.location.href = redirectTo
          }, 1200)
        } else {
          this.showError(data.message || 'Erro ao fazer login')
        }
      } catch (error) {
        console.error('Erro no login:', error)
        this.showError('Erro de conexão. Tente novamente.')
      } finally {
        this.resetButton(btnText, btnLoading, loginButton)
      }
    }

    showSuccess() {
      const modal = document.getElementById('successModal')
      if (modal) modal.style.display = 'flex'
    }

    showError(message) {
      let errorDiv = document.querySelector('.error-message')
      if (!errorDiv) {
        errorDiv = document.createElement('div')
        errorDiv.className = 'error-message'
        document.querySelector('.login-form').prepend(errorDiv)
      }

      errorDiv.innerHTML = `
        <div class="error-content">
          <i class="fas fa-exclamation-circle"></i>
          <span>${message}</span>
        </div>
      `

      errorDiv.style.display = 'block'
      setTimeout(() => {
        errorDiv.style.display = 'none'
      }, 5000)
    }

    resetButton(btnText, btnLoading, button) {
      btnText.style.display = 'block'
      btnLoading.style.display = 'none'
      button.disabled = false
    }
}

document.addEventListener('DOMContentLoaded', () => {
  new LoginSystem()
})


