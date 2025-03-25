import { html } from 'lit-html';

export default {
  title: 'Components/Buttons',
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'success', 'danger', 'warning', 'info', 'light', 'dark', 'link'],
      defaultValue: 'primary'
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
      defaultValue: 'md'
    },
    disabled: {
      control: { type: 'boolean' },
      defaultValue: false
    },
    text: {
      control: { type: 'text' },
      defaultValue: 'Button'
    }
  }
};

const ButtonTemplate = ({ variant, size, disabled, text }) => {
  const sizeClass = size === 'md' ? '' : `btn-${size}`;
  const buttonClass = `btn btn-${variant} ${sizeClass}`;
  
  return html`
    <button class="${buttonClass}" ?disabled=${disabled}>${text}</button>
  `;
};

export const Button = ButtonTemplate.bind({});

export const ButtonVariants = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Button Variants</h1>
      
      <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem;">
        <button class="btn btn-primary">Primary</button>
        <button class="btn btn-secondary">Secondary</button>
        <button class="btn btn-success">Success</button>
        <button class="btn btn-danger">Danger</button>
        <button class="btn btn-warning">Warning</button>
        <button class="btn btn-info">Info</button>
        <button class="btn btn-light">Light</button>
        <button class="btn btn-dark">Dark</button>
        <button class="btn btn-link">Link</button>
      </div>
      
      <h2 style="margin-top: 2rem;">Outline Buttons</h2>
      <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem;">
        <button class="btn btn-outline-primary">Primary</button>
        <button class="btn btn-outline-secondary">Secondary</button>
        <button class="btn btn-outline-success">Success</button>
        <button class="btn btn-outline-danger">Danger</button>
        <button class="btn btn-outline-warning">Warning</button>
        <button class="btn btn-outline-info">Info</button>
        <button class="btn btn-outline-light">Light</button>
        <button class="btn btn-outline-dark">Dark</button>
      </div>
      
      <h2 style="margin-top: 2rem;">Button Sizes</h2>
      <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <button class="btn btn-primary btn-lg">Large button</button>
        <button class="btn btn-primary">Default button</button>
        <button class="btn btn-primary btn-sm">Small button</button>
      </div>
      
      <h2 style="margin-top: 2rem;">Button States</h2>
      <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem;">
        <button class="btn btn-primary">Normal</button>
        <button class="btn btn-primary active">Active</button>
        <button class="btn btn-primary" disabled>Disabled</button>
      </div>
      
      <h2 style="margin-top: 2rem;">Button with Icons</h2>
      <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem;">
        <button class="btn btn-primary">
          <i class="fas fa-save"></i> Save
        </button>
        <button class="btn btn-success">
          <i class="fas fa-check"></i> Confirm
        </button>
        <button class="btn btn-danger">
          <i class="fas fa-trash"></i> Delete
        </button>
      </div>
    </div>
  `;
};

export const ButtonUsage = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Button Usage Guidelines</h1>
      
      <div style="max-width: 800px;">
        <h2 style="margin-top: 2rem;">Primary vs Secondary Buttons</h2>
        <p>Use primary buttons for the main action in a section or form. Use secondary buttons for alternative actions.</p>
        
        <div style="display: flex; gap: 1rem; margin: 1rem 0;">
          <button class="btn btn-primary">Save changes</button>
          <button class="btn btn-secondary">Cancel</button>
        </div>
        
        <h2 style="margin-top: 2rem;">Color Meaning</h2>
        <ul>
          <li><strong>Primary (Blue):</strong> Main actions, navigation, general purpose</li>
          <li><strong>Success (Green):</strong> Positive actions, confirmation, completion</li>
          <li><strong>Danger (Red):</strong> Destructive actions, errors, warnings</li>
          <li><strong>Warning (Yellow):</strong> Cautionary actions, alerts</li>
          <li><strong>Info (Cyan):</strong> Informational actions, help</li>
        </ul>
        
        <h2 style="margin-top: 2rem;">Button Positioning</h2>
        <p>When using multiple buttons:</p>
        <ul>
          <li>Position primary action on the right (for Western reading direction)</li>
          <li>Group related buttons together</li>
          <li>Use consistent ordering across the application</li>
        </ul>
        
        <h2 style="margin-top: 2rem;">Accessibility Considerations</h2>
        <ul>
          <li>Ensure sufficient color contrast (WCAG AA minimum)</li>
          <li>Include text labels, not just icons</li>
          <li>Use appropriate aria attributes when needed</li>
          <li>Ensure keyboard navigation works properly</li>
        </ul>
      </div>
    </div>
  `;
}; 