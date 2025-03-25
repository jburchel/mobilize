/**
 * LazyLoad.js
 * Handles lazy loading of images and components for performance optimization
 */

class LazyLoad {
  constructor(options = {}) {
    this.options = {
      rootMargin: '0px 0px 200px 0px', // Load images 200px before they enter viewport
      threshold: 0.1,
      loadingClass: 'loading',
      loadedClass: 'loaded',
      ...options
    };
    
    this.observer = null;
    this.init();
  }
  
  init() {
    // Check if IntersectionObserver is supported
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(this.onIntersection.bind(this), {
        rootMargin: this.options.rootMargin,
        threshold: this.options.threshold
      });
      
      // Start observing elements
      this.observeElements();
    } else {
      // Fallback for browsers that don't support IntersectionObserver
      this.loadAllElements();
    }
    
    // Set up event listener for dynamic content
    document.addEventListener('DOMContentLoaded', () => this.observeElements());
    document.addEventListener('mobilize:content-loaded', () => this.observeElements());
  }
  
  observeElements() {
    // Find all lazy-load images
    const images = document.querySelectorAll('img.lazy-image:not(.loaded)');
    images.forEach(img => {
      // Add loading class
      img.classList.add(this.options.loadingClass);
      
      // Start observing
      this.observer?.observe(img);
    });
    
    // Find all elements with background images
    const bgElements = document.querySelectorAll('[data-background]:not(.loaded)');
    bgElements.forEach(el => {
      el.classList.add(this.options.loadingClass);
      this.observer?.observe(el);
    });
  }
  
  onIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Stop observing the element
        this.observer.unobserve(entry.target);
        
        // Load the element
        if (entry.target.tagName.toLowerCase() === 'img') {
          this.loadImage(entry.target);
        } else if (entry.target.hasAttribute('data-background')) {
          this.loadBackgroundImage(entry.target);
        }
      }
    });
  }
  
  loadImage(img) {
    const src = img.getAttribute('data-src');
    const srcset = img.getAttribute('data-srcset');
    const sizes = img.getAttribute('data-sizes');
    
    if (src) {
      img.src = src;
    }
    
    if (srcset) {
      img.srcset = srcset;
    }
    
    if (sizes) {
      img.sizes = sizes;
    }
    
    img.onload = () => {
      img.classList.remove(this.options.loadingClass);
      img.classList.add(this.options.loadedClass);
      
      // If it has blur-up class, handle that too
      if (img.classList.contains('blur-up')) {
        img.classList.add('loaded');
      }
    };
  }
  
  loadBackgroundImage(element) {
    const src = element.getAttribute('data-background');
    if (src) {
      // Create a hidden image to preload
      const img = new Image();
      img.onload = () => {
        element.style.backgroundImage = `url('${src}')`;
        element.classList.remove(this.options.loadingClass);
        element.classList.add(this.options.loadedClass);
      };
      img.src = src;
    }
  }
  
  loadAllElements() {
    // Fallback for when IntersectionObserver is not available
    const images = document.querySelectorAll('img.lazy-image:not(.loaded)');
    images.forEach(img => this.loadImage(img));
    
    const bgElements = document.querySelectorAll('[data-background]:not(.loaded)');
    bgElements.forEach(el => this.loadBackgroundImage(el));
  }
  
  // Call this method to refresh and find new elements
  refresh() {
    this.observeElements();
  }
}

// Initialize and export instance
const lazyLoad = new LazyLoad();

// Create a custom event for when content is dynamically added
window.dispatchEvent(new CustomEvent('mobilize:lazy-load-initialized'));

export default lazyLoad; 