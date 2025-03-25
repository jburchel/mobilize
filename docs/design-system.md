# Mobilize CRM Design System

This document provides an overview of the Mobilize CRM design system, its components, and how to use them in development.

## Overview

The Mobilize CRM design system consists of:

1. **Design Tokens**: Foundational variables for colors, typography, spacing, etc.
2. **Component Library**: Reusable UI components with consistent styling
3. **Pattern Guidelines**: Common UI patterns and their implementation
4. **Documentation**: Guidelines for usage and implementation

## Design Tokens

All design tokens are defined in `app/static/css/design-tokens.css`. These CSS variables should be used throughout the application for consistent styling.

### How to Use Design Tokens

```css
/* Example of using design tokens */
.my-component {
  color: var(--color-primary-blue);
  font-size: var(--font-size-md);
  padding: var(--spacing-md);
  border-radius: var(--border-radius-sm);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base) var(--transition-timing-ease);
}
```

## Component Documentation

### Component Structure

Each component should:

1. Use design tokens for all styling values
2. Be responsive by default
3. Include necessary ARIA attributes for accessibility
4. Support keyboard navigation where applicable
5. Have clear documentation on usage

### Component Template

```html
<!-- Example component template -->
<div class="card-component" aria-labelledby="card-title">
  <div class="card-header">
    <h3 id="card-title" class="card-title">Card Title</h3>
  </div>
  <div class="card-body">
    <p class="card-text">Card content goes here</p>
  </div>
  <div class="card-footer">
    <button class="btn btn-primary">Action</button>
  </div>
</div>
```

## Setting Up Storybook (Development Guide)

We use Storybook for component documentation and development. To set up Storybook:

1. Install dependencies:
   ```bash
   npm install -g @storybook/cli
   npx sb init
   ```

2. Start Storybook:
   ```bash
   npm run storybook
   ```

3. Creating a component story:
   ```js
   // Example: Button.stories.js
   export default {
     title: 'Components/Button',
     component: Button,
   };
   
   export const Primary = () => '<button class="btn btn-primary">Primary Button</button>';
   export const Secondary = () => '<button class="btn btn-secondary">Secondary Button</button>';
   ```

## Accessibility Guidelines

All components must:

1. Have appropriate color contrast (minimum 4.5:1 for text)
2. Be navigable via keyboard
3. Include appropriate ARIA roles and attributes
4. Support screen readers
5. Provide text alternatives for non-text content

## Performance Considerations

1. Use CSS variables for runtime theme changes
2. Minimize DOM nesting
3. Use CSS transitions instead of JavaScript animations where possible
4. Lazy load components not visible in the initial viewport
5. Optimize images using the provided script

## Build Process

Our build process includes:

1. CSS optimization with PostCSS
2. Image optimization with Sharp
3. Component documentation with Storybook

To build optimized assets:

```bash
npm run build
```

## Contributing to the Design System

1. All new components should be built using design tokens
2. Document components in Storybook
3. Test components for accessibility
4. Ensure responsive behavior on all devices
5. Get design review before implementation 