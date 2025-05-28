/**
 * ConfirmMsgBox - A reusable confirmation dialog component for Vue applications
 * 
 * Usage:
 * 1. Import this file in your HTML with: <script src="/confirmmsgbox.js"></script>
 * 2. Use the component in your Vue instance:
 *    this.$confirmDialog({
 *      title: 'Confirmation Required',
 *      message: 'Are you sure you want to proceed?',
 *      confirmText: 'Confirm',
 *      cancelText: 'Cancel',
 *      onConfirm: () => { console.log('User confirmed'); },
 *      onCancel: () => { console.log('User cancelled'); }
 *    });
 */

(function() {
  // Create the component template
  const template = `
    <transition name="confirm-fade">
      <div class="confirm-overlay" v-if="visible">
        <div class="confirm-dialog" @click.stop>
          <div class="confirm-dialog-header">
            <h3>{{ title }}</h3>

          </div>
          <div class="confirm-dialog-body">
            <p style="color: #fff;">{{ message }}</p>
          </div>
          <div class="confirm-dialog-footer">
            <button class="confirm-btn confirm-btn-cancel" @click="cancel">{{ cancelText }}</button>
            <button class="confirm-btn confirm-btn-confirm" @click="confirm">{{ confirmText }}</button>
          </div>
        </div>
      </div>
    </transition>
  `;

  // Add the CSS to the document head
  const style = document.createElement('style');
  style.textContent = `
    .confirm-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 9999;
    }
    
    .confirm-dialog {
      background: #2a2a2a;
      border-radius: 12px;
      width: 90%;
      max-width: 450px;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
      overflow: hidden;
    }
    
    .confirm-dialog-header {
      background: #222;
      padding: 15px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #444;
    }
    
    .confirm-dialog-header h3 {
      color: #2962ff;
      margin: 0;
      font-size: 18px;
    }
    
    .confirm-dialog-body {
      padding: 20px;
      color: #ccc;
      font-size: 16px;
      max-height: 60vh;
      overflow-y: auto;
    }
    
    .confirm-dialog-footer {
      padding: 15px 20px;
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      border-top: 1px solid #444;
    }
    
    .confirm-btn {
      padding: 8px 16px;
      border-radius: 8px;
      border: none;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.2s;
      height: 40px;
    }
    
    .confirm-btn-cancel {
      background: #363636;
      color: #ccc;
    }
    
    .confirm-btn-cancel:hover {
      background: #444;
    }
    
    .confirm-btn-confirm {
      background: #2962ff;
      color: white;
    }
    
    .confirm-btn-confirm:hover {
      background: #1e4bd8;
    }
    
    /* Transitions */
    .confirm-fade-enter-active, .confirm-fade-leave-active {
      transition: opacity 0.3s;
    }
    
    .confirm-fade-enter, .confirm-fade-leave-to {
      opacity: 0;
    }
    
    .confirm-dialog {
      transition: transform 0.3s, opacity 0.3s;
    }
    
    .confirm-fade-enter .confirm-dialog {
      transform: scale(0.9);
      opacity: 0;
    }
    
    .confirm-fade-enter-to .confirm-dialog {
      transform: scale(1);
      opacity: 1;
    }
  `;
  document.head.appendChild(style);

  // Create Vue component
  const ConfirmDialogComponent = {
    template: template,
    data() {
      return {
        visible: false,
        title: 'Confirm',
        message: 'Are you sure?',
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        resolvePromise: null,
        rejectPromise: null
      };
    },
    methods: {
      confirm() {
        this.visible = false;
        if (this.resolvePromise) {
          this.resolvePromise(true);
        }
        if (this.onConfirmCallback) {
          this.onConfirmCallback();
        }
      },
      cancel() {
        this.visible = false;
        if (this.resolvePromise) {
          this.resolvePromise(false);
        }
        if (this.onCancelCallback) {
          this.onCancelCallback();
        }
      },
      open(options) {
        this.title = options.title || 'Confirm';
        this.message = options.message || 'Are you sure?';
        this.confirmText = options.confirmText || 'Confirm';
        this.cancelText = options.cancelText || 'Cancel';
        this.onConfirmCallback = options.onConfirm;
        this.onCancelCallback = options.onCancel;
        this.visible = true;
        
        return new Promise(resolve => {
          this.resolvePromise = resolve;
        });
      }
    }
  };

  // Create and mount the component instance when needed
  let confirmDialogInstance = null;

  // Install as a Vue plugin
  const ConfirmDialogPlugin = {
    install(Vue) {
      // Add prototype method to show dialog
      Vue.prototype.$confirmDialog = function(options) {
        if (!confirmDialogInstance) {
          // Create a div for mounting
          const container = document.createElement('div');
          document.body.appendChild(container);
          
          // Create and mount component
          const ConfirmDialogConstructor = Vue.extend(ConfirmDialogComponent);
          confirmDialogInstance = new ConfirmDialogConstructor();
          confirmDialogInstance.$mount(container);
        }
        
        return confirmDialogInstance.open(options);
      };
    }
  };
  
  // Auto-install if Vue is detected
  if (typeof Vue !== 'undefined') {
    Vue.use(ConfirmDialogPlugin);
  } else {
    console.warn('Vue not detected! Please install ConfirmDialogPlugin manually.');
    window.ConfirmDialogPlugin = ConfirmDialogPlugin;
  }
})(); 