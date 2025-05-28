const timelineStyles = `
.header-timeline {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 40px;
  height: 50px;
}

.timeline-step {
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 1;
  transition: all 0.3s;
}

.timeline-step.future {
  opacity: 0.5;
}

.step-number {
  width: 24px;
  height: 24px;
  background: #797979;  /* grey for future steps */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  color: #fff;
}

.step-label {
  font-size: 14px;
  font-weight: 500;
  color: #797979;  /* grey for future steps */
}

/* Past steps */
.timeline-step.past .step-number {
  background: #7c9efd;  /* darker blue */
}

.timeline-step.past .step-label {
  color: #7c9efd;  /* darker blue */
}

/* Current step */
.timeline-step.current .step-number {
  background: #2962ff;  /* current blue */
}

.timeline-step.current .step-label {
  color: #2962ff;  /* current blue */
}
`;

// Create and append style element
const styleElement = document.createElement('style');
styleElement.textContent = timelineStyles;
document.head.appendChild(styleElement);

// Then define the Vue component
Vue.component('timeline', {
  props: {
    currentStep: {
      type: Number,
      required: true
    }
  },
  template: `
    <div class="header-timeline">
      <div v-for="step in 8" :key="step" 
           :class="['timeline-step', {
             'past': step < currentStep,
             'current': step === currentStep,
             'future': step > currentStep
           }]">
        <div class="step-number">{{ step }}</div>
        <div class="step-label">{{ getStepLabel(step) }}</div>
      </div>
    </div>
  `,
  methods: {
    getStepLabel(step) {
      const labels = {
        1: 'Information Collection',
        2: 'Constants & Variables',
        3: 'Actions',
        4: 'Assertions',
        5: 'NL Annotation',
        6: 'Code Generation',
        7: 'Verification',
        8: 'Refinement'
      };
      return labels[step];
    }
  }
});