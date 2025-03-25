/**
 * ThemeToggle.js
 * Handles dark/light theme toggling functionality
 */

class ThemeToggle {
  constructor(options = {}) {
    this.options = {
      storageKey: 'mobilize-theme-preference',
      themeClass: 'dark-theme',
      transitionClass: 'theme-transition',
      transitionDuration: 500,
      autoDetect: true,
      ...options
    };
    
    this.isInitialized = false;
    this.toggleElements = [];
    this.currentTheme = null;
    
    this.init();
  }
  
  init() {
    // Only initialize once
    if (this.isInitialized) return;
    
    // Add transition class to smooth theme changes
    document.documentElement.classList.add(this.options.transitionClass);
    document.body.classList.add(this.options.transitionClass);
    
    // Check for stored preference
    const storedTheme = localStorage.getItem(this.options.storageKey);
    
    if (storedTheme) {
      // Apply stored theme
      this.setTheme(storedTheme);
    } else if (this.options.autoDetect) {
      // Check for system preference if no stored preference exists
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        this.setTheme('dark');
      } else {
        this.setTheme('light');
      }
      
      // Listen for system preference changes
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem(this.options.storageKey)) {
          this.setTheme(e.matches ? 'dark' : 'light', false);
        }
      });
    } else {
      // Default to light theme if no preference found and autoDetect is disabled
      this.setTheme('light');
    }
    
    // Find all theme toggle controls
    this.findToggleElements();
    
    // Listen for toggle button clicks
    document.addEventListener('click', (event) => {
      const toggleElement = event.target.closest('.theme-toggle');
      if (toggleElement) {
        this.toggleTheme();
      }
    });
    
    // Mark as initialized
    this.isInitialized = true;
    
    // Dispatch event when theme is initialized
    document.dispatchEvent(new CustomEvent('mobilize:theme-initialized', {
      detail: { theme: this.currentTheme }
    }));
  }
  
  findToggleElements() {
    // Find all toggle elements in the DOM
    this.toggleElements = document.querySelectorAll('.theme-toggle');
    
    // Apply ARIA attributes
    this.toggleElements.forEach(toggle => {
      toggle.setAttribute('role', 'switch');
      toggle.setAttribute('aria-checked', this.currentTheme === 'dark' ? 'true' : 'false');
      toggle.setAttribute('aria-label', 'Toggle dark mode');
      toggle.setAttribute('tabindex', '0');
      
      // Add keyboard support
      toggle.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.toggleTheme();
        }
      });
    });
  }
  
  setTheme(theme, savePreference = true) {
    // Validate theme
    if (theme !== 'dark' && theme !== 'light') {
      console.error('Invalid theme specified. Use "dark" or "light".');
      return;
    }
    
    // Update current theme
    this.currentTheme = theme;
    
    // Apply theme to body
    if (theme === 'dark') {
      document.body.classList.add(this.options.themeClass);
      document.body.classList.add('dark-mode-transition');
      document.body.classList.remove('light-mode-transition');
    } else {
      document.body.classList.remove(this.options.themeClass);
      document.body.classList.add('light-mode-transition');
      document.body.classList.remove('dark-mode-transition');
    }
    
    // Update all toggle controls
    this.toggleElements.forEach(toggle => {
      toggle.setAttribute('aria-checked', theme === 'dark' ? 'true' : 'false');
    });
    
    // Save preference
    if (savePreference) {
      localStorage.setItem(this.options.storageKey, theme);
    }
    
    // Dispatch theme change event
    document.dispatchEvent(new CustomEvent('mobilize:theme-changed', {
      detail: { theme }
    }));
  }
  
  toggleTheme() {
    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
  }
  
  // Helper to get current theme
  getTheme() {
    return this.currentTheme;
  }
  
  // Helper to check if dark theme is active
  isDarkTheme() {
    return this.currentTheme === 'dark';
  }
}

// Create an instance and export
const themeToggle = new ThemeToggle();

export default themeToggle; 