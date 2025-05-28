/**
 * Loading Component - A reusable loading overlay for Vue applications
 * 
 * Usage:
 * 1. Import this file in your HTML with: <script src="/loading.js"></script>
 * 2. Use the component in your Vue template:
 *    <loading-overlay v-if="isLoading" text="Saving..."></loading-overlay>
 * 
 * Props:
 * - text: The text to display (default: "Loading...")
 * - showDots: Whether to show the animated dots (default: true)
 * - showWaitText: Whether to show "Please wait a moment" (default: true)
 */

(function() {
  // Create the component template
  const template = `
    <div class="loading-overlay">
      <div class="loading-text">
        <div class="analyzing-text">{{ text }}</div>
        <div v-if="showDots" class="loader-dots">
          <div class="loader-dot"></div>
          <div class="loader-dot"></div>
          <div class="loader-dot"></div>
        </div>
        <div v-if="showWaitText" class="wait-text">Please wait</div>
      </div>
    </div>
  `;

  // Add the CSS to the document head
  const style = document.createElement('style');
  style.textContent = `
    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
    }

    .loading-text {
      font-size: 20px;
      font-weight: 500;
      color: white;
      background: rgba(41, 98, 255, 0.9);
      padding: 20px 40px;
      border-radius: 16px;
      text-align: center;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    .loader-dots {
      display: flex;
      justify-content: center;
      gap: 8px;
      margin-top: 10px;
    }

    .loader-dot {
      width: 8px;
      height: 8px;
      background: white;
      border-radius: 50%;
      animation: bounce 0.5s ease-in-out infinite;
    }

    .loader-dot:nth-child(2) {
      animation-delay: 0.1s;
    }

    .loader-dot:nth-child(3) {
      animation-delay: 0.2s;
    }

    @keyframes bounce {
      0%, 100% {
        transform: translateY(0);
      }
      50% {
        transform: translateY(-10px);
      }
    }

    .analyzing-text {
      display: inline-block;
      margin-bottom: 10px;
      background: linear-gradient(90deg, #2962ff, #3d7dff, #2962ff);
      background-size: 200% auto;
      animation: shine 2s linear infinite;
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    @keyframes shine {
      to {
        background-position: 200% center;
      }
    }

    .wait-text {
      opacity: 0.8;
      font-size: 0.9em;
      animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% {
        opacity: 0.6;
      }
      50% {
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(style);

  // Create Vue component
  Vue.component('loading-overlay', {
    template: template,
    props: {
      text: {
        type: String,
        default: 'Loading...'
      },
      showDots: {
        type: Boolean,
        default: true
      },
      showWaitText: {
        type: Boolean,
        default: true
      }
    }
  });
})(); 