# Mobilize CRM Design System

This document provides an overview of the Mobilize CRM design system, its components, and usage guidelines.

## Introduction

The Mobilize CRM design system is a collection of reusable components, guidelines, and design tokens that ensure consistency and efficiency across the application. It serves as a single source of truth for designers and developers.

## Design Tokens

Design tokens are the visual design atoms of the design system. They define:

- Colors
- Typography
- Spacing
- Border radii
- Shadows
- Transitions

These tokens are implemented as CSS custom properties (variables) in `app/static/css/design-tokens.css`.

## Core Components

The design system includes the following core components:

### Buttons

Buttons allow users to take actions and make choices. Different styles of buttons represent different kinds of actions.

- Primary buttons: Main actions
- Secondary buttons: Alternative actions
- Outline buttons: Less prominent actions
- Button sizes: Small, Medium, Large

See `stories/buttons.stories.js` for examples and usage guidelines.

### Forms

Forms allow users to enter data. The design system includes various form controls:

- Text inputs
- Select dropdowns
- Checkboxes
- Radio buttons
- Textareas
- Input groups
- Form validation states

See `stories/forms.stories.js` for examples and usage guidelines.

### Cards

Cards are containers that group related content and actions. They provide a flexible way to present information.

- Basic cards
- Cards with headers/footers
- Stat cards
- Cards with colored borders
- Dashboard cards

See `stories/cards.stories.js` for examples and usage guidelines.

### Containers

Containers help create consistent layouts across the application:

- Fixed-width containers
- Fluid containers
- Header containers
- Table containers

## Usage Guidelines

### General Principles

1. **Consistency**: Follow established patterns and use existing components whenever possible.
2. **Accessibility**: Ensure all components are accessible to users with disabilities.
3. **Simplicity**: Keep interfaces simple and focused on the task at hand.
4. **Hierarchy**: Use visual hierarchy to guide users through interfaces.

### Using Design Tokens

Always use design tokens instead of hard-coded values:

```css
/* DO */
.element {
  color: var(--color-primary-blue);
  margin-bottom: var(--spacing-md);
}

/* DON'T */
.element {
  color: #183963;
  margin-bottom: 16px;
}
```

## Component Documentation

For detailed documentation about each component, visual examples, and code snippets, run the Storybook documentation:

```
npm run storybook
```

This will launch a local server at http://localhost:6006 with interactive documentation.

## Build a Static Version

To build a static version of the documentation site:

```
npm run storybook:build
```

This will generate static files in the `docs/storybook` directory that can be deployed to any web server.

## Contributing

When adding new components or modifying existing ones:

1. Update the design tokens if needed
2. Create or update the component's story file
3. Include usage guidelines and accessibility considerations
4. Document any variants or props
5. Ensure the component is responsive 